from flask import request, jsonify
from datetime import datetime
import logging
from ...database.connection import execute_query
from . import bp

@bp.route('/futures/basic', methods=['GET'])
def get_futures_basic():
    try:
        exchange = request.args.get('exchange')
        fut_type = request.args.get('futType')
        fut_code = request.args.get('futCode')
        
        query = '''
            SELECT ts_code, symbol, exchange, name, fut_code, multiplier,
                   trade_unit, per_unit, quote_unit, quote_unit_desc,
                   d_mode_desc, list_date, delist_date, d_month,
                   last_ddate, trade_time_desc
            FROM fut_basic
            WHERE 1=1
        '''
        params = []
        
        if exchange:
            query += ' AND exchange = ?'
            params.append(exchange)
        if fut_type:
            query += ' AND fut_type = ?'
            params.append(fut_type)
        if fut_code:
            query += ' AND fut_code = ?'
            params.append(fut_code)
            
        today = datetime.now().strftime('%Y%m%d')
        query += ' AND (delist_date IS NULL OR delist_date > ?)'
        params.append(today)
        
        query += ' ORDER BY ts_code'
            
        results = execute_query(query, params)
        
        cursor = execute_query(query, params, return_cursor=True)
        columns = [column[0] for column in cursor.description]
        
        formatted_results = []
        for row in results:
            formatted_row = dict(zip(columns, row))
            
            if formatted_row.get('list_date'):
                formatted_row['list_date'] = str(formatted_row['list_date'])
            if formatted_row.get('delist_date'):
                formatted_row['delist_date'] = str(formatted_row['delist_date'])
            if formatted_row.get('last_ddate'):
                formatted_row['last_ddate'] = str(formatted_row['last_ddate'])
            
            formatted_results.append(formatted_row)
        
        return jsonify({
            'success': True,
            'data': formatted_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/futures/<ts_code>/daily', methods=['GET'])
def get_futures_daily(ts_code):
    try:
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        trade_date = request.args.get('tradeDate')
        
        query = '''
            SELECT ts_code, trade_date, pre_close, pre_settle, open,
                   high, low, close, settle, change1, change2,
                   vol as volume, amount, oi as open_interest, oi_chg,
                   delv_settle
            FROM fut_daily
            WHERE ts_code = ?
        '''
        params = [ts_code]
        
        if trade_date:
            query += ' AND trade_date = ?'
            params.append(trade_date)
        else:
            if start_date:
                query += ' AND trade_date >= ?'
                params.append(start_date[:10])  # Extract YYYY-MM-DD
            if end_date:
                query += ' AND trade_date <= ?'
                params.append(end_date[:10])
                
        query += ' ORDER BY trade_date DESC'
        
        results = execute_query(query, params)
        
        # 格式化日期字段
        formatted_results = []
        for row in results:
            formatted_row = dict(row)
            if formatted_row.get('trade_date'):
                formatted_row['trade_date'] = str(formatted_row['trade_date'])
            formatted_results.append(formatted_row)
        
        return jsonify({
            'success': True,
            'data': formatted_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/futures/<ts_code>/minutes', methods=['GET'])
def get_futures_minutes(ts_code):
    try:
        freq = request.args.get('freq', '1min')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        query = '''
            SELECT ts_code, trade_time, open, close, high,
                   low, vol, amount, oi
            FROM fut_mins
            WHERE ts_code = ?
        '''
        params = [ts_code]
        
        if start_date:
            query += ' AND trade_time >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND trade_time <= ?'
            params.append(end_date)
            
        query += ' ORDER BY trade_time'
        
        results = execute_query(query, params)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/futures/mapping', methods=['GET'])
def get_futures_mapping():
    try:
        ts_code = request.args.get('tsCode')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        trade_date = request.args.get('tradeDate')
        
        query = '''
            SELECT ts_code, trade_date, mapping_ts_code
            FROM fut_mapping
            WHERE 1=1
        '''
        params = []
        
        if ts_code:
            query += ' AND ts_code = ?'
            params.append(ts_code)
        if trade_date:
            query += ' AND trade_date = ?'
            params.append(trade_date)
        else:
            if start_date:
                query += ' AND trade_date >= ?'
                params.append(start_date[:10])
            if end_date:
                query += ' AND trade_date <= ?'
                params.append(end_date[:10])
                
        query += ' ORDER BY trade_date'
        
        results = execute_query(query, params)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/futures/categories', methods=['GET'])
def get_futures_categories():
    """
    获取按交易所和品种分类的期货合约列表，只返回在fut_daily表中有交易数据的合约
    """
    logger = logging.getLogger(__name__)
    logger.info("Fetching futures categories")
    
    try:
        query = '''
            SELECT DISTINCT b.ts_code, b.name, b.exchange, b.fut_code
            FROM fut_basic b
            INNER JOIN fut_daily d ON b.ts_code = d.ts_code
            WHERE (b.delist_date IS NULL OR b.delist_date > 20240101)
            ORDER BY b.ts_code
        '''
        
        today = datetime.now().strftime('%Y%m%d')
        logger.info(f"Executing query with today's date: {today}")
        
        # 在一次调用中获取所有数据
        results = execute_query(query)
        logger.info(f"Query returned {len(results)} results")
        
        # 按交易所和品种分类
        categorized = {}
        for row in results:
            # 假设列的顺序是: ts_code, name, exchange, fut_code
            ts_code, name, exchange, fut_code = row
            
            if exchange not in categorized:
                categorized[exchange] = {}
                logger.info(f"Created new exchange category: {exchange}")
                
            if fut_code not in categorized[exchange]:
                categorized[exchange][fut_code] = []
                logger.info(f"Created new futures code category: {fut_code} under {exchange}")
                
            categorized[exchange][fut_code].append({
                'code': ts_code,
                'name': name,
                'fut_code': fut_code
            })
            
        logger.info(f"Successfully categorized {len(results)} futures contracts")
        return jsonify({
            'success': True,
            'data': categorized
        })
        
    except Exception as e:
        logger.error(f"Error fetching futures categories: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 