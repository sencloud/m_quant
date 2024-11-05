from flask import jsonify, request
from datetime import datetime, timedelta
from . import bp
from ..services.stock_service import StockService
import logging
import tushare as ts
from urllib.parse import unquote
from backend.data.process_data import ProcessData
from backend.ai.models.ml_models import MLModels
import torch
import numpy as np
import pandas as pd
import os

logger = logging.getLogger(__name__)

# 初始化 tushare
ts.set_token('')
pro = ts.pro_api()

# 定义模型保存路径
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

@bp.route('/stocks', methods=['GET'])
def get_stocks():
    """Get list of available stocks with names, exchange, and industry"""
    try:
        grouped_stocks = StockService.get_grouped_stocks()
        return jsonify(grouped_stocks)
    except Exception as e:
        logger.error(f"Error fetching stocks list: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/stocks/<code>', methods=['GET'])
def get_stock_data(code):
    """获取特定股票的详细数据"""
    try:
        granularity = request.args.get('granularity', 'day')
        start_date = unquote(request.args.get('startDate', ''))
        end_date = unquote(request.args.get('endDate', ''))

        logger.info(f"Received request for stock {code} with params: granularity={granularity}, start_date={start_date}, end_date={end_date}")

        if not (start_date and end_date):
            logger.error("Start date and end date are required")
            return jsonify({'error': 'Start date and end date are required'}), 400

        # 根据粒度获取数据
        if granularity == 'day':
            data = StockService.get_daily_data(code, start_date, end_date)
        else:
            data = StockService.get_intraday_data(code, granularity, start_date, end_date)

        if not data:
            return jsonify([])  # 如果没有数据，返回空列表

        return jsonify(data)

    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/stocks/available', methods=['GET'])
def get_available_stocks():
    """获取可用股票列表"""
    try:
        stocks = StockService.get_available_stocks()
        return jsonify(stocks)
    except Exception as e:
        logger.error(f"Error fetching available stocks: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/stocks/sync', methods=['POST'])
def sync_stock_data():
    """同步股票数据"""
    try:
        data = request.get_json()
        ts_code = data.get('ts_code')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        if not all([ts_code, start_date, end_date]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # 从TuShare获取数据并保存
        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', '')
        )
        
        if df.empty:
            return jsonify({'message': 'No data available for the specified period'}), 200
            
        ProcessData.save_stock_data(ts_code, df)
        return jsonify({'message': 'Data synchronized successfully'})
        
    except Exception as e:
        logger.error(f"Error syncing stock data: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
        
@bp.route('/stock/train', methods=['POST'])
def train_stock():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        models = data.get('models', [])
        time_period = data.get('timePeriod', 30)
        prediction_date = data.get('predictionDate')
        
        if not symbol or not models:
            return jsonify({
                'status': 'error',
                'message': 'Symbol and models are required'
            }), 400
            
        # 计算训练数据的日期范围
        end_date = datetime.strptime(prediction_date, '%Y-%m-%d')
        start_date = end_date - timedelta(days=time_period + 50)  # 多获取50天用于计算指标
        
        # 获取股票数据并计算技术指标
        logger.info(f"Fetching and processing stock data for {symbol}, start_date={start_date}, end_date={end_date}")
        stock_data = ProcessData.get_stock_data(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            is_training=True
        )
        
        if stock_data is None or stock_data.empty:
            return jsonify({
                'status': 'error',
                'message': 'No data available for the specified stock'
            }), 404
            
        # 验证所需的特征
        required_features = [
            'SMA_5', 'SMA_20', 'EMA_5', 'EMA_20',
            'Returns', 'Momentum', 'Volatility',
            'Volume_MA_5', 'Volume_MA_20'
        ]
        
        missing_features = [f for f in required_features if f not in stock_data.columns]
        if missing_features:
            return jsonify({
                'status': 'error',
                'message': f'Missing required features: {missing_features}'
            }), 400
            
        # 初始化模型
        ml_models = MLModels()
        
        # 准备特征
        feature_columns = [
            'SMA_5', 'SMA_20', 'EMA_5', 'EMA_20',
            'Returns', 'Momentum', 'Volatility',
            'Volume_MA_5', 'Volume_MA_20'
        ]
        
        # 准备训练数据
        train_loader, test_loader, X_test, y_test = ml_models.prepare_data(
            stock_data,
            'Target_5d',
            feature_columns
        )
        
        # 存储模型结果
        model_results = {}
        
        for model_type in models:
            # 训练模型
            metrics = ml_models.train_model(
                model_type,
                train_loader,
                test_loader,
                X_test,
                y_test
            )
            model_results[model_type] = metrics
            
            # 修改保存路径
            model_path = os.path.join(MODEL_DIR, f"{symbol}_{model_type}.pth")
            logger.info(f"Saving model to {model_path}")
            ml_models.save_model(model_type, model_path)
        
        return jsonify({
            'status': 'success',
            'model_metrics': model_results
        })
        
    except Exception as e:
        logger.error(f"Error in stock training: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/stock/predict', methods=['POST'])
def predict_stock():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        models = data.get('models', [])
        prediction_date = data.get('predictionDate')
        
        if not symbol or not models:
            return jsonify({
                'status': 'error',
                'message': 'Symbol and models are required'
            }), 400
            
        # 修改日期范围计算
        end_date = datetime.strptime(prediction_date, '%Y-%m-%d')
        # 获取预测日期前50天的数据用于计算特征
        start_date = end_date - timedelta(days=60)
        
        # 获取股票数据并计算技术指标
        stock_data = ProcessData.get_stock_data(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            is_training=False
        )
        
        if stock_data is None or stock_data.empty:
            return jsonify({
                'status': 'error',
                'message': 'No data available for the specified stock'
            }), 404
            
        # 准备特征
        feature_columns = [
            'SMA_5', 'SMA_20', 'EMA_5', 'EMA_20',
            'Returns', 'Momentum', 'Volatility',
            'Volume_MA_5', 'Volume_MA_20'
        ]
        
        # 初始化模型
        ml_models = MLModels()
        
        # 存储预测结果
        predictions = {}
        model_metrics = {}
        
        for model_type in models:
            # 修改加载路径
            model_path = os.path.join(MODEL_DIR, f"{symbol}_{model_type}.pth")
            logger.info(f"Loading model from {model_path}")
            if not os.path.exists(model_path):
                return jsonify({
                    'status': 'error',
                    'message': f'Model {model_type} not found. Please train the model first.'
                }), 404
                
            if not ml_models.load_model(model_type, model_path):
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to load model {model_type}. Please try training again.'
                }), 500
            
            # 使用最近的数据进行预测
            recent_features = stock_data[feature_columns].values
            pred = ml_models.predict(model_type, recent_features)
            predictions[model_type] = float(pred[-1])  # 只取最后一个预测值
            
            # 计算预测置信度
            confidence = ml_models.calculate_prediction_confidence(
                recent_features,
                model_type
            )
            model_metrics[model_type] = {'confidence': confidence}
        
        # 修改返回数据的处理
        # 确保返回预测日期前30天的数据，包括最近5天
        last_30_days = stock_data.iloc[-90:]  # 获取最后30天数据
        
        # 准备K线数据
        historical_prices = [{
            'open': float(row['Open']),
            'close': float(row['Close']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'volume': float(row['Volume']) if 'Volume' in row else None
        } for _, row in last_30_days.iterrows()]
        
        logger.info(f"Prediction date: {prediction_date}")
        logger.info(f"Data date range: {stock_data.index[0]} to {stock_data.index[-1]}")
        logger.info(f"Number of data points: {len(stock_data)}")
        logger.info(f"Last 5 dates in data: {stock_data.index[-5:].strftime('%Y-%m-%d').tolist()}")
        
        # 准备技术指标数据
        technical_indicators = {
            'SMA_5': stock_data['SMA_5'].tolist(),
            'SMA_20': stock_data['SMA_20'].tolist(),
            'EMA_5': stock_data['EMA_5'].tolist(),
            'EMA_20': stock_data['EMA_20'].tolist(),
            'Returns': stock_data['Returns'].tolist(),
            'Momentum': stock_data['Momentum'].tolist(),
            'Volatility': stock_data['Volatility'].tolist(),
            'Volume_MA_5': stock_data['Volume_MA_5'].tolist(),
            'Volume_MA_20': stock_data['Volume_MA_20'].tolist()
        }
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'historical_dates': last_30_days.index.strftime('%Y-%m-%d').tolist(),
            'historical_prices': historical_prices,
            'technical_indicators': technical_indicators,  # 添加技术指标
            'predictions': predictions,
            'model_metrics': model_metrics
        })
        
    except Exception as e:
        logger.error(f"Error in stock prediction: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/stocks/filter/factors', methods=['POST'])
def filter_stocks_by_factors():
    """根据因子筛选股票"""
    try:
        data = request.get_json()
        factors = data.get('factors', {})
        weights = data.get('weights', {})
        
        if not factors or not weights:
            return jsonify({
                'error': 'Missing required parameters'
            }), 400
            
        filtered_stocks = StockService.apply_factor_filter(factors, weights)
        return jsonify(filtered_stocks)
        
    except Exception as e:
        logger.error(f"Error filtering stocks by factors: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp.route('/stocks/factors/metadata', methods=['GET'])
def get_factor_metadata():
    """获取因子元数据"""
    try:
        metadata = StockService.get_factor_metadata()
        return jsonify(metadata)
    except Exception as e:
        logger.error(f"Error getting factor metadata: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500