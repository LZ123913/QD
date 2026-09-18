"""
Lightweight HTTP server for the prediction API.
Uses Python's built-in http.server (no Flask dependency).
ThreadingHTTPServer ensures one failed connection won't crash the server.

Endpoints:
  GET  /api/models         -> list of models with metrics
  POST /api/predict        -> { date, model, days? } -> prediction result
  GET  /api/health         -> health check
"""
import json
import sys
import os
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predict_engine import get_engine, MODEL_LABELS

PORT = 5000


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json(self, code, obj):
        try:
            body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._cors()
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def do_OPTIONS(self):
        self._json(204, {})

    def do_GET(self):
        try:
            if self.path == '/api/health':
                self._json(200, {'status': 'ok'})
            elif self.path == '/api/models':
                eng = get_engine()
                metrics = eng.get_model_metrics()
                models = []
                for key, label in MODEL_LABELS.items():
                    m = metrics.get(key, {})
                    models.append({
                        'key': key,
                        'label': label,
                        'metrics': m,
                    })
                self._json(200, {'models': models})
            else:
                self._json(404, {'error': 'not found'})
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            traceback.print_exc()
            self._json(500, {'error': str(e)})

    def do_POST(self):
        if self.path != '/api/predict':
            self._json(404, {'error': 'not found'})
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length) if length > 0 else b''
            data = json.loads(raw) if raw else {}
            date = data.get('date', '')
            model = data.get('model', 'att_lstm')
            days = int(data.get('days', 1))
            if not date:
                self._json(400, {'error': 'date is required'})
                return
            if days < 1 or days > 7:
                days = 1
            eng = get_engine()
            result = eng.predict_range(date, model, days=days)
            self._json(200, result)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            traceback.print_exc()
            self._json(500, {'error': str(e)})

    def log_message(self, fmt, *args):
        sys.stderr.write(f'[server] {args[0]}\n')


def main():
    print('Loading models and data...', flush=True)
    eng = get_engine()
    print(f'  Models: {list(eng.models.keys())}', flush=True)
    print(f'  Data range: {eng.df["datetime"].iloc[0]} -> {eng.df["datetime"].iloc[-1]}', flush=True)
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'Prediction server running at http://127.0.0.1:{PORT}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...', flush=True)
        server.shutdown()


if __name__ == '__main__':
    main()
