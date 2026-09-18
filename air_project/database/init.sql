-- ============================================================
-- 青岛大气PM2.5/PM10分析系统 - 数据库初始化脚本
-- 适用: MySQL 5.7+ / MariaDB 10.3+
-- 工具: HeidiSQL
-- ============================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS qingdao_air
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE qingdao_air;

-- ============================================================
-- 1. 原始污染物数据表 (来源: data_all_poll.csv)
-- ============================================================
DROP TABLE IF EXISTS `air_quality_raw`;
CREATE TABLE `air_quality_raw` (
  `id`        INT AUTO_INCREMENT PRIMARY KEY,
  `datetime`  DATETIME NOT NULL,
  `AQI`       DECIMAL(6,1),
  `CO`        DECIMAL(5,2),
  `NO2`       DECIMAL(6,1),
  `O3`        DECIMAL(6,1),
  `O3_8h`     DECIMAL(6,1),
  `PM10`      DECIMAL(6,1),
  `PM2_5`     DECIMAL(6,1),
  `SO2`       DECIMAL(6,1),
  UNIQUE KEY `uk_datetime` (`datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原始污染物小时数据';

-- ============================================================
-- 2. PM数据表 (来源: data_pm.csv)
-- ============================================================
DROP TABLE IF EXISTS `air_quality_pm`;
CREATE TABLE `air_quality_pm` (
  `id`        INT AUTO_INCREMENT PRIMARY KEY,
  `datetime`  DATETIME NOT NULL,
  `PM2_5`     DECIMAL(6,1),
  `PM10`      DECIMAL(6,1),
  UNIQUE KEY `uk_datetime` (`datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PM2.5/PM10小时数据';

-- ============================================================
-- 3. 完整特征数据表 (来源: all_feature_data.csv, 46列特征)
-- ============================================================
DROP TABLE IF EXISTS `air_quality_features`;
CREATE TABLE `air_quality_features` (
  `id`          INT AUTO_INCREMENT PRIMARY KEY,
  `datetime`    DATETIME NOT NULL,
  `AQI`         DECIMAL(6,1),
  `CO`          DECIMAL(5,2),
  `NO2`         DECIMAL(6,1),
  `O3`          DECIMAL(6,1),
  `O3_8h`       DECIMAL(6,1),
  `PM10`        DECIMAL(6,1),
  `PM2_5`       DECIMAL(6,1),
  `SO2`         DECIMAL(6,1),
  `hour`        INT,
  `hour_sin`    DOUBLE,
  `hour_cos`    DOUBLE,
  `is_workday`  INT,
  `PM2_5_lag_1h`   DECIMAL(6,1),
  `PM10_lag_1h`    DECIMAL(6,1),
  `PM2_5_lag_3h`   DECIMAL(6,1),
  `PM10_lag_3h`    DECIMAL(6,1),
  `PM2_5_lag_6h`   DECIMAL(6,1),
  `PM10_lag_6h`    DECIMAL(6,1),
  `PM2_5_lag_12h`  DECIMAL(6,1),
  `PM10_lag_12h`   DECIMAL(6,1),
  `PM2_5_lag_24h`  DECIMAL(6,1),
  `PM10_lag_24h`   DECIMAL(6,1),
  `PM2_5_roll_mean_3h`  DECIMAL(10,4),
  `PM2_5_roll_std_3h`   DECIMAL(10,4),
  `PM2_5_delta_3h`      DECIMAL(6,1),
  `PM10_roll_mean_3h`   DECIMAL(10,4),
  `PM10_roll_std_3h`    DECIMAL(10,4),
  `PM10_delta_3h`       DECIMAL(6,1),
  `PM2_5_roll_mean_6h`  DECIMAL(10,4),
  `PM2_5_roll_std_6h`   DECIMAL(10,4),
  `PM2_5_delta_6h`      DECIMAL(6,1),
  `PM10_roll_mean_6h`   DECIMAL(10,4),
  `PM10_roll_std_6h`    DECIMAL(10,4),
  `PM10_delta_6h`       DECIMAL(6,1),
  `PM2_5_roll_mean_12h` DECIMAL(10,4),
  `PM2_5_roll_std_12h`  DECIMAL(10,4),
  `PM2_5_delta_12h`     DECIMAL(6,1),
  `PM10_roll_mean_12h`  DECIMAL(10,4),
  `PM10_roll_std_12h`   DECIMAL(10,4),
  `PM10_delta_12h`      DECIMAL(6,1),
  `PM2_5_roll_mean_24h` DECIMAL(10,4),
  `PM2_5_roll_std_24h`  DECIMAL(10,4),
  `PM2_5_delta_24h`     DECIMAL(6,1),
  `PM10_roll_mean_24h`  DECIMAL(10,4),
  `PM10_roll_std_24h`   DECIMAL(10,4),
  `PM10_delta_24h`      DECIMAL(6,1),
  `pm25_pm10_ratio`  DECIMAL(8,6),
  `coarse_particle`  DECIMAL(6,1),
  UNIQUE KEY `uk_datetime` (`datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='完整特征数据(46维)';

-- ============================================================
-- 4. 模型评估结果表 (来源: all_model_result.csv)
-- ============================================================
DROP TABLE IF EXISTS `model_results`;
CREATE TABLE `model_results` (
  `id`          INT AUTO_INCREMENT PRIMARY KEY,
  `model_name`  VARCHAR(50) NOT NULL,
  `PM2_5_MAE`   DOUBLE,
  `PM2_5_RMSE`  DOUBLE,
  `PM2_5_R2`    DOUBLE,
  `PM10_MAE`    DOUBLE,
  `PM10_RMSE`   DOUBLE,
  `PM10_R2`     DOUBLE,
  UNIQUE KEY `uk_model` (`model_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='各模型评估指标';

-- ============================================================
-- 5. 注意力权重表 (来源: attention_weight.csv)
-- ============================================================
DROP TABLE IF EXISTS `attention_weights`;
CREATE TABLE `attention_weights` (
  `id`                  INT AUTO_INCREMENT PRIMARY KEY,
  `history_hour`       INT NOT NULL,
  `mean_attention_weight` DOUBLE,
  UNIQUE KEY `uk_hour` (`history_hour`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='注意力机制历史小时权重';
