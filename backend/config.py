from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Tushare API配置
    TUSHARE_TOKEN: str = "你的tushare token"
    
    # Deepseek API配置
    DEEPSEEK_API_KEY: str

    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    
    # 应用配置
    PROJECT_NAME: str = "豆粕组合策略"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str | None = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    
    # 安全配置
    SECRET_KEY: str = "your_secret_key_here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 

# 期货交易乘数配置
FUTURES_MULTIPLIER = {
    # 商品期货
    'M': 10,     # 豆粕
    'Y': 10,     # 豆油
    'P': 10,     # 棕榈油
    'C': 10,     # 玉米
    'A': 10,     # 豆一
    'RB': 10,    # 螺纹钢
    'I': 100,    # 铁矿石
    'J': 100,    # 焦炭
    'JM': 60,    # 焦煤
    'CU': 5,     # 铜
    'AL': 5,     # 铝
    'ZN': 5,     # 锌
    'PB': 5,     # 铅
    'AU': 1000,  # 黄金
    'AG': 15,    # 白银
    'RU': 10,    # 橡胶
    'FU': 10,    # 燃油
    'TA': 5,     # PTA
    'MA': 10,    # 甲醇
    'PP': 5,     # 聚丙烯
    'L': 5,      # 塑料
    'V': 5,      # PVC
    
    # 金融期货
    'IF': 300,   # 沪深300
    'IC': 200,   # 中证500
    'IH': 300,   # 上证50
    'T': 10000,  # 国债
    'TF': 10000, # 5年国债
}

def get_multiplier(symbol: str) -> int:
    """
    获取期货品种的交易乘数
    :param symbol: 期货代码，例如 'M2401'
    :return: 交易乘数，如果找不到则返回1
    """
    # 提取品种代码（去掉月份）
    # 只提取第一个字母或连续的字母作为品种代码
    import re
    product = re.match(r'([A-Za-z]+)', symbol.upper())
    product = product.group(1) if product else ""
    return FUTURES_MULTIPLIER.get(product, 1)

def is_futures(symbol: str) -> bool:
    """
    判断是否是期货品种
    :param symbol: 完整代码，例如 'futures-M2401'
    :return: 是否是期货
    """
    if not symbol:
        return False
    parts = symbol.split('-')
    return len(parts) > 1 and parts[0].lower() == 'futures' 