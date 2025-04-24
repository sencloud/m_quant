from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import logging
from config import settings
from utils.logger import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.soybean import SoybeanImportDB, SoybeanImport, PortDetail, CustomsDetail
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

    def get_soybean_import_data(self) -> Dict[str, Any]:
        """获取大豆进口数据
        
        Returns:
            大豆进口数据
        """
        try:
            db = self.SessionLocal()
            
            # 从数据库获取最新数据
            data = db.query(SoybeanImportDB).order_by(SoybeanImportDB.date.desc()).first()
            if not data:
                return {
                    "current_shipment": 0.0,
                    "current_shipment_yoy": 0.0,
                    "forecast_shipment": 0.0,
                    "forecast_shipment_yoy": 0.0,
                    "current_arrival": 0.0,
                    "current_arrival_yoy": 0.0,
                    "next_arrival": 0.0,
                    "next_arrival_yoy": 0.0,
                    "monthly_comparison": [],
                    "port_distribution": [],
                    "port_details": [],
                    "customs_details": []
                }
            
            # 计算同比数据
            prev_year_data = db.query(SoybeanImportDB).filter(
                SoybeanImportDB.date == data.date - timedelta(days=365)
            ).first()
            
            current_shipment_yoy = 0.0
            forecast_shipment_yoy = 0.0
            current_arrival_yoy = 0.0
            next_arrival_yoy = 0.0
            
            if prev_year_data:
                current_shipment_yoy = (data.current_shipment - prev_year_data.current_shipment) / prev_year_data.current_shipment * 100
                forecast_shipment_yoy = (data.forecast_shipment - prev_year_data.forecast_shipment) / prev_year_data.forecast_shipment * 100
                current_arrival_yoy = (data.current_arrival - prev_year_data.current_arrival) / prev_year_data.current_arrival * 100
                next_arrival_yoy = (data.next_arrival - prev_year_data.next_arrival) / prev_year_data.next_arrival * 100
            
            # 构建月度对比数据
            monthly_comparison = [
                {"month": data.date.strftime('%Y-%m'), "value": data.current_shipment, "type": "actual"},
                {"month": data.date.strftime('%Y-%m'), "value": data.forecast_shipment, "type": "forecast"}
            ]
            
            # 构建港口分布数据
            port_distribution = [
                {"port": detail["port"], "value": float(detail["current"]), "type": "current"}
                for detail in data.port_details
            ]
            
            # 直接使用数据库中的JSON数据
            port_details = [PortDetail(**detail) for detail in data.port_details]
            customs_details = [CustomsDetail(**detail) for detail in data.customs_details]
            
            result = {
                "current_shipment": data.current_shipment,
                "current_shipment_yoy": current_shipment_yoy,
                "forecast_shipment": data.forecast_shipment,
                "forecast_shipment_yoy": forecast_shipment_yoy,
                "current_arrival": data.current_arrival,
                "current_arrival_yoy": current_arrival_yoy,
                "next_arrival": data.next_arrival,
                "next_arrival_yoy": next_arrival_yoy,
                "monthly_comparison": monthly_comparison,
                "port_distribution": port_distribution,
                "port_details": port_details,
                "customs_details": customs_details
            }
            
            logger.info(f"成功获取大豆进口数据")
            return result
            
        except Exception as e:
            logger.error(f"获取大豆进口数据失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "current_shipment": 0.0,
                "current_shipment_yoy": 0.0,
                "forecast_shipment": 0.0,
                "forecast_shipment_yoy": 0.0,
                "current_arrival": 0.0,
                "current_arrival_yoy": 0.0,
                "next_arrival": 0.0,
                "next_arrival_yoy": 0.0,
                "monthly_comparison": [],
                "port_distribution": [],
                "port_details": [],
                "customs_details": []
            }
        finally:
            if 'db' in locals():
                db.close() 