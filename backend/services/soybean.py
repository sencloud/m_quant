from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from config import settings
from utils.logger import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.soybean import (
    SoybeanImportDB, SoybeanImport, PortDetail, CustomsDetail,
    ComparisonData, PortDistributionData
)

class SoybeanService:
    """大豆进口数据服务"""
    
    def __init__(self):
        """初始化大豆进口数据服务"""
        try:
            # 初始化数据库连接
            self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("大豆进口数据库连接初始化完成")
        except Exception as e:
            logger.error(f"大豆进口数据服务初始化失败: {e}")
            self.engine = None
            self.SessionLocal = None

    def _calculate_yoy(self, current: float, previous: float) -> float:
        """计算同比增长率"""
        if previous == 0:
            return 0.0
        return (current - previous) / previous * 100

    def _calculate_mom(self, current: float, previous: float) -> float:
        """计算环比增长率"""
        if previous == 0:
            return 0.0
        return (current - previous) / previous * 100

    def get_soybean_import_data(self) -> SoybeanImport:
        """获取大豆进口数据"""
        db = None
        try:
            db = self.SessionLocal()
            
            # 获取最新数据
            current_data = db.query(SoybeanImportDB).order_by(SoybeanImportDB.date.desc()).first()
            if not current_data:
                logger.warning("未找到大豆进口数据")
                return SoybeanImport(
                    date=datetime.now().strftime("%Y-%m-%d"),
                    current_shipment=0.0,
                    forecast_shipment=0.0,
                    forecast_next_shipment=0.0,
                    current_arrival=0.0,
                    next_arrival=0.0,
                    current_month_arrival=0.0,
                    next_month_arrival=0.0,
                    port_details=[],
                    customs_details=[]
                )
            
            # 获取去年同期数据
            last_year_date = current_data.date - timedelta(days=365)
            prev_year_data = db.query(SoybeanImportDB).filter(
                SoybeanImportDB.date >= last_year_date,
                SoybeanImportDB.date < last_year_date + timedelta(days=7)
            ).first()
            
            # 获取上月数据
            last_month_date = current_data.date - timedelta(days=30)
            prev_month_data = db.query(SoybeanImportDB).filter(
                SoybeanImportDB.date >= last_month_date,
                SoybeanImportDB.date < last_month_date + timedelta(days=7)
            ).first()
            
            # 构建月度对比数据
            monthly_comparison: List[ComparisonData] = []
            try:
                # 获取当年所有月份数据
                current_year = current_data.date.year
                year_data = db.query(SoybeanImportDB).filter(
                    SoybeanImportDB.date >= datetime(current_year, 1, 1),
                    SoybeanImportDB.date <= datetime(current_year, 12, 31)
                ).order_by(SoybeanImportDB.date.asc()).all()
                
                for data in year_data:
                    # 实际装船量
                    monthly_comparison.append(
                        ComparisonData(
                            month=data.date.strftime('%Y-%m'),
                            value=data.current_shipment,
                            type="实际装船量"
                        )
                    )
                    # 预测装船量
                    monthly_comparison.append(
                        ComparisonData(
                            month=data.date.strftime('%Y-%m'),
                            value=data.forecast_shipment,
                            type="预报装船量"
                        )
                    )
                    # 实际到港量
                    monthly_comparison.append(
                        ComparisonData(
                            month=data.date.strftime('%Y-%m'),
                            value=data.current_arrival,
                            type="实际到港量"
                        )
                    )
                    # 预测到港量
                    monthly_comparison.append(
                        ComparisonData(
                            month=data.date.strftime('%Y-%m'),
                            value=data.next_arrival,
                            type="预报到港量"
                        )
                    )
            except Exception as e:
                logger.error(f"构建月度对比数据失败: {e}")
                monthly_comparison = []

            # 构建基础响应对象
            result = SoybeanImport(
                date=current_data.date.strftime("%Y-%m-%d"),
                # 装船数据
                current_shipment=current_data.current_shipment,
                forecast_shipment=current_data.forecast_shipment,
                forecast_next_shipment=current_data.forecast_next_shipment,
                
                # 到港数据
                current_arrival=current_data.current_arrival,
                next_arrival=current_data.next_arrival,
                current_month_arrival=current_data.current_month_arrival,
                next_month_arrival=current_data.next_month_arrival,
                
                # 预期差异
                shipment_forecast_diff=current_data.current_shipment - current_data.forecast_shipment,
                arrival_forecast_diff=current_data.current_month_arrival - current_data.next_arrival,
                
                # 图表数据
                monthly_comparison=monthly_comparison,
                port_distribution=[
                    PortDistributionData(
                        port=detail["port"],
                        value=float(detail["current"]),
                        type="current"
                    )
                    for detail in current_data.port_details
                ],
                
                # 详细数据
                port_details=[PortDetail(**detail) for detail in current_data.port_details],
                customs_details=[CustomsDetail(**detail) for detail in current_data.customs_details],
                created_at=current_data.created_at,
                updated_at=current_data.updated_at
            )
            
            # 计算同比数据
            if prev_year_data:
                result.current_shipment_yoy = self._calculate_yoy(
                    current_data.current_shipment, 
                    prev_year_data.current_shipment
                )
                result.forecast_shipment_yoy = self._calculate_yoy(
                    current_data.forecast_shipment,
                    prev_year_data.forecast_shipment
                )
                result.current_arrival_yoy = self._calculate_yoy(
                    current_data.current_arrival,
                    prev_year_data.current_arrival
                )
                result.next_arrival_yoy = self._calculate_yoy(
                    current_data.next_arrival,
                    prev_year_data.next_arrival
                )
            
            # 计算环比数据
            if prev_month_data:
                result.current_shipment_mom = self._calculate_mom(
                    current_data.current_shipment,
                    prev_month_data.current_shipment
                )
                result.forecast_shipment_mom = self._calculate_mom(
                    current_data.forecast_shipment,
                    prev_month_data.forecast_shipment
                )
                result.current_arrival_mom = self._calculate_mom(
                    current_data.current_arrival,
                    prev_month_data.current_arrival
                )
            
            logger.info(f"成功获取大豆进口数据，当前日期：{current_data.date}")
            return result
            
        except Exception as e:
            logger.error(f"获取大豆进口数据失败: {e}")
            raise
        finally:
            if db:
                try:
                    db.close()
                except Exception as e:
                    logger.error(f"关闭数据库连接失败: {e}")

    def get_monthly_comparison(self) -> List[ComparisonData]:
        """获取月度对比数据"""
        db = None
        try:
            db = self.SessionLocal()
            comparison_data = []

            # 获取当前月份数据
            current_date = datetime.now()
            first_day = current_date.replace(day=1)
            
            current_data = db.query(SoybeanImportDB)\
                .filter(SoybeanImportDB.date >= first_day)\
                .order_by(SoybeanImportDB.date.desc())\
                .first()
            
            if current_data:
                comparison_data.append(
                    ComparisonData(
                        month=current_data.date.strftime('%Y-%m'),
                        value=current_data.current_shipment,
                        type="实际装船量"
                    )
                )

            # 获取预测到港数据
            next_month = current_date.replace(day=1) + timedelta(days=32)
            next_month_start = next_month.replace(day=1)
            
            forecast_data = db.query(SoybeanImportDB)\
                .filter(SoybeanImportDB.date >= next_month_start)\
                .order_by(SoybeanImportDB.date.asc())\
                .first()
            
            if forecast_data:
                comparison_data.append(
                    ComparisonData(
                        month=forecast_data.date.strftime('%Y-%m'),
                        value=forecast_data.forecast_arrival,
                        type="预报到港量"
                    )
                )

            # 获取同比数据
            last_year = current_date.year - 1
            yoy_data = db.query(SoybeanImportDB)\
                .filter(
                    SoybeanImportDB.date.between(
                        datetime(last_year, 1, 1),
                        datetime(last_year, 12, 31)
                    )
                )\
                .order_by(SoybeanImportDB.date.asc())\
                .all()
            
            for data in yoy_data:
                comparison_data.append(
                    ComparisonData(
                        month=data.date.strftime('%Y-%m'),
                        value=data.current_shipment,
                        type="实际装船量"
                    )
                )

            return comparison_data

        except Exception as e:
            logger.error(f"获取月度对比数据失败: {str(e)}")
            return []
        finally:
            if db:
                try:
                    db.close()
                except Exception as e:
                    logger.error(f"关闭数据库连接失败: {str(e)}") 