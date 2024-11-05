from flask import Blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# 导入所有路由
from .routes import stock_routes, backtest_routes, trade_routes, futures_routes

# 初始化CTP管理器
# from .utils.ctp_manager import CTPManager
# ctp_manager = CTPManager()
# ctp_manager.start()

@bp.before_app_shutdown
def cleanup():
    pass
    # if ctp_manager:
    #     ctp_manager.stop()

