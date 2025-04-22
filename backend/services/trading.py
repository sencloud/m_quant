from sqlalchemy import create_engine, Column, String, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Optional
from models.trading import DailyStrategyAnalysis
from config import settings
from utils.logger import logger
import pandas as pd
import tushare as ts

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
        # 初始化tushare API
        try:
            token = settings.TUSHARE_TOKEN
            if not token:
                self.logger.error("未找到 TUSHARE_TOKEN，请在 .env 文件中设置")
                self.pro = None
            else:
                ts.set_token(token)
                self.pro = ts.pro_api()
                self.logger.debug("Tushare API初始化完成")
        except Exception as e:
            self.logger.error(f"Tushare API初始化失败: {str(e)}")
            self.pro = None

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

    def get_trading_data(self) -> dict:
        """获取豆粕期货交易相关的实时数据"""
        try:
            # 获取当前主力合约
            # 获取最近的交易日
            trade_cal = self._call_tushare_api(
                self.pro.trade_cal,
                exchange='DCE',
                is_open='1',
                start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d')
            )
            if trade_cal is None or trade_cal.empty:
                self.logger.warning(f"未找到最近的交易日")
                return {}
            
            # 按日期降序排序，从最近的交易日开始查找
            trade_cal = trade_cal.sort_values('cal_date', ascending=False)
            
            # 尝试查找最近5个交易日的主力合约
            main_contract = None
            latest_trade_date = None
            
            for _, row in trade_cal.head(5).iterrows():
                current_date = row['cal_date']
                self.logger.info(f"尝试获取{current_date}的主力合约")
                
                temp_main_contract = self._call_tushare_api(
                    self.pro.fut_mapping,
                    ts_code="M.DCE",
                    trade_date=current_date
                )
                
                if temp_main_contract is not None and not temp_main_contract.empty:
                    main_contract = temp_main_contract.iloc[0]['mapping_ts_code'].split('.')[0]  # 去掉.DCE后缀
                    latest_trade_date = current_date
                    self.logger.info(f"在{current_date}找到主力合约: {main_contract}")
                    break
                else:
                    self.logger.warning(f"在{current_date}未找到主力合约")
            
            if main_contract is None:
                self.logger.warning(f"在最近5个交易日未找到主力合约")
                return {}
            
            # 获取当前日期和下一个交易日
            today = datetime.now()
            next_day = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # 获取主力合约的日线数据
            df_daily = self._call_tushare_api(
                self.pro.fut_daily,
                ts_code=f"{main_contract}.DCE",
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),  # 获取近30天数据用于计算指标
                end_date=latest_trade_date
            )
            
            if df_daily is None or df_daily.empty:
                self.logger.warning(f"未获取到{main_contract}的日线数据")
                return {}
            
            # 按日期排序
            df_daily = df_daily.sort_values('trade_date')
            
            # 获取最新价格数据
            latest_data = df_daily.iloc[-1]
            current_price = float(latest_data['close'])
            high_low = f"{latest_data['low']}-{latest_data['high']}"
            
            # 计算移动平均线
            df_daily['ma5'] = df_daily['close'].rolling(window=5).mean()
            df_daily['ma20'] = df_daily['close'].rolling(window=20).mean()
            ma5 = float(df_daily['ma5'].iloc[-1])
            ma20 = float(df_daily['ma20'].iloc[-1])
            
            # 计算支撑和阻力位
            recent_lows = df_daily['low'].tail(10)
            recent_highs = df_daily['high'].tail(10)
            low_support = float(recent_lows.mean())
            strong_support = float(recent_lows.min())
            high_resistance = float(recent_highs.mean())
            strong_resistance = float(recent_highs.max())
            
            # 计算MACD
            exp1 = df_daily['close'].ewm(span=12, adjust=False).mean()
            exp2 = df_daily['close'].ewm(span=26, adjust=False).mean()
            macd_diff = float(exp1.iloc[-1] - exp2.iloc[-1])
            macd_dea = float(df_daily['close'].ewm(span=9, adjust=False).mean().iloc[-1])
            
            # 计算RSI
            delta = df_daily['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = float(100 - (100 / (1 + rs)).iloc[-1])
            
            # 计算布林带
            std20 = df_daily['close'].rolling(window=20).std()
            upper_band = ma20 + 2 * std20
            lower_band = ma20 - 2 * std20
            
            # 判断布林带趋势
            bb_trend = "收口" if std20.iloc[-1] < std20.iloc[-2] else "扩张"
            
            # 获取量仓数据
            volume = int(latest_data['vol'])  # 成交量(手)
            
            # 获取上周同一天的数据用于计算周度变化
            last_week_date = (datetime.strptime(latest_trade_date, '%Y%m%d') - timedelta(days=7)).strftime('%Y%m%d')
            last_week_data = self._call_tushare_api(
                self.pro.fut_daily,
                ts_code=f"{main_contract}.DCE",
                start_date=last_week_date,
                end_date=last_week_date
            )
            
            # 计算周度持仓变化
            if last_week_data is not None and not last_week_data.empty:
                weekly_position_change = int(latest_data['oi'] - last_week_data.iloc[0]['oi'])  # 本周持仓量 - 上周持仓量
            else:
                weekly_position_change = 0
                logger.warning(f"未获取到上周持仓数据，使用默认值0")
            
            # 获取持仓数据
            # 尝试获取最新交易日的持仓数据
            oi_data = self._call_tushare_api(
                self.pro.fut_holding,
                symbol=f"{main_contract}", 
                exchange='DCE',
                trade_date=latest_trade_date
            )
            logger.info(f"持仓数据: {oi_data}")
            
            # 如果持仓数据为空，尝试获取前一交易日的数据
            if oi_data is None or oi_data.empty:
                # 获取前一交易日
                prev_trade_date = self._call_tushare_api(
                    self.pro.trade_cal,
                    exchange='DCE',
                    start_date=(datetime.strptime(latest_trade_date, '%Y%m%d') - timedelta(days=10)).strftime('%Y%m%d'),
                    end_date=latest_trade_date,
                    is_open=1
                )
                
                if prev_trade_date is not None and not prev_trade_date.empty:
                    prev_trade_date = prev_trade_date.sort_values('cal_date', ascending=False).iloc[1]['cal_date']
                    logger.info(f"尝试获取前一交易日({prev_trade_date})的持仓数据")
                    
                    oi_data = self._call_tushare_api(
                        self.pro.fut_holding,
                        symbol=f"{main_contract}", 
                        exchange='DCE',
                        trade_date=prev_trade_date
                    )
                    logger.info(f"前一交易日持仓数据: {oi_data}")
            
            # 计算净空持仓和多空变化
            if oi_data is not None and not oi_data.empty:
                # 计算前20席位的总持仓情况
                total_long = oi_data['long_hld'].sum()  # 总持买仓量
                total_short = oi_data['short_hld'].sum()  # 总持卖仓量
                net_position = total_long - total_short  # 正数为净多头，负数为净空头
                
                # 计算持仓变化
                long_position_change = int(oi_data['long_chg'].sum())  # 多头持仓变化
                short_position_change = int(oi_data['short_chg'].sum())  # 空头持仓变化
                
                # 确定主导方向
                if net_position > 0:
                    position_direction = "多"
                    net_position_abs = net_position
                else:
                    position_direction = "空"
                    net_position_abs = abs(net_position)
            else:
                position_direction = "多"
                net_position_abs = 0
                long_position_change = 0
                short_position_change = 0
            
            # 获取美元兑人民币汇率
            fx_data = self._call_tushare_api(
                self.pro.fx_daily,
                ts_code='USDCNH.FXCM',  # 使用离岸人民币汇率
                start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),  # 获取最近7天数据，确保能获取到最新汇率
                end_date=datetime.now().strftime('%Y%m%d')
            )
            
            if fx_data is not None and not fx_data.empty:
                # 打印列名以便调试
                self.logger.debug(f"汇率数据列名: {fx_data.columns.tolist()}")
                
                # 按日期排序并获取最新汇率
                fx_data = fx_data.sort_values('trade_date', ascending=False)
                
                # 使用买入收盘价作为汇率（也可以用卖出收盘价ask_close的平均值）
                if 'bid_close' in fx_data.columns:
                    usd_cny = float(fx_data.iloc[0]['bid_close'])
                    self.logger.info(f"获取到最新美元兑人民币汇率(买入价): {usd_cny}")
                elif 'ask_close' in fx_data.columns:
                    usd_cny = float(fx_data.iloc[0]['ask_close'])
                    self.logger.info(f"获取到最新美元兑人民币汇率(卖出价): {usd_cny}")
                else:
                    self.logger.warning("未找到bid_close或ask_close字段，可用列: " + ", ".join(fx_data.columns))
                    usd_cny = 7.15  # 使用默认值
            else:
                usd_cny = 7.15  # 如果获取失败，使用默认值
                self.logger.warning("获取汇率失败，使用默认值7.15")

            # 生成分析文本
            price_analysis = (
                f"当前价格形态 价格点位：{current_price}元/吨，日内波动区间{high_low}元，"
                f"5日均线{ma5:.1f}元，20日均线{ma20:.1f}元。 "
                f"关键位：下方支撑{low_support:.1f}元（日内低点）→ 强支撑{strong_support:.1f}元（趋势线）；"
                f"上方压力{high_resistance:.1f}元（日内高点）→ 强压力{strong_resistance:.1f}元（前高阻力）。"
            )

            technical_analysis = (
                f"技术信号： MACD（12,26,9）：DIFF {macd_diff}，DEA {macd_dea}，"
                f"{'红柱收敛' if macd_diff > 0 and macd_diff < macd_dea else '绿柱扩张'}，"
                f"{'短期动能减弱' if macd_diff < macd_dea else '短期动能增强'}。 "
                f"RSI(14)：{rsi:.1f}，"
                f"{'超买区间' if rsi > 70 else '超卖区间' if rsi < 30 else '中性区间'}，"
                f"{'有超买信号' if rsi > 70 else '有超卖信号' if rsi < 30 else '无超买/超卖信号'}。 "
                f"布林带：价格{'高于上轨' if current_price > upper_band.iloc[-1] else '低于下轨' if current_price < lower_band.iloc[-1] else '贴近中轨'}（{ma20:.1f}元），"
                f"{bb_trend}迹象，波动率{'下降' if bb_trend == '收口' else '上升'}。"
            )

            volume_analysis = (
                f"量仓数据 成交量：{volume:,}手"
                f"{'↑' if volume > df_daily['vol'].iloc[-2] else '↓'}（较前日{'放量' if volume > df_daily['vol'].iloc[-2] else '缩量'}），"
                f"但周度持仓{'增加' if weekly_position_change > 0 else '减少'}{abs(weekly_position_change):,}手，"
                f"市场{'分歧加剧' if abs(weekly_position_change) > 5000 else '趋于一致'}。 "
                f"主力持仓：前20席位净{position_direction}头{net_position_abs:,}手，"
                f"空头{'增仓' if short_position_change > 0 else '减仓'}（{abs(short_position_change):,}手），"
                f"多头{'增仓' if long_position_change > 0 else '减仓'}（{abs(long_position_change):,}手），"
                f"{'空头主导但边际转弱' if position_direction == '空' and short_position_change < 0 else '多头主导且持续增强' if position_direction == '多' and long_position_change > 0 else '市场处于均衡状态'}。"
            )

            return {
                "price_analysis": price_analysis,
                "technical_analysis": technical_analysis,
                "volume_analysis": volume_analysis,
                "raw_data": {
                    "main_contract": main_contract,
                    "next_day": next_day,
                    "current_price": current_price,
                    "ma5": ma5,
                    "ma20": ma20,
                    "macd_diff": macd_diff,
                    "macd_dea": macd_dea,
                    "rsi": rsi,
                    "volume": volume,
                    "weekly_position_change": weekly_position_change,
                    "net_position": net_position_abs,
                    "position_direction": position_direction,
                    "short_position_change": short_position_change,
                    "long_position_change": long_position_change,
                    "usd_cny": usd_cny
                }
            }
        except Exception as e:
            self.logger.error(f"获取交易数据失败: {str(e)}")
            raise

    def _call_tushare_api(self, api_func, **kwargs):
        """调用tushare API的辅助方法"""
        try:
            return api_func(**kwargs)
        except Exception as e:
            self.logger.error(f"调用tushare API失败: {str(e)}")
            raise 