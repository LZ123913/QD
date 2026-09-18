-- ============================================================
-- 数据导入脚本 - 在HeidiSQL中执行
-- 注意: 先把CSV文件路径改成你电脑上的实际路径
-- 方式一: 用LOAD DATA INFILE (推荐,速度快)
-- 方式二: 用HeidiSQL的"导入CSV文件"界面手动导入
-- ============================================================

USE qingdao_air;

-- ============================================================
-- 方式一: LOAD DATA INFILE 导入
-- 请将路径替换为你的实际CSV文件路径
-- MySQL需开启 secure_file_priv 或使用 LOCAL
-- ============================================================

-- 1. 导入原始污染物数据 (data_all_poll.csv)
LOAD DATA LOCAL INFILE 'C:/path/to/data_all_poll.csv'
INTO TABLE `air_quality_raw`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(`datetime`, `AQI`, `CO`, `NO2`, `O3`, `O3_8h`, `PM10`, `PM2_5`, `SO2`);

-- 2. 导入PM数据 (data_pm.csv)
LOAD DATA LOCAL INFILE 'C:/path/to/data_pm.csv'
INTO TABLE `air_quality_pm`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(`datetime`, `PM2_5`, `PM10`);

-- 3. 导入完整特征数据 (all_feature_data.csv)
-- 列顺序与CSV表头一致,共47列(含datetime)
LOAD DATA LOCAL INFILE 'C:/path/to/all_feature_data.csv'
INTO TABLE `air_quality_features`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(`datetime`, `AQI`, `CO`, `NO2`, `O3`, `O3_8h`, `PM10`, `PM2_5`, `SO2`,
 `hour`, `hour_sin`, `hour_cos`, `is_workday`,
 `PM2_5_lag_1h`, `PM10_lag_1h`,
 `PM2_5_lag_3h`, `PM10_lag_3h`,
 `PM2_5_lag_6h`, `PM10_lag_6h`,
 `PM2_5_lag_12h`, `PM10_lag_12h`,
 `PM2_5_lag_24h`, `PM10_lag_24h`,
 `PM2_5_roll_mean_3h`, `PM2_5_roll_std_3h`, `PM2_5_delta_3h`,
 `PM10_roll_mean_3h`, `PM10_roll_std_3h`, `PM10_delta_3h`,
 `PM2_5_roll_mean_6h`, `PM2_5_roll_std_6h`, `PM2_5_delta_6h`,
 `PM10_roll_mean_6h`, `PM10_roll_std_6h`, `PM10_delta_6h`,
 `PM2_5_roll_mean_12h`, `PM2_5_roll_std_12h`, `PM2_5_delta_12h`,
 `PM10_roll_mean_12h`, `PM10_roll_std_12h`, `PM10_delta_12h`,
 `PM2_5_roll_mean_24h`, `PM2_5_roll_std_24h`, `PM2_5_delta_24h`,
 `PM10_roll_mean_24h`, `PM10_roll_std_24h`, `PM10_delta_24h`,
 `pm25_pm10_ratio`, `coarse_particle`);

-- 4. 导入模型评估结果 (all_model_result.csv)
LOAD DATA LOCAL INFILE 'C:/path/to/all_model_result.csv'
INTO TABLE `model_results`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(`model_name`, `PM2_5_MAE`, `PM2_5_RMSE`, `PM2_5_R2`, `PM10_MAE`, `PM10_RMSE`, `PM10_R2`);

-- 5. 导入注意力权重 (attention_weight.csv)
LOAD DATA LOCAL INFILE 'C:/path/to/attention_weight.csv'
INTO TABLE `attention_weights`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(`history_hour`, `mean_attention_weight`);

-- ============================================================
-- 方式二: HeidiSQL图形界面导入
-- 1. 选中数据库 qingdao_air -> 右键 -> 导入CSV文件
-- 2. 选择对应CSV, 目标表选对应表名
-- 3. 字段映射自动匹配, 注意:
--    - CSV中的 "PM2.5" 列映射到数据库的 PM2_5
--    - CSV中的 "PM10" 列映射到数据库的 PM10
-- 4. 按上面5个表逐一导入即可
-- ============================================================
