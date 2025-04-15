from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FlashNews(BaseModel):
    """快讯数据模型"""
    id: Optional[int] = None
    datetime: datetime
    content: str
    analysis: Optional[str] = None
    remarks: Optional[str] = None

class NewsArticle(BaseModel):
    """资讯数据模型"""
    id: Optional[int] = None
    datetime: datetime
    title: str
    content: str
    analysis: Optional[str] = None
    remarks: Optional[str] = None 