from flask import jsonify, request, abort
from . import bp
from ..services.trade_service import TradeService
from ..utils.ctp_manager import trade_queue
import logging

logger = logging.getLogger(__name__)

@bp.route('/webhook/tradingview', methods=['POST'])
def tradingview_webhook():
    """处理来自TradingView的webhook请求"""
    try:
        if not request.is_json:
            logger.error("Received non-JSON request to TradingView webhook")
            abort(400, description="Content-Type must be application/json")

        alert_data = request.get_json()
        logger.info(f"Received TradingView alert: {alert_data}")

        # 验证必需字段
        required_fields = ['symbol', 'strategy', 'action', 'quantity']
        if not all(field in alert_data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in alert_data]
            logger.error(f"Missing required fields in TradingView alert: {missing_fields}")
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # 存储交易请求并获取ID
        trade_id = TradeService.store_trade_request(alert_data)
        
        # 添加到处理队列
        trade_queue.put({
            'id': trade_id,
            **alert_data
        })

        return jsonify({
            'status': 'success',
            'message': "Trade request queued successfully",
            'trade_id': trade_id
        }), 200

    except Exception as e:
        logger.error(f"Error processing TradingView webhook: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/trades/<int:trade_id>', methods=['GET'])
def get_trade_status(trade_id):
    """获取交易状态"""
    try:
        trade = TradeService.get_trade_status(trade_id)
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
            
        return jsonify(trade)
    except Exception as e:
        logger.error(f"Error getting trade status: {e}")
        return jsonify({'error': str(e)}), 500 