from fastapi import APIRouter, Depends
from services.account import AccountService
from models.account import Account

router = APIRouter()

@router.get("/account", response_model=Account)
async def get_account():
    """获取账户信息"""
    account_service = AccountService()
    return account_service.get_account() 