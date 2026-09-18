"""
Prediction engine: loads models, scalers, feature data; builds input sequences;
runs forward pass; supports in-range lookup and autoregressive multi-step forecast.
"""
import os
import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from nn_numpy import MODEL_FORWARD, att_lstm_forward
from pt_loader import load_state_dict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 46 feature columns in scaler/test_x order
FEATURE_COLS = [
    'AQI', 'CO', 'NO2', 'O3', 'O3_8h', 'SO2',
    'hour', 'hour_sin', 'hour_cos', 'is_workday',
    'PM2.5_lag_1h', 'PM10_lag_1h',
    'PM2.5_lag_3h', 'PM10_lag_3h',
    'PM2.5_lag_6h', 'PM10_lag_6h',
    'PM2.5_lag_12h', 'PM10_lag_12h',
    'PM2.5_lag_24h', 'PM10_lag_24h',
    'PM2.5_roll_mean_3h', 'PM2.5_roll_std_3h', 'PM2.5_delta_3h',
    'PM10_roll_mean_3h', 'PM10_roll_std_3h', 'PM10_delta_3h',
    'PM2.5_roll_mean_6h', 'PM2.5_roll_std_6h', 'PM2.5_delta_6h',
    'PM10_roll_mean_6h', 'PM10_roll_std_6h', 'PM10_delta_6h',
    'PM2.5_roll_mean_12h', 'PM2.5_roll_std_12h', 'PM2.5_delta_12h',
    'PM10_roll_mean_12h', 'PM10_roll_std_12h', 'PM10_delta_12h',
    'PM2.5_roll_mean_24h', 'PM2.5_roll_std_24h', 'PM2.5_delta_24h',
    'PM10_roll_mean_24h', 'PM10_roll_std_24h', 'PM10_delta_24h',
    'pm25_pm10_ratio', 'coarse_particle',
]

SEQ_LEN = 24

MODEL_FILES = {
    'baseline_lstm': 'baseline_lstm.pt',
    'baseline_gru': 'baseline_gru.pt',
    'cnn_lstm': 'cnn_lstm.pt',
    'att_lstm': 'att_lstm.pt',
    'ablation_noatt_lstm': 'ablation_noatt_lstm.pt',
}

MODEL_LABELS = {
    'baseline_lstm': 'LSTM 基线模型',
    'baseline_gru': 'GRU 基线模型',
    'cnn_lstm': 'CNN-LSTM 混合模型',
    'att_lstm': 'Attention-LSTM 注意力模型',
    'ablation_noatt_lstm': '消融实验(无注意力)',
}


class CompatUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        remap = {
            'numpy._core': 'numpy.core',
            'numpy._core.multiarray': 'numpy.core.multiarray',
            'numpy._core.numeric': 'numpy.core.numeric',
        }
        for old, new in remap.items():
            if module.startswith(old):
                module = new + module[len(old):]
        __import__(module, level=0)
        return getattr(sys.modules[module], name)


def _load_pkl(path):
    with open(path, 'rb') as f:
        return CompatUnpickler(f).load()


