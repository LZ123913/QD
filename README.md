# 青岛大气PM2.5/PM10分析与预测系统

基于2021-2026年青岛小时级监测数据，实现空气质量的统计分析、可视化展示与深度学习浓度预测。

## 项目结构

```
青岛/
├── index.html                # 前端入口
├── package.json              # 前端依赖与构建配置
├── vite.config.js            # Vite构建配置
├── jsconfig.json
├── README.md                 # 本文件
├── public/                   # 前端静态资源
│   ├── data_pm_filled.csv    # 前端可视化用数据
│   └── favicon.ico
├── src/                      # Vue 3 前端源码
│   ├── App.vue               # 主布局
│   ├── main.js               # 入口
│   ├── router/index.js       # 路由
│   ├── utils/data.js         # 数据处理与统计函数
│   └── views/                # 页面组件
│       ├── DashboardView.vue  # 数据概览
│       ├── DataView.vue       # 原始数据
│       ├── TrendView.vue      # 趋势分析
│       ├── CorrelationView.vue# 关联分析
│       ├── SourceView.vue     # 成因分析
│       └── PredictView.vue    # 浓度预测
└── air_project/              # 后端AI模型与数据
    ├── server/               # 预测服务
    │   ├── app.py            # HTTP服务入口
    │   ├── predict_engine.py # 预测引擎
    │   └── nn_numpy.py        # 纯NumPy前向传播
    ├── database/             # 数据库脚本
    │   ├── init.sql          # 建库建表脚本
    │   └── import_data.sql   # 数据导入脚本
    ├── pt_loader.py          # PyTorch权重加载器(纯NumPy)
    ├── *.pt                  # 5个模型权重
    ├── *.csv                 # 数据与结果
    ├── scaler_x.pkl          # 输入标准化器
    └── scaler_y.pkl          # 输出标准化器
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vue Router + ECharts + PapaParse |
| 构建 | Vite |
| 后端 | Python标准库 http.server |
| AI模型 | PyTorch训练(运行时纯NumPy推理,无需安装torch) |
| 数据库 | MySQL / MariaDB (HeidiSQL管理) |
| 数据处理 | NumPy + Pandas |

## 环境要求

- **Node.js** >= 18 (推荐 22.x)
- **Python** >= 3.8
- **MySQL** >= 5.7 或 MariaDB >= 10.3
- **HeidiSQL** (数据库可视化管理工具)

## 部署步骤

### 第一步：数据库初始化

1. 打开HeidiSQL，连接到MySQL/MariaDB服务器
2. 打开 `air_project/database/init.sql`，全选执行（创建数据库及5张表）
3. 打开 `air_project/database/import_data.sql`，将CSV路径改为实际路径后执行
   - 或使用HeidiSQL图形界面：右键数据库 -> 导入CSV文件 -> 逐表导入

### 第二步：后端启动

```sh
cd air_project/server
pip install numpy pandas
python app.py
```

预测服务启动后监听 `http://127.0.0.1:5000`

### 第三步：前端启动

```sh
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`

### 第四步：生产构建

```sh
npm run build      # 生成 dist/ 目录
npm run preview    # 本地预览构建产物
```

将 `dist/` 目录部署到任意Web服务器（Nginx/Apache/IIS）即可。

## 数据说明

| 数据文件 | 说明 | 时间范围 |
|---------|------|---------|
| data_all_poll.csv | 原始污染物(AQI/CO/NO2/O3/O3_8h/PM10/PM2.5/SO2) | 2021-2026 |
| data_pm.csv | PM2.5与PM10小时数据 | 2021-2026 |
| all_feature_data.csv | 46维特征数据(含滞后/滚动统计) | 2021-2026 |
| all_model_result.csv | 各模型评估指标(MAE/RMSE/R²) | - |

## 模型说明

| 模型 | 文件 | 说明 |
|------|------|------|
| LSTM基线 | baseline_lstm.pt | 标准LSTM网络 |
| GRU基线 | baseline_gru.pt | 标准GRU网络 |
| CNN-LSTM | cnn_lstm.pt | CNN特征提取+LSTM时序 |
| Attention-LSTM | att_lstm.pt | 带注意力机制的LSTM |
| 消融实验 | ablation_noatt_lstm.pt | 去除注意力的对照 |

## 项目仓库

- Gitee: (待上传后填写)
- GitHub: (待上传后填写)
