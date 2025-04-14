from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import market_data, trading, fundamental, core_factor, arbitrage, trend_follow, obv_adx_ema
from config import settings
from utils.logger import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端开发服务器访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)
logger.info("CORS中间件配置完成")

# 注册路由
app.include_router(
    market_data.router,
    prefix=f"{settings.API_V1_STR}/market",
    tags=["market"]
)
logger.info("市场数据路由注册完成")

app.include_router(
    trading.router,
    prefix=f"{settings.API_V1_STR}/trading",
    tags=["trading"]
)
logger.info("交易策略路由注册完成")

app.include_router(
    fundamental.router,
    prefix=f"{settings.API_V1_STR}/fundamental",
    tags=["fundamental"]
)
logger.info("基本面分析路由注册完成")

app.include_router(
    core_factor.router,
    prefix=f"{settings.API_V1_STR}/core-factor",
    tags=["core_factor"]
)
logger.info("核心驱动因子分析路由注册完成")

app.include_router(
    arbitrage.router,
    prefix=f"{settings.API_V1_STR}/arbitrage",
    tags=["arbitrage"]
)
logger.info("套利策略路由注册完成")

app.include_router(
    trend_follow.router,
    prefix=f"{settings.API_V1_STR}/trend_follow",
    tags=["trend_follow"]
)
logger.info("趋势跟随策略路由注册完成")

app.include_router(
    obv_adx_ema.router,
    prefix=f"{settings.API_V1_STR}/obv_adx_ema",
    tags=["obv_adx_ema"]
)
logger.info("OBV、ADX与EMA组合策略路由注册完成")

@app.on_event("startup")
async def startup_event():
    logger.info("应用启动")
    logger.info(f"项目名称: {settings.PROJECT_NAME}")
    logger.info(f"API版本: {settings.API_V1_STR}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("应用关闭")

@app.get("/")
async def root():
    logger.debug("收到根路径请求")
    return {"message": "Welcome to 豆粕组合策略 API"} 