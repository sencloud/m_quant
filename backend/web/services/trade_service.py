from datetime import datetime
from backend.database.connection import execute_query
import logging

logger = logging.getLogger(__name__)

class TradeService:
    @staticmethod
    def store_trade_request(trade_request):
        """存储交易请求并返回ID"""
        query = '''
            INSERT INTO trade_requests 
            (symbol, action, quantity, strategy, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING id
        '''
        result = execute_query(
            query,
            (
                trade_request['symbol'],
                trade_request['action'],
                trade_request['quantity'],
                trade_request['strategy'],
                'pending',
                datetime.now().isoformat()
            )
        )
        return result[0][0] if result else None

    @staticmethod
    def update_trade_status(trade_id, status, error_message=None):
        """更新交易请求状态"""
        query = '''
            UPDATE trade_requests 
            SET status = ?, 
                executed_at = CASE WHEN ? IN ('completed', 'failed') 
                            THEN datetime('now') ELSE executed_at END,
                error_message = ?
            WHERE id = ?
        '''
        execute_query(query, (status, status, error_message, trade_id))

    @staticmethod
    def get_trade_status(trade_id):
        """获取交易状态"""
        query = '''
            SELECT id, symbol, action, quantity, strategy, status, 
                   timestamp, executed_at, error_message
            FROM trade_requests
            WHERE id = ?
        '''
        result = execute_query(query, (trade_id,))
        
        if not result:
            return None
            
        trade = result[0]
        return {
            'id': trade[0],
            'symbol': trade[1],
            'action': trade[2],
            'quantity': trade[3],
            'strategy': trade[4],
            'status': trade[5],
            'timestamp': trade[6],
            'executed_at': trade[7],
            'error_message': trade[8]
        }