from flask import jsonify, request
from . import bp
from ..services.backtest_service import BacktestService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@bp.route('/backtest', methods=['POST'])
def run_backtest():
    """运行回测"""
    try:
        request_data = request.get_json()
        logger.info(f"Received backtest request: {request_data}")
        
        # 验证必需参数
        required_fields = ['strategy', 'startDate', 'endDate']
        if not all(field in request_data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in request_data]
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # 验证至少有一个交易品种被选择
        if not request_data.get('stock') and not request_data.get('futures'):
            return jsonify({'error': 'At least one of stock or futures must be selected'}), 400
        
        # 验证日期
        try:
            start_date = datetime.strptime(request_data['startDate'], '%Y-%m-%d')
            end_date = datetime.strptime(request_data['endDate'], '%Y-%m-%d')
            if start_date > end_date:
                return jsonify({'error': 'Start date must be before end date'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # 运行回测
        if request_data.get('stock'):
            symbol = request_data['stock']
            symbol_type = 'stock'
        else:
            symbol = request_data['futures']
            symbol_type = 'futures'
            
        results = BacktestService.run_backtest({
            'strategy': request_data['strategy'],
            'symbol': symbol,
            'symbol_type': symbol_type,
            'startDate': request_data['startDate'],
            'endDate': request_data['endDate']
        })
        
        if not results:
            return jsonify({'error': 'Backtest did not produce any results'}), 500
            
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 