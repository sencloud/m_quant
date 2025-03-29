from sqlalchemy import create_engine, Column, String, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional
from models.trading import DailyStrategyAnalysis
from config import settings
from utils.logger import logger

Base = declarative_base()

class StrategyAnalysisDB(Base):
    __tablename__ = "strategy_analysis"

    date = Column(Date, primary_key=True)
    reasoning_content = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradingService:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logger

    def get_strategy_analysis(self, date: str) -> Optional[DailyStrategyAnalysis]:
        """从数据库获取指定日期的策略分析"""
        try:
            db = self.SessionLocal()
            # 将字符串日期转换为 date 对象
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
            analysis = db.query(StrategyAnalysisDB).filter(StrategyAnalysisDB.date == query_date).first()
            if analysis:
                return DailyStrategyAnalysis(
                    date=analysis.date,
                    reasoning_content=analysis.reasoning_content,
                    content=analysis.content,
                    created_at=analysis.created_at.date(),  # 转换为 date 对象
                    updated_at=analysis.updated_at.date()   # 转换为 date 对象
                )
            return None
        except Exception as e:
            self.logger.error(f"获取策略分析失败: {str(e)}")
            raise
        finally:
            db.close()

    def save_strategy_analysis(self, analysis: DailyStrategyAnalysis) -> None:
        """保存策略分析到数据库"""
        try:
            db = self.SessionLocal()
            db_analysis = StrategyAnalysisDB(
                date=analysis.date,
                reasoning_content=analysis.reasoning_content,
                content=analysis.content
            )
            db.merge(db_analysis)
            db.commit()
            self.logger.info(f"策略分析已保存到数据库 - 日期: {analysis.date}")
        except Exception as e:
            self.logger.error(f"保存策略分析失败: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close() 