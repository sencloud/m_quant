from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from services.soybean import SoybeanService
from models.soybean import SoybeanImport

router = APIRouter()

@router.get("/import", response_model=SoybeanImport)
def get_soybean_import_data():
    try:
        service = SoybeanService()
        return service.get_soybean_import_data()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 