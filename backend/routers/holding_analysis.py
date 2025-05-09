from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import math
from config import settings
from utils.logger import logger
import json

router = APIRouter()

# 初始化tushare
ts.set_token(settings.TUSHARE_TOKEN)
pro = ts.pro_api()

def clean_float(value: float) -> float:
    """处理异常浮点数，确保JSON序列化不会失败"""
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return float(value)
    return 0.0

def safe_int(value: float) -> int:
    """安全地将浮点数转换为整数，处理NaN和inf"""
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return 0
        return int(value)
    return 0

def clean_value(value: Any) -> Any:
    """清理任意值中的异常浮点数"""
    if isinstance(value, dict):
        return {k: clean_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [clean_value(item) for item in value]
    elif isinstance(value, float):
        return clean_float(value)
    return value

@router.get("/broker-holdings")
async def get_broker_holdings(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取期货公司维度的持仓变化数据"""
    try:
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
            
        logger.info(f"查询期货公司持仓数据 - 合约: {symbol}, 日期范围: {start_date} 至 {end_date}")

        df = pro.fut_holding(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"获取到原始数据 {len(df)} 条记录")

        if df.empty:
            logger.warning(f"未找到合约 {symbol} 在 {start_date} 至 {end_date} 的持仓数据")
            raise HTTPException(status_code=404, detail="No data found")

        # 填充NaN值
        df = df.fillna(0)
        logger.debug(f"填充NaN值后的数据形状: {df.shape}")

        # 计算每个期货公司的关键指标
        broker_stats = []
        unique_brokers = df['broker'].unique()
        logger.info(f"发现 {len(unique_brokers)} 家期货公司")
        
        for broker in unique_brokers:
            logger.debug(f"处理期货公司: {broker}")
            broker_data = df[df['broker'] == broker]
            
            # 计算持仓变化趋势
            holdings_trend = []
            unique_dates = sorted(broker_data['trade_date'].unique())
            logger.debug(f"期货公司 {broker} 有 {len(unique_dates)} 天的数据")
            
            for i, date in enumerate(unique_dates):
                daily_data = broker_data[broker_data['trade_date'] == date].iloc[0]
                long_hld = safe_int(daily_data['long_hld'])
                short_hld = safe_int(daily_data['short_hld'])
                
                # 计算当日变化
                if i > 0:
                    prev_data = broker_data[broker_data['trade_date'] == unique_dates[i-1]].iloc[0]
                    long_chg = long_hld - prev_data['long_hld']
                    short_chg = short_hld - prev_data['short_hld']
                else:
                    long_chg = 0
                    short_chg = 0
                
                # 净持仓变化 = 多头变化 - 空头变化
                net_change = long_chg - short_chg
                
                holdings_trend.append({
                    'date': date,
                    'long_hld': long_hld,  # 多头持仓
                    'short_hld': short_hld,  # 空头持仓
                    'long_chg': long_chg,  # 多头变化
                    'short_chg': short_chg,  # 空头变化
                    'net_change': net_change  # 净持仓变化
                })
                
                logger.debug(f"日期 {date}, 期货公司 {broker}: 多头持仓 {long_hld}, 空头持仓 {short_hld}, 净持仓变化 {net_change}")

            # 计算汇总数据
            total_vol = safe_int(broker_data['vol'].sum())
            first_day = broker_data[broker_data['trade_date'] == unique_dates[0]].iloc[0]
            last_day = broker_data[broker_data['trade_date'] == unique_dates[-1]].iloc[0]
            
            net_long_chg = last_day['long_hld'] - first_day['long_hld']
            net_short_chg = last_day['short_hld'] - first_day['short_hld']
            net_position_change = net_long_chg - net_short_chg  # 修正净持仓变化计算

            logger.debug(f"期货公司 {broker} 统计指标: 总成交量 {total_vol}")
            logger.debug(f"期货公司 {broker} 净持仓变化: {net_position_change} (多头变化 {net_long_chg}, 空头变化 {net_short_chg})")

            broker_stats.append({
                'broker': broker,
                'holdings_trend': holdings_trend,
                'summary': {
                    'total_vol': total_vol,
                    'net_long_chg': net_long_chg,
                    'net_short_chg': net_short_chg,
                    'net_position_change': net_position_change
                }
            })

        # 按总成交量排序
        broker_stats.sort(key=lambda x: x['summary']['total_vol'], reverse=True)
        logger.info(f"按总成交量排序后，排名第一的期货公司是: {broker_stats[0]['broker'] if broker_stats else 'N/A'}")

        result = {
            'success': True,
            'data': clean_value(broker_stats)
        }
        logger.info(f"成功处理期货公司持仓数据，返回 {len(broker_stats)} 家期货公司的数据")
        return result

    except Exception as e:
        logger.error(f"获取期货公司持仓数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-holdings")
async def get_daily_holdings(
    symbol: str,
    trade_date: str,
    top_n: int = 10
):
    """获取指定交易日的持仓排名数据"""
    try:
        logger.info(f"查询单日持仓数据 - 合约: {symbol}, 日期: {trade_date}, top_n: {top_n}")

        df = pro.fut_holding(
            symbol=symbol,
            trade_date=trade_date
        )

        logger.info(f"获取到原始数据 {len(df)} 条记录")

        if df.empty:
            logger.warning(f"未找到合约 {symbol} 在 {trade_date} 的持仓数据")
            raise HTTPException(status_code=404, detail="No data found")

        # 填充NaN值
        df = df.fillna(0)
        logger.debug(f"填充NaN值后的数据形状: {df.shape}")

        # 计算影响力得分
        total_vol = df['vol'].sum()
        logger.debug(f"总成交量: {total_vol}")
        df['vol_ratio'] = df['vol'] / total_vol
        df['net_position_change'] = df['long_chg'] - df['short_chg']
        df['impact_score'] = df['net_position_change'] * df['vol_ratio']
        
        logger.debug(f"计算影响力得分后的数据头部: {df[['broker', 'vol', 'vol_ratio', 'net_position_change', 'impact_score']].head().to_dict()}")

        # 获取多空持仓排名
        top_long = df.nlargest(top_n, 'long_chg')[
            ['broker', 'long_hld', 'long_chg', 'impact_score']
        ].to_dict('records')
        
        top_short = df.nlargest(top_n, 'short_chg')[
            ['broker', 'short_hld', 'short_chg', 'impact_score']
        ].to_dict('records')

        logger.info(f"多头持仓排名前 {len(top_long)} 名: {[item['broker'] for item in top_long[:3]]}...")
        logger.info(f"空头持仓排名前 {len(top_short)} 名: {[item['broker'] for item in top_short[:3]]}...")

        total_net_position_change = safe_int(df['net_position_change'].sum())
        logger.info(f"总净持仓变化: {total_net_position_change}")

        result = {
            'trade_date': trade_date,
            'top_long': top_long,
            'top_short': top_short,
            'total_vol': safe_int(total_vol),
            'net_position_change': total_net_position_change
        }

        logger.info(f"成功处理单日持仓数据，返回多头排名 {len(top_long)} 条，空头排名 {len(top_short)} 条")
        return {
            'success': True,
            'data': clean_value(result)
        }

    except Exception as e:
        logger.error(f"获取单日持仓数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/holding-correlation")
async def get_holding_correlation(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """分析主力持仓变化与价格变化的相关性"""
    try:
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            
        logger.info(f"查询持仓相关性数据 - 合约: {symbol}, 日期范围: {start_date} 至 {end_date}")

        df = pro.fut_holding(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"获取到原始数据 {len(df)} 条记录")

        if df.empty:
            logger.warning(f"未找到合约 {symbol} 在 {start_date} 至 {end_date} 的持仓数据")
            raise HTTPException(status_code=404, detail="No data found")

        # 填充NaN值
        df = df.fillna(0)
        logger.debug(f"填充NaN值后的数据形状: {df.shape}")

        # 计算每日净持仓变化
        logger.debug(f"开始计算每日净持仓变化")
        daily_net_change = df.groupby('trade_date').agg({
            'long_chg': 'sum',
            'short_chg': 'sum'
        })
        daily_net_change['net_change'] = daily_net_change['long_chg'] - daily_net_change['short_chg']
        
        logger.debug(f"每日净持仓变化数据形状: {daily_net_change.shape}")
        logger.debug(f"每日净持仓变化数据头部: {daily_net_change.head().to_dict()}")
        
        result = []
        for date, row in daily_net_change.iterrows():
            long_chg = safe_int(row['long_chg'])
            short_chg = safe_int(row['short_chg'])
            net_change = safe_int(row['net_change'])
            
            logger.debug(f"日期 {date}: 多头变化 {long_chg}, 空头变化 {short_chg}, 净变化 {net_change}")
            
            result.append({
                'trade_date': date,
                'long_chg': long_chg,
                'short_chg': short_chg,
                'net_change': net_change
            })

        logger.info(f"成功处理持仓相关性数据，返回 {len(result)} 天的数据")
        return {
            'success': True,
            'data': clean_value(result)
        }

    except Exception as e:
        logger.error(f"获取持仓相关性数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 