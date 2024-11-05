from flask import Blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

from . import stock_routes, backtest_routes, trade_routes, futures_routes