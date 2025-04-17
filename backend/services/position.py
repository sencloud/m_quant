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
        self.logger = logger

    def get_position(self, symbol: str) -> Optional[PositionDB]:
        """获取指定品种的持仓"""
        try:
            db = self.SessionLocal()
            self.logger.info(f"尝试获取持仓，品种: {symbol}")
            position = db.query(PositionDB).filter(
                PositionDB.symbol == symbol,
                PositionDB.status.in_(['open', 'partial_closed'])  # 同时查询open和partial_closed状态的持仓
            ).first()
            self.logger.info(f"查询结果: {position}")
            if position:
                self.logger.info(f"持仓详情 - ID: {position.id}, 品种: {position.symbol}, 状态: {position.status}, 数量: {position.quantity}, 价格: {position.price}")
            return position
        except Exception as e:
            self.logger.error(f"获取持仓失败: {e}")
            return None
        finally:
            db.close()

    def create_position(self, position: PositionCreate) -> PositionDB:
        """创建新持仓"""
        try:
            db = self.SessionLocal()
            db_position = PositionDB(**position.dict())
            db.add(db_position)
            db.commit()
            db.refresh(db_position)
            return db_position
        except Exception as e:
            self.logger.error(f"创建持仓失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def update_position(self, position: Position) -> Position:
        """更新持仓信息"""
        try:
            db = self.SessionLocal()
            db_position = db.query(PositionDB).filter(PositionDB.id == position.id).first()
            if db_position:
                db_position.symbol = position.symbol
                db_position.price = position.price
                db_position.quantity = position.quantity
                db_position.status = position.status
                db.commit()
                db.refresh(db_position)
                return Position(
                    id=db_position.id,
                    symbol=db_position.symbol,
                    price=db_position.price,
                    quantity=db_position.quantity,
                    status=db_position.status,
                    created_at=db_position.created_at,
                    updated_at=db_position.updated_at
                )
            else:
                raise ValueError(f"Position with id {position.id} not found")
        except Exception as e:
            self.logger.error(f"更新持仓失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def close_position(self, symbol: str) -> None:
        """平仓"""
        try:
            db = self.SessionLocal()
            position = self.get_position(symbol)
            if position:
                position.status = 'closed'
                db.commit()
        except Exception as e:
            self.logger.error(f"平仓失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def delete_position(self, position_id: str) -> None:
        """删除持仓"""
        try:
            db = self.SessionLocal()
            position = db.query(PositionDB).filter(PositionDB.id == position_id).first()
            if not position:
                raise ValueError(f"持仓不存在: {position_id}")
            
            db.delete(position)
            db.commit()
            self.logger.info(f"删除持仓成功: {position_id}")
        except Exception as e:
            self.logger.error(f"删除持仓失败: {e}")
            db.rollback()
            raise
        finally:
            db.close() 