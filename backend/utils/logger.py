import sys
from loguru import logger
from pathlib import Path

# 创建日志目录
log_path = Path("logs")
log_path.mkdir(exist_ok=True)

# 配置日志
logger.remove()  # 移除默认的处理器

# 添加控制台处理器
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 添加文件处理器
logger.add(
    "logs/app_{time}.log",
    rotation="500 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    encoding="utf-8"
) 