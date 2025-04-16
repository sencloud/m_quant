from datetime import datetime, timedelta
import json
import os
from typing import Optional
import pandas as pd
import tushare as ts

from AI.data.cache import get_cache
from AI.data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
)
from loguru import logger
from config import settings

# Global cache instance
_cache = get_cache()

# 初始化tushare
def _init_tushare():
    """初始化tushare API"""
    token = settings.TUSHARE_TOKEN
    if not token:
        logger.error("未找到 TUSHARE_TOKEN，请在 .env 文件中设置")
        return None
    
    try:
        ts.set_token(token)
        pro = ts.pro_api()
        # 测试连接
        pro.query('stock_basic', limit=1)
        logger.info("Tushare API初始化完成")
        return pro
    except Exception as e:
        logger.error(f"Tushare API 连接失败: {e}")
        return None

# 全局tushare实例
_pro = _init_tushare()

def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data from cache or API."""
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by date range and convert to Price objects
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # If not in cache or no data in range, fetch from API
    if _pro is None:
        logger.error("Tushare API 未初始化，无法获取价格数据")
        return []
    
    try:
        # 转换日期格式为YYYYMMDD
        start_date_formatted = start_date.replace('-', '')
        end_date_formatted = end_date.replace('-', '')
        
        # 获取股票代码格式
        if '.' not in ticker:
            # 假设是A股，添加后缀
            if ticker.startswith('6'):
                ts_code = f"{ticker}.SH"
            else:
                ts_code = f"{ticker}.SZ"
        else:
            ts_code = ticker
        
        # 获取日线数据
        df = _pro.daily(ts_code=ts_code, start_date=start_date_formatted, end_date=end_date_formatted)
        
        if df is None or df.empty:
            logger.warning(f"未找到价格数据: {ticker}, 时间范围: {start_date} - {end_date}")
            return []
        
        # 转换为Price对象
        prices = []
        for _, row in df.iterrows():
            # 转换日期格式为YYYY-MM-DD
            date_str = row['trade_date']
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            
            price = Price(
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                volume=int(row['vol']),
                time=formatted_date
            )
            prices.append(price)
        
        # Cache the results as dicts
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        return prices
    except Exception as e:
        logger.error(f"获取价格数据失败: {ticker} - {e}")
        return []


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    ann_date: str | None = None,
    start_date: str | None = None,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from cache or API."""
    logger.info(f"开始获取财务指标数据: ticker={ticker}, end_date={end_date}, period={period}, limit={limit}")
    
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        logger.info(f"从缓存获取到财务指标数据: {len(cached_data)}条")
        # Filter cached data by date and limit
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            logger.info(f"缓存数据过滤后: {len(filtered_data)}条")
            return filtered_data[:limit]

    # If not in cache or insufficient data, fetch from API
    if _pro is None:
        logger.error("Tushare API 未初始化，无法获取财务指标数据")
        return []
    
    try:
        # 转换日期格式为YYYYMMDD
        end_date_formatted = end_date.replace('-', '')
        start_date_formatted = start_date.replace('-', '') if start_date else None
        ann_date_formatted = ann_date.replace('-', '') if ann_date else None
        
        # 获取股票代码格式
        if '.' not in ticker:
            # 假设是A股，添加后缀
            if ticker.startswith('6'):
                ts_code = f"{ticker}.SH"
            else:
                ts_code = f"{ticker}.SZ"
        else:
            ts_code = ticker
        
        logger.info(f"准备调用Tushare API: ts_code={ts_code}, end_date={end_date_formatted}")
        
        # 获取财务指标数据
        df = _pro.fina_indicator(ts_code=ts_code)

        logger.info(f"获取财务指标数据: {ticker}, 结束日期: {end_date}, 数据数量: {len(df)}")
        
        if df is None or df.empty:
            logger.warning(f"未找到财务指标数据: {ticker}, 结束日期: {end_date}")
            return []
        
        # 转换为FinancialMetrics对象
        metrics = []
        for _, row in df.iterrows():
            # 转换日期格式为YYYY-MM-DD
            date_str = row['end_date']
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            
            try:
                metric = FinancialMetrics(
                    ticker=ticker,
                    report_period=formatted_date,
                    period=period,
                    currency="CNY",
                    market_cap=float(row['total_mv']) if 'total_mv' in row and pd.notna(row['total_mv']) else None,
                    enterprise_value=None,  # tushare没有直接提供
                    price_to_earnings_ratio=float(row['pe']) if 'pe' in row and pd.notna(row['pe']) else None,
                    price_to_book_ratio=float(row['pb']) if 'pb' in row and pd.notna(row['pb']) else None,
                    price_to_sales_ratio=None,  # tushare没有直接提供
                    enterprise_value_to_ebitda_ratio=None,  # tushare没有直接提供
                    enterprise_value_to_revenue_ratio=None,  # tushare没有直接提供
                    free_cash_flow_yield=None,  # tushare没有直接提供
                    peg_ratio=None,  # tushare没有直接提供
                    gross_margin=float(row['gross_margin']) if 'gross_margin' in row and pd.notna(row['gross_margin']) else None,
                    operating_margin=None,  # tushare没有直接提供
                    net_margin=float(row['netprofit_margin']) if 'netprofit_margin' in row and pd.notna(row['netprofit_margin']) else None,
                    return_on_equity=float(row['roe']) if 'roe' in row and pd.notna(row['roe']) else None,
                    return_on_assets=float(row['roa']) if 'roa' in row and pd.notna(row['roa']) else None,
                    return_on_invested_capital=float(row['roic']) if 'roic' in row and pd.notna(row['roic']) else None,
                    asset_turnover=float(row['assets_turn']) if 'assets_turn' in row and pd.notna(row['assets_turn']) else None,
                    inventory_turnover=float(row['inv_turn']) if 'inv_turn' in row and pd.notna(row['inv_turn']) else None,
                    receivables_turnover=float(row['ar_turn']) if 'ar_turn' in row and pd.notna(row['ar_turn']) else None,
                    days_sales_outstanding=float(row['arturn_days']) if 'arturn_days' in row and pd.notna(row['arturn_days']) else None,
                    operating_cycle=float(row['turn_days']) if 'turn_days' in row and pd.notna(row['turn_days']) else None,
                    working_capital_turnover=None,  # tushare没有直接提供
                    current_ratio=float(row['current_ratio']) if 'current_ratio' in row and pd.notna(row['current_ratio']) else None,
                    quick_ratio=float(row['quick_ratio']) if 'quick_ratio' in row and pd.notna(row['quick_ratio']) else None,
                    cash_ratio=float(row['cash_ratio']) if 'cash_ratio' in row and pd.notna(row['cash_ratio']) else None,
                    operating_cash_flow_ratio=None,  # tushare没有直接提供
                    debt_to_equity=float(row['debt_to_eqt']) if 'debt_to_eqt' in row and pd.notna(row['debt_to_eqt']) else None,
                    debt_to_assets=float(row['debt_to_assets']) if 'debt_to_assets' in row and pd.notna(row['debt_to_assets']) else None,
                    interest_coverage=float(row['ebit_to_interest']) if 'ebit_to_interest' in row and pd.notna(row['ebit_to_interest']) else None,
                    revenue_growth=float(row['tr_yoy']) if 'tr_yoy' in row and pd.notna(row['tr_yoy']) else None,
                    earnings_growth=float(row['netprofit_yoy']) if 'netprofit_yoy' in row and pd.notna(row['netprofit_yoy']) else None,
                    book_value_growth=float(row['bps_yoy']) if 'bps_yoy' in row and pd.notna(row['bps_yoy']) else None,
                    earnings_per_share_growth=float(row['basic_eps_yoy']) if 'basic_eps_yoy' in row and pd.notna(row['basic_eps_yoy']) else None,
                    free_cash_flow_growth=float(row['ocf_yoy']) if 'ocf_yoy' in row and pd.notna(row['ocf_yoy']) else None,
                    operating_income_growth=float(row['op_yoy']) if 'op_yoy' in row and pd.notna(row['op_yoy']) else None,
                    ebitda_growth=None,  # tushare没有直接提供
                    payout_ratio=None,  # tushare没有直接提供
                    earnings_per_share=float(row['eps']) if 'eps' in row and pd.notna(row['eps']) else None,
                    book_value_per_share=float(row['bps']) if 'bps' in row and pd.notna(row['bps']) else None,
                    free_cash_flow_per_share=float(row['cfps']) if 'cfps' in row and pd.notna(row['cfps']) else None,
                )
                metrics.append(metric)
            except Exception as e:
                logger.error(f"处理财务指标数据行时出错: {e}, 行数据: {row.to_dict()}")
                continue
        
        logger.info(f"成功处理财务指标数据: {len(metrics)}条")
        
        # Cache the results as dicts
        _cache.set_financial_metrics(ticker, [m.model_dump() for m in metrics])
        return metrics
    except Exception as e:
        logger.error(f"获取财务指标数据失败: {ticker} - {e}")
        import traceback
        traceback.print_exc()
        return []


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[LineItem]:
    """Fetch line items from API."""
    logger.info(f"开始获取财务指标行项目: ticker={ticker}, line_items={line_items}, end_date={end_date}, period={period}")
    
    if _pro is None:
        logger.error("Tushare API 未初始化，无法获取财务指标数据")
        return []
    
    try:
        # 转换日期格式为YYYYMMDD
        end_date_formatted = end_date.replace('-', '')
        
        # 获取股票代码格式
        if '.' not in ticker:
            # 假设是A股，添加后缀
            if ticker.startswith('6'):
                ts_code = f"{ticker}.SH"
            else:
                ts_code = f"{ticker}.SZ"
        else:
            ts_code = ticker
        
        logger.info(f"准备调用Tushare API: ts_code={ts_code}, end_date={end_date_formatted}")
        
        # 获取财务指标数据
        df = _pro.fina_indicator(ts_code=ts_code)

        logger.info(f"获取财务指标数据: {ticker}, 结束日期: {end_date}, 数据数量: {len(df)}")
        
        if df is None or df.empty:
            logger.warning(f"未找到财务指标数据: {ticker}, 结束日期: {end_date}")
            return []
        
        # 转换为LineItem对象
        results = []
        for _, row in df.iterrows():
            # 转换日期格式为YYYY-MM-DD
            date_str = row['end_date']
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            
            try:
                # 创建LineItem对象
                line_item = LineItem(
                    ticker=ticker,
                    report_period=formatted_date,
                    period=period,
                    currency="CNY",
                    revenue=float(row['revenue']) if 'revenue' in row and pd.notna(row['revenue']) else None,
                    earnings_per_share=float(row['eps']) if 'eps' in row and pd.notna(row['eps']) else None,
                    net_income=float(row['netprofit']) if 'netprofit' in row and pd.notna(row['netprofit']) else None,
                    free_cash_flow=float(row['ocf']) if 'ocf' in row and pd.notna(row['ocf']) else None,
                    operating_margin=float(row['op_margin']) if 'op_margin' in row and pd.notna(row['op_margin']) else None,
                    depreciation_and_amortization=float(row['dep_amor']) if 'dep_amor' in row and pd.notna(row['dep_amor']) else None,
                    total_assets=float(row['total_assets']) if 'total_assets' in row and pd.notna(row['total_assets']) else None,
                    total_liabilities=float(row['total_liab']) if 'total_liab' in row and pd.notna(row['total_liab']) else None,
                    current_assets=float(row['total_cur_assets']) if 'total_cur_assets' in row and pd.notna(row['total_cur_assets']) else None,
                    current_liabilities=float(row['total_cur_liab']) if 'total_cur_liab' in row and pd.notna(row['total_cur_liab']) else None,
                    book_value_per_share=float(row['bps']) if 'bps' in row and pd.notna(row['bps']) else None,
                    dividends_and_other_cash_distributions=float(row['dv_ratio']) if 'dv_ratio' in row and pd.notna(row['dv_ratio']) else None,
                    outstanding_shares=float(row['total_share']) if 'total_share' in row and pd.notna(row['total_share']) else None,
                    line_items={}  # 初始化空字典
                )
                
                # 填充请求的line_items
                for item in line_items:
                    if item in row and pd.notna(row[item]):
                        line_item.line_items[item] = float(row[item])
                
                results.append(line_item)
            except Exception as e:
                logger.error(f"处理财务指标行项目数据时出错: {e}, 行数据: {row.to_dict()}")
                continue
        
        logger.info(f"成功处理财务指标行项目数据: {len(results)}条")
        return results
    except Exception as e:
        logger.error(f"获取财务指标行项目数据失败: {ticker} - {e}")
        import traceback
        traceback.print_exc()
        return []


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[InsiderTrade]:
    """Fetch insider trades from cache or API."""
    # Check cache first
    if cached_data := _cache.get_insider_trades(ticker):
        # Filter cached data by date range
        filtered_data = [InsiderTrade(**trade) for trade in cached_data 
                        if (start_date is None or (trade.get("transaction_date") or trade["filing_date"]) >= start_date)
                        and (trade.get("transaction_date") or trade["filing_date"]) <= end_date]
        filtered_data.sort(key=lambda x: x.transaction_date or x.filing_date, reverse=True)
        if filtered_data:
            return filtered_data

    # If not in cache or insufficient data, fetch from API
    if _pro is None:
        logger.error("Tushare API 未初始化，无法获取高管持股变动数据")
        return []
    
    try:
        # 转换日期格式为YYYYMMDD
        end_date_formatted = end_date.replace('-', '')
        start_date_formatted = start_date.replace('-', '') if start_date else None
        
        # 获取股票代码格式
        if '.' not in ticker:
            # 假设是A股，添加后缀
            if ticker.startswith('6'):
                ts_code = f"{ticker}.SH"
            else:
                ts_code = f"{ticker}.SZ"
        else:
            ts_code = ticker
        
        # 获取高管持股变动数据
        params = {'ts_code': ts_code, 'end_date': end_date_formatted, 'limit': limit}
        if start_date_formatted:
            params['start_date'] = start_date_formatted
            
        df = _pro.stk_holdertrade(**params)
        
        if df is None or df.empty:
            logger.warning(f"未找到高管持股变动数据: {ticker}, 时间范围: {start_date} - {end_date}")
            return []
        
        # 转换为InsiderTrade对象
        trades = []
        for _, row in df.iterrows():
            # 转换日期格式为YYYY-MM-DD
            date_str = row['ann_date']
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            
            trade = InsiderTrade(
                ticker=ticker,
                issuer=None,  # tushare没有直接提供
                name=row['holder_name'] if 'holder_name' in row and pd.notna(row['holder_name']) else None,
                title=None,  # tushare没有直接提供
                is_board_director=None,  # tushare没有直接提供
                transaction_date=formatted_date,
                transaction_shares=float(row['vol']) if 'vol' in row and pd.notna(row['vol']) else None,
                transaction_price_per_share=float(row['price']) if 'price' in row and pd.notna(row['price']) else None,
                transaction_value=float(row['vol']) * float(row['price']) if 'vol' in row and 'price' in row and pd.notna(row['vol']) and pd.notna(row['price']) else None,
                shares_owned_before_transaction=None,  # tushare没有直接提供
                shares_owned_after_transaction=None,  # tushare没有直接提供
                security_title=None,  # tushare没有直接提供
                filing_date=formatted_date
            )
            trades.append(trade)
        
        # Cache the results
        _cache.set_insider_trades(ticker, [trade.model_dump() for trade in trades])
        return trades
    except Exception as e:
        logger.error(f"获取高管持股变动数据失败: {ticker} - {e}")
        return []


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[CompanyNews]:
    """Fetch company news from cache or API."""
    # Check cache first
    if cached_data := _cache.get_company_news(ticker):
        # Filter cached data by date range
        filtered_data = [CompanyNews(**news) for news in cached_data 
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data

    # If not in cache or insufficient data, fetch from API
    if _pro is None:
        logger.error("Tushare API 未初始化，无法获取新闻数据")
        return []
    
    try:
        # 转换日期格式为YYYY-MM-DD
        end_date_formatted = end_date.replace('-', '')
        start_date_formatted = start_date.replace('-', '') if start_date else None
        
        # 获取股票代码格式
        if '.' not in ticker:
            # 假设是A股，添加后缀
            if ticker.startswith('6'):
                ts_code = f"{ticker}.SH"
            else:
                ts_code = f"{ticker}.SZ"
        else:
            ts_code = ticker
        
        # 获取新闻数据
        params = {'end_date': end_date_formatted, 'limit': limit}
        if start_date_formatted:
            params['start_date'] = start_date_formatted
            
        df = _pro.news(src='sina', **params)
        
        if df is None or df.empty:
            logger.warning(f"未找到新闻数据: {ticker}, 时间范围: {start_date} - {end_date}")
            return []
        
        # 转换为CompanyNews对象
        news_list = []
        for _, row in df.iterrows():
            # 转换日期格式为YYYY-MM-DD
            date_str = row['datetime']
            formatted_date = date_str.split(' ')[0]  # 假设格式为YYYY-MM-DD HH:MM:SS
            
            # 检查新闻内容是否与股票相关
            content = row['content'] if 'content' in row and pd.notna(row['content']) else ''
            if ticker not in content and ts_code not in content:
                continue
                
            news = CompanyNews(
                ticker=ticker,
                title=row['title'] if 'title' in row and pd.notna(row['title']) else '',
                author=None,  # tushare没有直接提供
                source=row['source'] if 'source' in row and pd.notna(row['source']) else 'sina',
                date=formatted_date,
                url=row['url'] if 'url' in row and pd.notna(row['url']) else '',
                sentiment=None  # tushare没有直接提供
            )
            news_list.append(news)
        
        # Cache the results
        _cache.set_company_news(ticker, [news.model_dump() for news in news_list])
        return news_list
    except Exception as e:
        logger.error(f"获取新闻数据失败: {ticker} - {e}")
        return []


def get_market_cap(
    ticker: str,
    end_date: str,
) -> float | None:
    """Fetch market cap from the API."""
    financial_metrics = get_financial_metrics(ticker, end_date)
    if not financial_metrics:
        return None
        
    market_cap = financial_metrics[0].market_cap
    if not market_cap:
        return None

    return market_cap


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)
