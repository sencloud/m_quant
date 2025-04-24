from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime
from services.soybean import SoybeanService

router = APIRouter()

class PortData(BaseModel):
    port: str
    current: float
    next_month: float
    next_two_month: float

class CustomsData(BaseModel):
    customs: str
    current: float
    next_period: float
    next_month: float
    next_two_month: float

class ComparisonData(BaseModel):
    month: str
    value: float
    type: str

class PortDistributionData(BaseModel):
    port: str
    value: float
    type: str

class SoybeanImportData(BaseModel):
    current_shipment: float
    current_shipment_yoy: float
    forecast_shipment: float
    forecast_shipment_yoy: float
    current_arrival: float
    current_arrival_yoy: float
    next_arrival: float
    next_arrival_yoy: float
    monthly_comparison: List[ComparisonData]
    port_distribution: List[PortDistributionData]
    port_details: List[PortData]
    customs_details: List[CustomsData]

@router.get("/import", response_model=SoybeanImportData)
def get_soybean_import_data():
    try:
        service = SoybeanService()
        return service.get_soybean_import_data()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 