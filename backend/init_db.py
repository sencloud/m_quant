from models.soybean import Base
from config import settings
from sqlalchemy import create_engine

def init_db():
    """初始化数据库表"""
    engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
    Base.metadata.create_all(bind=engine)
    print("数据库表初始化完成")

if __name__ == "__main__":
    init_db() 