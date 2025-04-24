from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import logging
from config import settings
from utils.logger import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.soybean import (
    SoybeanImportDB, SoybeanImport, PortDetail, CustomsDetail,
    ComparisonData, PortDistributionData
)
import json

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
        try:
            db = self.SessionLocal()
            
            # 获取最新数据
            current_data = db.query(SoybeanImportDB).order_by(SoybeanImportDB.date.desc()).first()
            print(current_data.date)
            if not current_data:
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
            prev_year_data = db.query(SoybeanImportDB).filter(
                SoybeanImportDB.date == current_data.date - timedelta(days=365)
            ).first()
            print(prev_year_data.date)
            
            # 获取上月数据
            prev_month_data = db.query(SoybeanImportDB).filter(
                SoybeanImportDB.date < current_data.date
            ).order_by(SoybeanImportDB.date.desc()).first()
            print(prev_month_data.date)
            
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
                
                # 同环比数据 - 初始化为0
                current_shipment_yoy=0.0,
                current_shipment_mom=0.0,
                forecast_shipment_yoy=0.0,
                forecast_shipment_mom=0.0,
                current_arrival_yoy=0.0,
                current_arrival_mom=0.0,
                next_arrival_yoy=0.0,
                
                # 预期差异 - 初始化为0
                shipment_forecast_diff=0.0,
                arrival_forecast_diff=0.0,
                
                # 图表数据
                monthly_comparison=[
                    ComparisonData(
                        month=current_data.date.strftime('%Y-%m'),
                        value=current_data.current_shipment,
                        type="actual"
                    ),
                    ComparisonData(
                        month=current_data.date.strftime('%Y-%m'),
                        value=current_data.forecast_shipment,
                        type="forecast"
                    )
                ],
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
            
            # 计算预期差异
            result.shipment_forecast_diff = current_data.current_shipment - current_data.forecast_shipment
            result.arrival_forecast_diff = current_data.current_month_arrival - current_data.next_arrival
            
            logger.info("成功获取大豆进口数据")
            return result
            
        except Exception as e:
            logger.error(f"获取大豆进口数据失败: {e}")
            import traceback
            traceback.print_exc()
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
        finally:
            if 'db' in locals():
                db.close() 