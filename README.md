# 豆粕品种量化交易策略平台

## 项目简介

这是一个专注于豆粕品种交易的量化交易策略平台。平台整合了豆粕ETF、豆粕期货和期权的交易分析，为投资者提供全方位的交易决策支持。

## 核心功能

- **核心观点**: 提供豆粕市场的核心交易观点和策略建议
- **每日分析**: 实时更新市场动态，技术面和基本面分析
- **AI量化模型**: 基于深度强化学习的交易策略辅助系统

## 技术架构

### 前端技术栈
- React + TypeScript
- TailwindCSS
- Ant Design Pro
- ECharts 图表库
- WebSocket实时数据

### 后端技术栈
- Python FastAPI
- SQLite数据库
- Tushare数据接口
- PyTorch深度学习框架
- 日志监控系统

## 快速开始

### 环境要求
- Node.js >= 16
- Python >= 3.8
- pip
- npm 或 yarn

### 前端部署
```bash
cd frontend
npm install
npm start
```

### 后端部署
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app
```

### 环境变量配置
1. 在backend目录下复制`.env.sample`为`.env`
2. 配置必要的环境变量：
   - TUSHARE_TOKEN
   - DATABASE_URL
   - API_KEY等

## 项目结构
```
singz_quant/
├── frontend/           # React前端项目
│   ├── src/           # 源代码
│   ├── public/        # 静态资源
│   └── build/         # 构建输出
├── backend/           # FastAPI后端服务
│   ├── models/        # 数据模型
│   ├── routers/       # API路由
│   ├── services/      # 业务逻辑
│   └── utils/         # 工具函数
└── docs/             # 项目文档
```

## 许可证

MIT License