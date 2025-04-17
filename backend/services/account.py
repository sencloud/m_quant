from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.account import AccountDB
from config import settings
from utils.logger import logger
import uuid

class AccountService:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
        AccountDB.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logger
        
        # 初始化账户
        self._init_account()

    def _init_account(self) -> None:
        """初始化账户"""
        try:
            db = self.SessionLocal()
            # 检查是否已存在账户
            account = db.query(AccountDB).first()
            if not account:
                # 创建新账户
                account = AccountDB(
                    initial_balance=1000000.0,  # 初始资金100万
                    current_balance=1000000.0,  # 当前资产等于初始资金
                    available_balance=1000000.0,  # 可用资金等于当前资产
                    total_profit=0.0,
                    total_commission=0.0,
                    position_cost=0.0,
                    position_quantity=0
                )
                db.add(account)
                db.commit()
                self.logger.info("账户初始化成功")
        except Exception as e:
            self.logger.error(f"初始化账户失败: {e}")
            db.rollback()
            raise

    def get_account(self) -> AccountDB:
        """获取账户信息"""
        try:
            db = self.SessionLocal()
            account = db.query(AccountDB).first()
            return account
        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            raise
        finally:
            db.close()

    def update_account(self, account: AccountDB) -> None:
        """更新账户信息"""
        try:
            db = self.SessionLocal()
            db_account = db.query(AccountDB).first()
            if not db_account:
                raise ValueError("账户不存在")
            
            # 更新账户信息
            db_account.current_balance = account.current_balance
            db_account.available_balance = account.available_balance
            db_account.total_profit = account.total_profit
            db_account.total_commission = account.total_commission
            db_account.position_cost = account.position_cost
            db_account.position_quantity = account.position_quantity
            
            db.commit()
            self.logger.info("账户信息更新成功")
        except Exception as e:
            self.logger.error(f"更新账户信息失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def update_balance(self, profit: float, commission: float) -> None:
        """更新账户余额"""
        try:
            db = self.SessionLocal()
            account = db.query(AccountDB).first()
            if not account:
                raise ValueError("账户不存在")
            
            # 更新账户余额
            account.current_balance += profit
            account.available_balance += profit
            account.total_profit += profit
            account.total_commission += commission
            
            db.commit()
            self.logger.info(f"账户余额更新成功: 盈亏={profit}, 手续费={commission}")
        except Exception as e:
            self.logger.error(f"更新账户余额失败: {e}")
            db.rollback()
            raise
        finally:
            db.close() 