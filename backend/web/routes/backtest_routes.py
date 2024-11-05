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
        required_fields = ['strategy', 'stock', 'startDate', 'endDate']
        if not all(field in request_data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in request_data]
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # 验证日期
        try:
            start_date = datetime.strptime(request_data['startDate'], '%Y-%m-%d')
            end_date = datetime.strptime(request_data['endDate'], '%Y-%m-%d')
            if start_date > end_date:
                return jsonify({'error': 'Start date must be before end date'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # 运行回测
        results = BacktestService.run_backtest(request_data)
        
        if not results:
            return jsonify({'error': 'Backtest did not produce any results'}), 500
            
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 