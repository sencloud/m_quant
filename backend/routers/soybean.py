from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from services.soybean import SoybeanService
from models.soybean import SoybeanImport
from utils.logger import logger

router = APIRouter()

def get_soybean_service() -> SoybeanService:
    logger.debug("创建大豆进口数据服务实例")
    return SoybeanService()

@router.get("/import", response_model=SoybeanImport)
async def get_soybean_import_data(
    service: SoybeanService = Depends(get_soybean_service)
):
    """获取大豆进口数据"""
    try:
        data = service.get_soybean_import_data()
        if not data:
            raise HTTPException(status_code=404, detail="未找到大豆进口数据")
        return data
    except Exception as e:
        logger.error(f"获取大豆进口数据失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 