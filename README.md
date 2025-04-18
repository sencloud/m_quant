# 豆粕品种量化交易策略平台

## 项目简介

这是一个专注于豆粕品种交易的量化交易策略平台。平台整合了豆粕ETF、豆粕期货和期权的交易分析，为投资者提供全方位的交易决策支持。
访问网站立即体验：https://www.singzquant.com/

## 核心功能

- **核心观点**: 提供豆粕市场的核心交易观点和策略建议
- **每日分析**: 实时更新市场动态，技术面和基本面分析
- **AI量化模型**: 基于深度强化学习和多智能体的交易策略辅助系统
- 功能截图
![image](https://github.com/user-attachments/assets/e1d5a3d5-cfb6-466a-8cf9-400cb58d5800)
![image](https://github.com/user-attachments/assets/02504afe-fe54-4b20-b4ad-4a6f38d57b45)
![image](https://github.com/user-attachments/assets/5879b683-1846-4a2c-86a3-ddf540b43e4f)
![image](https://github.com/user-attachments/assets/833a6ad6-48d3-4d6b-908e-6550bcf84326)
![image](https://github.com/user-attachments/assets/469b615c-aef9-4aaf-8ab4-393dc23ab04e)

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

## 其他
如果你喜欢我的项目，可以给我买杯咖啡：
<img src="https://github.com/user-attachments/assets/e75ef971-ff56-41e5-88b9-317595d22f81" alt="image" width="300" height="300">

## 风险提示

本系统仅供学习和研究使用，不构成任何投资建议。使用本系统进行实盘交易需要自行承担风险。

## 许可证

MIT License
