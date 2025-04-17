from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models.position import PositionDB, Position, PositionCreate
from utils.logger import logger
from typing import List, Optional
from config import settings

class PositionService:
    def __init__(self, db: Session = None):
        self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
        PositionDB.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = db or self.SessionLocal()
        self.logger = logger

    def get_position(self, symbol: str) -> Optional[PositionDB]:
        """获取指定品种的持仓"""
        try:
            return self.db.query(PositionDB).filter(
                PositionDB.symbol == symbol,
                PositionDB.status == 'open'
            ).first()
        except Exception as e:
            self.logger.error(f"获取持仓失败: {e}")
            return None

    def create_position(self, position: PositionCreate) -> PositionDB:
        """创建新持仓"""
        try:
            db_position = PositionDB(**position.dict())
            self.db.add(db_position)
            self.db.commit()
            self.db.refresh(db_position)
            return db_position
        except Exception as e:
            self.logger.error(f"创建持仓失败: {e}")
            self.db.rollback()
            raise

    def update_position(self, position: PositionDB) -> PositionDB:
        """更新持仓"""
        try:
            self.db.commit()
            self.db.refresh(position)
            return position
        except Exception as e:
            self.logger.error(f"更新持仓失败: {e}")
            self.db.rollback()
            raise

    def close_position(self, symbol: str) -> None:
        """平仓"""
        try:
            position = self.get_position(symbol)
            if position:
                position.status = 'closed'
                self.db.commit()
        except Exception as e:
            self.logger.error(f"平仓失败: {e}")
            self.db.rollback()
            raise 