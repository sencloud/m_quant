from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Enum as SQLEnum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
from typing import List, Optional
from models.signals import Signal, SignalCreate, SignalUpdate, SignalType, SignalStatus
from config import settings
from utils.logger import logger
import uuid
import random
from services.account import AccountService
from services.position import PositionService
from models.position import PositionCreate
from config import get_multiplier, is_futures
from models.kline import KLineData

Base = declarative_base()

class SignalDB(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True)
    date = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    type = Column(SQLEnum(SignalType), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(SQLEnum(SignalStatus), nullable=False, default=SignalStatus.OPEN)
    reason = Column(String, nullable=False)  # 开平仓原因
    close_date = Column(DateTime, nullable=True)
    close_price = Column(Float, nullable=True)
    profit = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class SignalService:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logger
        self.account_service = AccountService()
        
        # 豆粕相关交易品种
        self.symbols = {
            'stock': ['600598', '000061'],  # 北大荒、农产品
            'futures': ['M2405', 'M2406', 'M2407'],  # 豆粕期货
            'options': ['M2405-C-3500', 'M2405-P-3500', 'M2406-C-3600', 'M2406-P-3600'],  # 豆粕期权
            'etf': ['159985']  # 豆粕ETF
        }
        
        # 初始化模拟数据
        # self._init_mock_data()

    def _init_mock_data(self):
        """初始化模拟数据"""
        try:
            db = self.SessionLocal()
            # 检查是否已有数据
            if db.query(SignalDB).first():
                return
                
            # 生成最近30天的模拟数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            current_date = start_date
            while current_date <= end_date:
                # 每个交易日生成2-5个信号
                for _ in range(random.randint(2, 5)):
                    # 随机选择品种类型
                    symbol_type = random.choice(list(self.symbols.keys()))
                    symbol = random.choice(self.symbols[symbol_type])
                    
                    # 生成信号
                    signal_type = random.choice(['buy', 'sell'])
                    price = self._generate_price(symbol_type, symbol)
                    quantity = random.randint(1, 10) * 100
                    
                    # 生成随机时间（9:30-15:00之间）
                    hour = random.randint(9, 14)
                    minute = random.randint(0, 59)
                    if hour == 9:
                        minute = random.randint(30, 59)
                    elif hour == 14:
                        minute = random.randint(0, 30)
                    current_time = current_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
                    
                    # 80%概率是已平仓信号
                    status = 'closed' if random.random() < 0.8 else 'open'
                    
                    # 生成开平仓原因
                    reasons = {
                        'buy': ['突破阻力位', '均线金叉', 'MACD金叉', 'RSI超卖', '支撑位反弹'],
                        'sell': ['跌破支撑位', '均线死叉', 'MACD死叉', 'RSI超买', '阻力位回落']
                    }
                    reason = random.choice(reasons[signal_type])
                    
                    # 如果是已平仓，生成平仓信息
                    close_date = None
                    close_price = None
                    profit = 0.0
                    
                    if status == 'closed':
                        # 平仓时间在开仓时间之后1-5天内
                        close_days = random.randint(1, 5)
                        close_hour = random.randint(9, 14)
                        close_minute = random.randint(0, 59)
                        if close_hour == 9:
                            close_minute = random.randint(30, 59)
                        elif close_hour == 14:
                            close_minute = random.randint(0, 30)
                        close_date = current_time + timedelta(days=close_days)
                        close_date = close_date.replace(hour=close_hour, minute=close_minute, second=random.randint(0, 59))
                        close_price = price * (1 + random.uniform(-0.05, 0.05))
                        profit = (close_price - price) * quantity if signal_type == 'buy' else (price - close_price) * quantity
                        
                        # 计算手续费并更新账户余额
                        commission = abs(close_price * quantity * 0.0003)
                        self.account_service.update_balance(profit, commission)
                    
                    # 添加类型前缀到品种名称
                    type_prefix = {
                        'stock': '股票',
                        'futures': '期货',
                        'options': '期权',
                        'etf': 'ETF'
                    }[symbol_type]
                    display_symbol = f"{type_prefix}-{symbol}"
                    
                    # 创建信号记录
                    signal = SignalDB(
                        id=str(uuid.uuid4()),
                        date=current_time,
                        symbol=display_symbol,
                        type=signal_type,
                        price=price,
                        quantity=quantity,
                        status=status,
                        reason=reason,
                        close_date=close_date,
                        close_price=close_price,
                        profit=profit
                    )
                    db.add(signal)
                
                current_date += timedelta(days=1)
            
            db.commit()
            self.logger.info("模拟数据初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化模拟数据失败: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def _generate_price(self, symbol_type: str, symbol: str) -> float:
        """根据品种类型生成合理的价格"""
        base_prices = {
            'stock': 15.0,  # 股票基准价
            'futures': 3500.0,  # 期货基准价
            'options': 100.0,  # 期权基准价
            'etf': 1.5  # ETF基准价
        }
        
        base_price = base_prices[symbol_type]
        # 在基准价上下10%范围内波动
        return base_price * (1 + random.uniform(-0.1, 0.1))

    def get_signals(self, start_date: datetime, end_date: datetime, signal_type: Optional[str] = None, page: int = 1, page_size: int = 10) -> tuple[List[Signal], int]:
        """获取指定日期范围内的信号"""
        try:
            db = self.SessionLocal()
            query = db.query(SignalDB).filter(
                SignalDB.date >= start_date,
                SignalDB.date <= end_date
            )
            
            # 根据类型筛选
            if signal_type:
                if signal_type in ['BUY_OPEN', 'SELL_OPEN', 'BUY_CLOSE', 'SELL_CLOSE']:
                    query = query.filter(SignalDB.type == signal_type)
                elif signal_type in ['open', 'closed']:
                    query = query.filter(SignalDB.status == signal_type)
            
            # 获取总记录数
            total = query.count()
            
            # 按日期时间倒序排序并分页
            signals = query.order_by(SignalDB.date.desc())\
                .offset((page - 1) * page_size)\
                .limit(page_size)\
                .all()
            
            # 转换为Pydantic模型
            return [
                Signal(
                    id=s.id,
                    date=s.date,
                    symbol=s.symbol,
                    type=s.type,
                    price=s.price,
                    quantity=s.quantity,
                    status=s.status,
                    reason=s.reason,
                    close_date=s.close_date,
                    close_price=s.close_price,
                    profit=s.profit,
                    created_at=s.created_at,
                    updated_at=s.updated_at
                ) for s in signals
            ], total
        except Exception as e:
            self.logger.error(f"获取信号失败: {e}")
            raise
        finally:
            db.close()

    def _get_signal_by_id(self, signal_id: int) -> Optional[Signal]:
        """根据ID获取信号"""
        return self.SessionLocal().query(SignalDB).filter(SignalDB.id == signal_id).first()

    def calc_trade(self, signal: Signal) -> None:
        """计算交易盈亏并更新账户"""
        try:
            self.logger.info(f"开始计算交易: {signal.id}, 类型: {signal.type}, 状态: {signal.status}")
            
            # 获取账户信息
            account = self.account_service.get_account()
            if not account:
                self.logger.error("账户不存在")
                return

            # 计算手续费 (假设手续费率为0.0003)
            commission_rate = 0.0003
            commission = signal.price * signal.quantity * commission_rate
            self.logger.info(f"计算手续费: {commission}")

            # 计算交易金额
            trade_amount = signal.price * signal.quantity
            self.logger.info(f"交易金额: {trade_amount}")

            # 获取持仓服务
            position_service = PositionService()

            # 获取该品种的持仓信息
            position = position_service.get_position(signal.symbol)
            self.logger.info(f"当前持仓: {position}")

            # 判断是否是期货
            is_futures_symbol = is_futures(signal.symbol)
            
            # 如果是期货，获取交易乘数
            multiplier = get_multiplier(signal.symbol.split('-')[1]) if is_futures_symbol else 10
            self.logger.info(f"品种: {signal.symbol}，{signal.symbol.split('-')[1]}, 是否期货: {is_futures_symbol}, 交易乘数: {multiplier}")

            db = self.SessionLocal()
            try:
                if signal.type == 'BUY_OPEN':
                    self.logger.info("处理买入开仓")
                    # 买入开仓
                    if position:
                        # 已有持仓，更新持仓成本
                        total_cost = position.price * position.quantity + trade_amount
                        total_quantity = position.quantity + signal.quantity
                        position.price = total_cost / total_quantity
                        position.quantity = total_quantity
                        position_service.update_position(position)
                        self.logger.info(f"更新持仓: {position}")
                    else:
                        # 新建持仓
                        position = position_service.create_position(PositionCreate(
                            symbol=signal.symbol,
                            price=signal.price,
                            quantity=signal.quantity,
                            status='open'
                        ))
                        self.logger.info(f"新建持仓: {position}")
                    
                    # 更新可用资金
                    if is_futures_symbol:
                        # 期货只需要保证金，假设保证金比例为10%
                        margin = trade_amount * 0.1
                        account.available_balance -= (margin + commission)
                        self.logger.info(f"期货保证金: {margin}")
                    else:
                        # 股票需要全额资金
                        account.available_balance -= (trade_amount + commission)
                        self.logger.info(f"股票全额资金: {trade_amount}")
                    
                    account.total_commission += commission
                    self.logger.info(f"更新账户余额: {account.available_balance}")

                elif signal.type == 'SELL_OPEN':
                    self.logger.info("处理卖出开仓")
                    # 卖出开仓
                    if position:
                        # 已有持仓，更新持仓成本
                        total_cost = position.price * position.quantity + trade_amount
                        total_quantity = position.quantity + signal.quantity
                        position.price = total_cost / total_quantity
                        position.quantity = total_quantity
                        position_service.update_position(position)
                        self.logger.info(f"更新持仓: {position}")
                    else:
                        # 新建持仓
                        position = position_service.create_position(PositionCreate(
                            symbol=signal.symbol,
                            price=signal.price,
                            quantity=signal.quantity,
                            status='open'
                        ))
                        self.logger.info(f"新建持仓: {position}")
                    
                    # 更新可用资金
                    if is_futures_symbol:
                        # 期货只需要保证金，假设保证金比例为10%
                        margin = trade_amount * 0.1
                        account.available_balance -= (margin + commission)
                        self.logger.info(f"期货保证金: {margin}")
                    else:
                        # 股票需要全额资金
                        account.available_balance -= (trade_amount + commission)
                        self.logger.info(f"股票全额资金: {trade_amount}")
                    
                    account.total_commission += commission
                    self.logger.info(f"更新账户余额: {account.available_balance}")

                elif signal.type == 'BUY_CLOSE':
                    self.logger.info("处理买入平仓")
                    # 买入平仓（对应卖出开仓）
                    if position:
                        # 计算盈亏：卖出开仓，买入平仓，价格下跌是盈利
                        profit = (position.price - signal.price) * signal.quantity * multiplier
                        self.logger.info(f"计算盈亏: {profit}, 平仓价: {signal.price}, 持仓价: {position.price}, 乘数: {multiplier}")
                        
                        # 更新信号盈亏和状态
                        db_signal = db.query(SignalDB).filter(SignalDB.id == signal.id).first()
                        if db_signal:
                            db_signal.profit = profit
                            db_signal.close_price = signal.price
                            db_signal.close_date = signal.date
                            
                            # 更新持仓
                            position.quantity -= signal.quantity
                            if position.quantity <= 0:
                                position_service.delete_position(position.id)
                                db_signal.status = 'closed'
                                # 找到对应的开仓信号并更新状态
                                open_signal = db.query(SignalDB).filter(
                                    SignalDB.symbol == signal.symbol,
                                    SignalDB.type == 'SELL_OPEN',
                                    SignalDB.status.in_(['open', 'partial_closed'])
                                ).first()
                                if open_signal:
                                    open_signal.status = 'closed'
                                    self.logger.info(f"更新开仓信号状态为已平仓: {open_signal.id}")
                                self.logger.info("完全平仓，删除持仓")
                            else:
                                position.status = 'partial_closed'  # 部分平仓
                                position_service.update_position(position)
                                db_signal.status = 'partial_closed'
                                # 找到对应的开仓信号并更新状态
                                open_signal = db.query(SignalDB).filter(
                                    SignalDB.symbol == signal.symbol,
                                    SignalDB.type == 'SELL_OPEN',
                                    SignalDB.status == 'open'
                                ).first()
                                if open_signal:
                                    open_signal.status = 'partial_closed'
                                    self.logger.info(f"更新开仓信号状态为部分平仓: {open_signal.id}")
                                self.logger.info(f"部分平仓，更新持仓: {position}")
                            
                            # 更新账户余额
                            account.available_balance += profit
                            account.total_commission += commission
                            self.logger.info(f"更新账户余额: {account.available_balance}")
                            
                            # 保存所有更新
                            db.commit()
                            self.logger.info(f"更新信号状态和盈亏: {signal.id}")
                            
                            # 更新信号对象以反映变更
                            signal.status = db_signal.status
                            signal.profit = profit
                            signal.close_price = signal.price
                            signal.close_date = signal.date

                elif signal.type == 'SELL_CLOSE':
                    self.logger.info("处理卖出平仓")
                    # 卖出平仓（对应买入开仓）
                    if position:
                        # 计算盈亏：买入开仓，卖出平仓，价格上涨是盈利
                        profit = (signal.price - position.price) * signal.quantity * multiplier
                        self.logger.info(f"计算盈亏: {profit}, 平仓价: {signal.price}, 持仓价: {position.price}, 乘数: {multiplier}")
                        
                        # 更新信号盈亏和状态
                        db_signal = db.query(SignalDB).filter(SignalDB.id == signal.id).first()
                        if db_signal:
                            db_signal.profit = profit
                            db_signal.close_price = signal.price
                            db_signal.close_date = signal.date
                            
                            # 更新持仓
                            position.quantity -= signal.quantity
                            if position.quantity <= 0:
                                position_service.delete_position(position.id)
                                db_signal.status = 'closed'
                                # 找到对应的开仓信号并更新状态
                                open_signal = db.query(SignalDB).filter(
                                    SignalDB.symbol == signal.symbol,
                                    SignalDB.type == 'BUY_OPEN',
                                    SignalDB.status.in_(['open', 'partial_closed'])
                                ).first()
                                if open_signal:
                                    open_signal.status = 'closed'
                                    self.logger.info(f"更新开仓信号状态为已平仓: {open_signal.id}")
                                self.logger.info("完全平仓，删除持仓")
                            else:
                                position.status = 'partial_closed'  # 部分平仓
                                position_service.update_position(position)
                                db_signal.status = 'partial_closed'
                                # 找到对应的开仓信号并更新状态
                                open_signal = db.query(SignalDB).filter(
                                    SignalDB.symbol == signal.symbol,
                                    SignalDB.type == 'BUY_OPEN',
                                    SignalDB.status == 'open'
                                ).first()
                                if open_signal:
                                    open_signal.status = 'partial_closed'
                                    self.logger.info(f"更新开仓信号状态为部分平仓: {open_signal.id}")
                                self.logger.info(f"部分平仓，更新持仓: {position}")
                            
                            # 更新账户余额
                            account.available_balance += profit
                            account.total_commission += commission
                            self.logger.info(f"更新账户余额: {account.available_balance}")
                            
                            # 保存所有更新
                            db.commit()
                            self.logger.info(f"更新信号状态和盈亏: {signal.id}")
                            
                            # 更新信号对象以反映变更
                            signal.status = db_signal.status
                            signal.profit = profit
                            signal.close_price = signal.price
                            signal.close_date = signal.date

                # 保存账户更新
                self.account_service.update_account(account)
                self.logger.info(f"交易计算完成，最终账户余额: {account.available_balance}")
                
            except Exception as e:
                self.logger.error(f"计算交易失败: {e}")
                db.rollback()
                raise
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"计算交易失败: {e}")
            raise

    def create_signal(self, signal: SignalCreate) -> Signal:
        """创建新信号"""
        try:
            db = self.SessionLocal()
            signal_id = str(uuid.uuid4())
            
            # 调整时区，加8小时
            date = signal.date
            if date:
                date = date + timedelta(hours=8)
            
            close_date = signal.close_date
            if close_date:
                close_date = close_date + timedelta(hours=8)
            
            # 对于平仓类型的信号，设置close_date和close_price
            if signal.type in ['SELL_CLOSE', 'BUY_CLOSE']:
                close_date = date
                close_price = signal.price
            else:
                close_date = None
                close_price = None
            
            db_signal = SignalDB(
                id=signal_id,
                date=date,
                symbol=signal.symbol,
                type=signal.type,
                price=signal.price,
                quantity=signal.quantity,
                status=signal.status,
                reason=signal.reason,
                close_date=close_date,
                close_price=close_price,
                profit=0.0  # 初始盈亏为0，在calc_trade中计算
            )
            db.add(db_signal)
            db.commit()
            db.refresh(db_signal)
            
            # 转换为Signal对象
            signal_obj = Signal(
                id=db_signal.id,
                date=db_signal.date,
                symbol=db_signal.symbol,
                type=db_signal.type,
                price=db_signal.price,
                quantity=db_signal.quantity,
                status=db_signal.status,
                reason=db_signal.reason,
                close_date=db_signal.close_date,
                close_price=db_signal.close_price,
                profit=db_signal.profit,
                created_at=db_signal.created_at,
                updated_at=db_signal.updated_at
            )
            
            # 计算交易
            self.calc_trade(signal_obj)
            
            # 重新获取更新后的信号
            db_signal = db.query(SignalDB).filter(SignalDB.id == signal_id).first()
            
            return Signal(
                id=db_signal.id,
                date=db_signal.date,
                symbol=db_signal.symbol,
                type=db_signal.type,
                price=db_signal.price,
                quantity=db_signal.quantity,
                status=db_signal.status,
                reason=db_signal.reason,
                close_date=db_signal.close_date,
                close_price=db_signal.close_price,
                profit=db_signal.profit,
                created_at=db_signal.created_at,
                updated_at=db_signal.updated_at
            )
        except Exception as e:
            self.logger.error(f"创建信号失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def update_signal(self, signal_id: str, signal: SignalUpdate) -> Signal:
        """更新信号"""
        try:
            db = self.SessionLocal()
            db_signal = db.query(SignalDB).filter(SignalDB.id == signal_id).first()
            if not db_signal:
                raise ValueError(f"信号不存在: {signal_id}")
            
            # 记录原始状态
            original_status = db_signal.status
            original_type = db_signal.type
            original_price = db_signal.price
            original_quantity = db_signal.quantity

            # 更新字段
            if signal.status is not None:
                db_signal.status = signal.status
            if signal.close_date is not None:
                db_signal.close_date = signal.close_date
            if signal.close_price is not None:
                db_signal.close_price = signal.close_price
            if signal.profit is not None:
                db_signal.profit = signal.profit
                
                # 如果是平仓，更新账户余额
                if signal.status == 'closed':
                    # 计算手续费（假设为成交金额的0.0003）
                    commission = abs(signal.close_price * db_signal.quantity * 0.0003)
                    # 更新账户余额
                    self.account_service.update_balance(signal.profit, commission)
            
            db.commit()
            db.refresh(db_signal)
            
            # 如果状态从open变为closed，重新计算交易
            if original_status == 'open' and signal.status == 'closed':
                self.calc_trade(Signal(
                    id=db_signal.id,
                    date=db_signal.date,
                    symbol=db_signal.symbol,
                    type=db_signal.type,
                    price=db_signal.price,
                    quantity=db_signal.quantity,
                    status=db_signal.status,
                    reason=db_signal.reason,
                    close_date=db_signal.close_date,
                    close_price=db_signal.close_price,
                    profit=db_signal.profit,
                    created_at=db_signal.created_at,
                    updated_at=db_signal.updated_at
                ))
            # 如果交易类型、价格或数量发生变化，重新计算
            elif (original_type != db_signal.type or 
                  original_price != db_signal.price or 
                  original_quantity != db_signal.quantity):
                self.calc_trade(Signal(
                    id=db_signal.id,
                    date=db_signal.date,
                    symbol=db_signal.symbol,
                    type=db_signal.type,
                    price=db_signal.price,
                    quantity=db_signal.quantity,
                    status=db_signal.status,
                    reason=db_signal.reason,
                    close_date=db_signal.close_date,
                    close_price=db_signal.close_price,
                    profit=db_signal.profit,
                    created_at=db_signal.created_at,
                    updated_at=db_signal.updated_at
                ))
            
            return Signal(
                id=db_signal.id,
                date=db_signal.date,
                symbol=db_signal.symbol,
                type=db_signal.type,
                price=db_signal.price,
                quantity=db_signal.quantity,
                status=db_signal.status,
                reason=db_signal.reason,
                close_date=db_signal.close_date,
                close_price=db_signal.close_price,
                profit=db_signal.profit,
                created_at=db_signal.created_at,
                updated_at=db_signal.updated_at
            )
        except Exception as e:
            self.logger.error(f"更新信号失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def delete_signal(self, signal_id: str) -> None:
        """删除信号"""
        try:
            db = self.SessionLocal()
            db_signal = db.query(SignalDB).filter(SignalDB.id == signal_id).first()
            if not db_signal:
                raise ValueError(f"信号不存在: {signal_id}")
            
            db.delete(db_signal)
            db.commit()
        except Exception as e:
            self.logger.error(f"删除信号失败: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()

    def generate_signals(self, start_date: datetime, end_date: datetime, signal_type: Optional[str] = None, page: int = 1, page_size: int = 10, klines: List[KLineData] = None) -> tuple[List[Signal], int]:
        """根据均线策略生成交易信号"""
        try:
            if not klines:
                return [], 0
                
            # 将K线数据转换为列表
            dates = []
            prices = []
            lows = []
            ema5s = []
            ema20s = []
            symbols = []
            for k in klines:
                dates.append(k.date)
                symbols.append(k.symbol)
                prices.append(k.close)
                lows.append(k.low)
                ema5s.append(k.ema5)
                ema20s.append(k.ema20)

            # 生成信号
            signals = []
            for i in range(len(prices)-1):
                if i < 20:  # 确保有足够的数据计算均线
                    continue
                    
                # 检查金叉条件
                if (ema5s[i] > ema20s[i] and  # 短期均线在长期均线上方
                    ema5s[i-1] <= ema20s[i-1] and  # 前一日短期均线在长期均线下方
                    ema20s[i] >= ema20s[i-1]):  # 长期均线平或上升
                    
                    # 计算前低作为止损点
                    stop_loss = min(lows[i-5:i])
                    
                    # 生成买入开仓信号
                    current_time = datetime.now()
                    signal = Signal(
                        id=str(uuid.uuid4()),
                        date=dates[i],
                        symbol=symbols[i],
                        type=SignalType.BUY_OPEN,
                        price=prices[i],
                        quantity=1,
                        status=SignalStatus.OPEN,
                        reason=f"金叉信号：短期均线上穿长期均线，止损价：{stop_loss:.2f}",
                        close_date=None,
                        close_price=None,
                        profit=0.0,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    signals.append(signal)
                
                # 检查平仓条件：价格跌破长期均线
                elif i > 0 and prices[i] < ema20s[i] and prices[i-1] >= ema20s[i-1]:
                    # 生成卖出平仓信号
                    current_time = datetime.now()
                    signal = Signal(
                        id=str(uuid.uuid4()),
                        date=dates[i],
                        symbol=symbols[i],
                        type=SignalType.SELL_CLOSE,
                        price=prices[i],
                        quantity=1,
                        status=SignalStatus.OPEN,
                        reason=f"平仓信号：价格跌破长期均线",
                        close_date=None,
                        close_price=None,
                        profit=0.0,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    signals.append(signal)

            # 返回最近的5个信号
            total = len(signals)
            # 按日期排序，确保返回最新的信号
            signals.sort(key=lambda x: x.date, reverse=True)
            # 只返回最近的5个信号
            return signals[:5], total

        except Exception as e:
            self.logger.error(f"生成信号失败: {str(e)}")
            return [], 0 