class PredictEngine:
    def __init__(self):
        self.models = {}
        self.scaler_x = None
        self.scaler_y = None
        self.df = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        # scalers
        self.scaler_x = _load_pkl(os.path.join(BASE, 'scaler_x.pkl'))
        self.scaler_y = _load_pkl(os.path.join(BASE, 'scaler_y.pkl'))
        # feature data - reindex to complete hourly range to fill small gaps
        df_raw = pd.read_csv(os.path.join(BASE, 'all_feature_data.csv'))
        df_raw['datetime'] = pd.to_datetime(df_raw['datetime'])
        df_raw = df_raw.sort_values('datetime').reset_index(drop=True)
        full_range = pd.date_range(start=df_raw['datetime'].iloc[0],
                                   end=df_raw['datetime'].iloc[-1], freq='h')
        df_raw = df_raw.set_index('datetime').reindex(full_range)
        # Forward-fill numeric columns, then backward-fill any leading NaNs
        df_raw = df_raw.ffill().bfill()
        df_raw.index.name = 'datetime'
        self.df = df_raw.reset_index()
        self.df_index = df_raw
        # models
        for key, fn in MODEL_FILES.items():
            p = os.path.join(BASE, fn)
            if os.path.exists(p):
                self.models[key] = load_state_dict(p)
        self._loaded = True

    def _scale_x(self, arr):
        """arr: (N, 46) -> scaled (N, 46)"""
        return (arr - self.scaler_x.data_min_) / (self.scaler_x.data_max_ - self.scaler_x.data_min_)

    def _inverse_y(self, arr):
        """arr: (..., 2) scaled -> original PM2.5, PM10"""
        return arr * (self.scaler_y.data_max_ - self.scaler_y.data_min_) + self.scaler_y.data_min_

    def _get_features_at(self, dt):
        """Get the 46-feature row for a datetime that exists in df."""
        row = self.df_index.loc[pd.Timestamp(dt)]
        return row[FEATURE_COLS].values.astype(np.float64)

    def _run_model(self, model_key, x_scaled):
        """x_scaled: (24, 46). Returns (2,) raw-scaled output."""
        sd = self.models[model_key]
        fn = MODEL_FORWARD[model_key]
        if model_key == 'att_lstm':
            out, _ = fn(x_scaled, sd)
        else:
            out = fn(x_scaled, sd)
        return out

    def predict_hour_inrange(self, target_dt, model_key):
        """
        Predict a single hour that is within the dataset range.
        target_dt: datetime of the hour to predict.
        Uses the 24 hours BEFORE target_dt as input (actual features).
        """
        # Input window: [target-24h, target-1h] (24 rows)
        start = target_dt - timedelta(hours=SEQ_LEN)
        times = [start + timedelta(hours=i) for i in range(SEQ_LEN)]
        feats = np.array([self._get_features_at(t) for t in times])
        feats_scaled = self._scale_x(feats)
        out_scaled = self._run_model(model_key, feats_scaled)
        out = self._inverse_y(out_scaled)
        return float(out[0]), float(out[1])

    def _build_next_features(self, history_pm25, history_pm10, history_dt, next_dt, last_exog):
        """
        Build the 46-feature vector for next_dt given history of PM values.
        history_pm25/pm10: lists ending at the most recent known/predicted hour (before next_dt).
        history_dt: list of datetimes corresponding to history.
        last_exog: dict with last known AQI, CO, NO2, O3, O3_8h, SO2.
        """
        h = next_dt.hour
        hour_sin = np.sin(2 * np.pi * h / 24)
        hour_cos = np.cos(2 * np.pi * h / 24)
        is_workday = 1 if next_dt.weekday() < 5 else 0

        # Helper to get PM value at lag hours ago
        def get_lag(vals, lag):
            if len(vals) >= lag:
                return vals[-lag]
            return vals[0]

        def roll_stats(vals, window):
            if len(vals) >= window:
                chunk = vals[-window:]
            else:
                chunk = vals[:]
            return np.mean(chunk), np.std(chunk)

        pm25_now = history_pm25[-1]
        pm10_now = history_pm10[-1]
        pm25_lag1 = get_lag(history_pm25, 1)
        pm10_lag1 = get_lag(history_pm10, 1)
        pm25_lag3 = get_lag(history_pm25, 3)
        pm10_lag3 = get_lag(history_pm10, 3)
        pm25_lag6 = get_lag(history_pm25, 6)
        pm10_lag6 = get_lag(history_pm10, 6)
        pm25_lag12 = get_lag(history_pm25, 12)
        pm10_lag12 = get_lag(history_pm10, 12)
        pm25_lag24 = get_lag(history_pm25, 24)
        pm10_lag24 = get_lag(history_pm10, 24)

        pm25_m3, pm25_s3 = roll_stats(history_pm25, 3)
        pm10_m3, pm10_s3 = roll_stats(history_pm10, 3)
        pm25_m6, pm25_s6 = roll_stats(history_pm25, 6)
        pm10_m6, pm10_s6 = roll_stats(history_pm10, 6)
        pm25_m12, pm25_s12 = roll_stats(history_pm25, 12)
        pm10_m12, pm10_s12 = roll_stats(history_pm10, 12)
        pm25_m24, pm25_s24 = roll_stats(history_pm25, 24)
        pm10_m24, pm10_s24 = roll_stats(history_pm10, 24)

        ratio = pm25_now / max(pm10_now, 1.0)
        coarse = pm10_now - pm25_now

        row = [
            last_exog['AQI'], last_exog['CO'], last_exog['NO2'],
            last_exog['O3'], last_exog['O3_8h'], last_exog['SO2'],
            h, hour_sin, hour_cos, is_workday,
            pm25_lag1, pm10_lag1,
            pm25_lag3, pm10_lag3,
            pm25_lag6, pm10_lag6,
            pm25_lag12, pm10_lag12,
            pm25_lag24, pm10_lag24,
            pm25_m3, pm25_s3, pm25_now - pm25_lag3,
            pm10_m3, pm10_s3, pm10_now - pm10_lag3,
            pm25_m6, pm25_s6, pm25_now - pm25_lag6,
            pm10_m6, pm10_s6, pm10_now - pm10_lag6,
            pm25_m12, pm25_s12, pm25_now - pm25_lag12,
            pm10_m12, pm10_s12, pm10_now - pm10_lag12,
            pm25_m24, pm25_s24, pm25_now - pm25_lag24,
            pm10_m24, pm10_s24, pm10_now - pm10_lag24,
            ratio, coarse,
        ]
        return np.array(row, dtype=np.float64)

    def predict_range(self, target_date_str, model_key, days=1):
        """
        Predict hourly PM2.5/PM10 for the given date (and optionally multiple days).
        target_date_str: 'YYYY-MM-DD'
        model_key: model identifier
        days: number of consecutive days to predict
        Returns dict with hourly results and daily averages.
        """
        self.load()
        if model_key not in self.models:
            raise ValueError(f'Unknown model: {model_key}')

        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        last_data_dt = self.df['datetime'].iloc[-1]
        first_data_dt = self.df['datetime'].iloc[0]

        # Determine if target is within dataset range
        target_end = target_date + timedelta(days=days) - timedelta(hours=1)

        if target_end <= last_data_dt and target_date >= first_data_dt + timedelta(hours=SEQ_LEN):
            # In-range: use actual features directly
            hourly = []
            for d in range(days):
                for h in range(24):
                    dt = target_date + timedelta(days=d, hours=h)
                    p25, p10 = self.predict_hour_inrange(dt, model_key)
                    p25 = max(0, p25)
                    p10 = max(0, p10)
                    hourly.append({
                        'datetime': dt.strftime('%Y-%m-%d %H:%M'),
                        'pm25': round(p25, 1),
                        'pm10': round(p10, 1),
                    })
        else:
            # Out-of-range: autoregressive forecast from last known data
            # Start with last SEQ_LEN known rows
            start_known = last_data_dt - timedelta(hours=SEQ_LEN - 1)
            known_times = [start_known + timedelta(hours=i) for i in range(SEQ_LEN)]
            known_feats = np.array([self._get_features_at(t) for t in known_times])

            # Build PM history from the last part of the dataset (need at least 24h for lag features)
            hist_start = last_data_dt - timedelta(hours=SEQ_LEN * 2)
            hist_df = self.df_index.loc[hist_start:last_data_dt]
            pm25_hist = hist_df['PM2.5'].tolist()
            pm10_hist = hist_df['PM10'].tolist()

            # Last known exogenous values
            last_row = self.df_index.loc[last_data_dt]
            last_exog = {
                'AQI': float(last_row['AQI']),
                'CO': float(last_row['CO']),
                'NO2': float(last_row['NO2']),
                'O3': float(last_row['O3']),
                'O3_8h': float(last_row['O3_8h']),
                'SO2': float(last_row['SO2']),
            }

            # Current feature window (24 x 46), scaled
            window_feats = known_feats.copy()

            # Determine how many hours to predict from last_data_dt+1 to target_end
            first_pred_dt = last_data_dt + timedelta(hours=1)
            hours_to_predict = int((target_end - first_pred_dt).total_seconds() / 3600) + 1

            if hours_to_predict <= 0:
                # Target is before or at last data point but window issue - use in-range fallback
                return self.predict_range_inrange_simple(target_date, model_key, days)

            all_preds = {}  # dt -> (pm25, pm10)
            current_dt = first_pred_dt
            for step in range(hours_to_predict):
                # Scale window and predict
                scaled = self._scale_x(window_feats)
                out_scaled = self._run_model(model_key, scaled)
                out = self._inverse_y(out_scaled)
                pm25 = max(0, float(out[0]))
                pm10 = max(0, float(out[1]))
                all_preds[current_dt] = (pm25, pm10)

                # Update PM history
                pm25_hist.append(pm25)
                pm10_hist.append(pm10)

                # Build next feature row
                next_dt = current_dt + timedelta(hours=1)
                next_feats = self._build_next_features(
                    pm25_hist, pm10_hist, None, next_dt, last_exog)

                # Slide window
                window_feats = np.vstack([window_feats[1:], next_feats])
                current_dt = next_dt

            # Extract requested range
            hourly = []
            for d in range(days):
                for h in range(24):
                    dt = target_date + timedelta(days=d, hours=h)
                    if dt in all_preds:
                        p25, p10 = all_preds[dt]
                    elif dt <= last_data_dt:
                        # Within known range but not predicted (shouldn't happen in out-of-range branch)
                        p25 = float(self.df_index.loc[dt, 'PM2.5'])
                        p10 = float(self.df_index.loc[dt, 'PM10'])
                    else:
                        p25, p10 = 0, 0
                    hourly.append({
                        'datetime': dt.strftime('%Y-%m-%d %H:%M'),
                        'pm25': round(p25, 1),
                        'pm10': round(p10, 1),
                    })

        # Daily averages
        daily = []
        for d in range(days):
            day_hours = hourly[d * 24:(d + 1) * 24]
            avg25 = np.mean([h['pm25'] for h in day_hours])
            avg10 = np.mean([h['pm10'] for h in day_hours])
            daily.append({
                'date': (target_date + timedelta(days=d)).strftime('%Y-%m-%d'),
                'pm25': round(float(avg25), 1),
                'pm10': round(float(avg10), 1),
            })

        return {
            'model': model_key,
            'model_label': MODEL_LABELS.get(model_key, model_key),
            'target_date': target_date_str,
            'days': days,
            'hourly': hourly,
            'daily': daily,
            'data_range': {
                'start': first_data_dt.strftime('%Y-%m-%d'),
                'end': last_data_dt.strftime('%Y-%m-%d'),
            },
        }

    def predict_range_inrange_simple(self, target_date, model_key, days):
        """Fallback in-range prediction."""
        hourly = []
        for d in range(days):
            for h in range(24):
                dt = target_date + timedelta(days=d, hours=h)
                try:
                    p25, p10 = self.predict_hour_inrange(dt, model_key)
                except Exception:
                    p25, p10 = 0, 0
                hourly.append({
                    'datetime': dt.strftime('%Y-%m-%d %H:%M'),
                    'pm25': round(max(0, p25), 1),
                    'pm10': round(max(0, p10), 1),
                })
        daily = []
        for d in range(days):
            day_hours = hourly[d * 24:(d + 1) * 24]
            daily.append({
                'date': (target_date + timedelta(days=d)).strftime('%Y-%m-%d'),
                'pm25': round(float(np.mean([h['pm25'] for h in day_hours])), 1),
                'pm10': round(float(np.mean([h['pm10'] for h in day_hours])), 1),
            })
        last_data_dt = self.df['datetime'].iloc[-1]
        first_data_dt = self.df['datetime'].iloc[0]
        return {
            'model': model_key,
            'model_label': MODEL_LABELS.get(model_key, model_key),
            'target_date': target_date.strftime('%Y-%m-%d'),
            'days': days,
            'hourly': hourly,
            'daily': daily,
            'data_range': {
                'start': first_data_dt.strftime('%Y-%m-%d'),
                'end': last_data_dt.strftime('%Y-%m-%d'),
            },
        }

    def get_model_metrics(self):
        """Load evaluation metrics from all_model_result.csv."""
        p = os.path.join(BASE, 'all_model_result.csv')
        if not os.path.exists(p):
            return {}
        df = pd.read_csv(p)
        # Map CSV display names (may contain special Unicode hyphens) to internal keys
        name_map = {
            'baseline-lstm': 'baseline_lstm',
            'baseline-gru': 'baseline_gru',
            'cnn-lstm': 'cnn_lstm',
            'attention-lstm': 'att_lstm',
        }
        metrics = {}
        for _, row in df.iterrows():
            raw_name = str(row.iloc[0]).replace('\u2011', '-').replace('\u2010', '-').lower()
            key = name_map.get(raw_name, raw_name)
            metrics[key] = {
                'label': MODEL_LABELS.get(key, str(row.iloc[0])),
                'pm25_mae': round(float(row.get('PM2.5_MAE', 0)), 2),
                'pm25_rmse': round(float(row.get('PM2.5_RMSE', 0)), 2),
                'pm25_r2': round(float(row.get('PM2.5_R2', 0)), 4),
                'pm10_mae': round(float(row.get('PM10_MAE', 0)), 2),
                'pm10_rmse': round(float(row.get('PM10_RMSE', 0)), 2),
                'pm10_r2': round(float(row.get('PM10_R2', 0)), 4),
            }
        return metrics


# Singleton
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = PredictEngine()
        _engine.load()
    return _engine
