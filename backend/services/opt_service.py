import tushare as ts
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from config import settings
from utils.logger import logger
from models.market_data import OptionBasic, OptionDaily

class OptService:
    """期权数据服务"""
    
    def __init__(self):
        """初始化期权数据服务"""
        try:
            self.token = settings.TUSHARE_TOKEN
            if not self.token:
                logger.error("未找到 TUSHARE_TOKEN，请在 .env 文件中设置")
                self.pro = None
            else:
                # 先设置 token，然后再获取 pro 实例
                ts.set_token(self.token)
                try:
                    self.pro = ts.pro_api()
                    # 测试连接
                    self.pro.query('stock_basic', limit=1)
                    logger.info("期权数据服务初始化完成")
                except Exception as e:
                    logger.error(f"Tushare API 连接失败: {e}")
                    self.pro = None
        except Exception as e:
            logger.error(f"期权数据服务初始化失败: {e}")
            self.pro = None
        
    def get_option_basics(self, exchange: str = 'DCE', opt_code: str = None, call_put: str = None) -> List[Dict[str, Any]]:
        """
        获取期权合约基本信息
        
        Args:
            exchange: 交易所代码，默认大连商品交易所
            opt_code: 标准合约代码
            call_put: 期权类型 C或P
            
        Returns:
            期权合约基本信息列表
        """
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取期权合约基本信息")
                return []
                
            logger.info(f"开始获取豆粕期权合约基本信息 - 交易所: {exchange}, 合约代码: {opt_code}, 期权类型: {call_put}")
            params = {'exchange': exchange}
            if opt_code:
                params['opt_code'] = opt_code
            if call_put:
                params['call_put'] = call_put
            
            # 调用Tushare API获取期权基本信息
            df = self.pro.opt_basic(**params)
            
            if df is None or df.empty:
                logger.warning(f"获取期权合约基本信息为空: exchange={exchange}, opt_code={opt_code}, call_put={call_put}")
                return []
            
            try:
                # 过滤只保留豆粕期权合约
                # 豆粕期权的合约代码通常以 m 开头
                # 有些旧版pandas不支持case参数，改用str.lower()
                df = df[df['ts_code'].str.lower().str.startswith('m') | 
                        df['name'].str.contains('豆粕', na=False)]
                
                if df.empty:
                    logger.warning("未找到豆粕相关期权合约")
                    return []
                
                # 筛选只保留01、05、09月份的期权合约
                try:
                    # 从ts_code或name中提取月份信息
                    # 通常格式为 m2401-C-2600.DCE 或类似的格式
                    current_year = datetime.now().year
                    current_month = datetime.now().month
                    
                    # 过滤有效月份的合约 (01, 05, 09)
                    valid_months = []
                    
                    # 计算当前年份和未来一年的有效月份
                    for year in [current_year, current_year + 1]:
                        for month in ["01", "05", "09"]:
                            contract_date = datetime.strptime(f"{year}{month}01", "%Y%m%d")
                            # 只保留当前日期之后的合约
                            if contract_date > datetime.now():
                                valid_months.append(f"{str(year)[-2:]}{month}")  # 格式如 "2401"
                    
                    # 如果没有找到有效月份，添加最近的过去月份
                    if not valid_months:
                        if current_month >= 9:
                            valid_months.append(f"{str(current_year)[-2:]}09")
                        elif current_month >= 5:
                            valid_months.append(f"{str(current_year)[-2:]}05")
                        else:
                            valid_months.append(f"{str(current_year-1)[-2:]}09")
                    
                    logger.info(f"筛选合约月份: {valid_months}")
                    
                    # 过滤合约
                    filtered_df = pd.DataFrame()
                    for month in valid_months:
                        # 尝试从ts_code中匹配，例如 m2401-C-2600.DCE
                        month_df = df[df['ts_code'].str.contains(f"m{month}", case=False, regex=False)]
                        filtered_df = pd.concat([filtered_df, month_df])
                    
                    # 如果过滤后为空，则使用原始数据
                    if filtered_df.empty:
                        logger.warning(f"过滤月份后未找到合约，将使用所有豆粕期权合约")
                    else:
                        df = filtered_df
                        logger.info(f"成功过滤出01、05、09月份的期权合约，共{len(df)}条记录")
                
                except Exception as e:
                    logger.error(f"筛选月份时出错: {str(e)}")
                    logger.info("将使用所有豆粕期权合约")
                
                logger.info(f"成功过滤出豆粕期权合约，共{len(df)}条记录")
            except Exception as e:
                logger.error(f"过滤豆粕期权数据时出错: {str(e)}")
                # 如果过滤出错，尝试直接使用原始数据
                logger.info("将使用所有期权数据，不进行过滤")
            
            # 将DataFrame转换为字典列表
            result = df.to_dict('records')
            
            # 确保数值类型正确
            for item in result:
                for k, v in item.items():
                    if pd.isna(v):
                        item[k] = None
                    elif k in ['exercise_price', 'list_price']:
                        item[k] = float(v) if v is not None else None
                    elif k in ['per_unit', 'quote_unit', 'min_price_chg'] and isinstance(v, (int, float)):
                        # 将数字类型的字段转为字符串
                        item[k] = str(v)
            
            logger.info(f"成功获取豆粕期权合约基本信息，共{len(result)}条记录")
            return result
        except Exception as e:
            logger.error(f"获取期权合约基本信息失败: {str(e)}")
            return []
            
    def get_option_daily(self, ts_code: str = None, trade_date: str = None, 
                         start_date: str = None, end_date: str = None, 
                         exchange: str = 'DCE') -> List[Dict[str, Any]]:
        """
        获取期权日线行情数据
        
        Args:
            ts_code: TS代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所代码
            
        Returns:
            期权日线行情数据列表
        """
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取期权日线行情数据")
                return []
            
            # 如果未指定具体期权代码，先获取豆粕期权列表
            if not ts_code:
                logger.info("未指定期权代码，先获取豆粕期权合约列表")
                try:
                    # 获取经过筛选的豆粕期权合约列表（01、05、09月份）
                    soybean_options = self.get_option_basics(exchange=exchange, call_put=None)
                    if not soybean_options:
                        logger.warning("未找到豆粕期权合约，将尝试获取所有期权")
                        # 如果没有找到豆粕期权，尝试获取交易所的所有期权
                        params = {'exchange': exchange}
                        df = self.pro.opt_basic(**params)
                        if df is None or df.empty:
                            logger.warning("未找到任何期权合约")
                            return []
                        
                        # 尝试从中筛选出豆粕相关合约
                        try:
                            # 过滤只保留豆粕期权合约
                            df = df[df['ts_code'].str.lower().str.startswith('m') | 
                                    df['name'].str.contains('豆粕', na=False)]
                            
                            # 进一步过滤月份
                            current_year = datetime.now().year
                            current_month = datetime.now().month
                            
                            # 计算有效月份
                            valid_months = []
                            # 计算当前年份和未来一年的有效月份
                            for year in [current_year, current_year + 1]:
                                for month in ["01", "05", "09"]:
                                    contract_date = datetime.strptime(f"{year}{month}01", "%Y%m%d")
                                    # 只保留当前日期之后的合约
                                    if contract_date > datetime.now():
                                        valid_months.append(f"{str(year)[-2:]}{month}")  # 格式如 "2401"
                            
                            # 如果没有找到有效月份，添加最近的过去月份
                            if not valid_months:
                                if current_month >= 9:
                                    valid_months.append(f"{str(current_year)[-2:]}09")
                                elif current_month >= 5:
                                    valid_months.append(f"{str(current_year)[-2:]}05")
                                else:
                                    valid_months.append(f"{str(current_year-1)[-2:]}09")
                            
                            # 过滤合约
                            filtered_df = pd.DataFrame()
                            for month in valid_months:
                                month_df = df[df['ts_code'].str.contains(f"m{month}", case=False, regex=False)]
                                filtered_df = pd.concat([filtered_df, month_df])
                            
                            if not filtered_df.empty:
                                df = filtered_df
                        except Exception as e:
                            logger.error(f"过滤合约月份时出错: {str(e)}")
                        
                        # 将DataFrame转换为字典列表
                        soybean_options = df.to_dict('records')
                        
                        if not soybean_options:
                            logger.warning("转换后期权合约列表为空")
                            return []
                        
                        logger.info(f"获取到{len(soybean_options)}个期权合约")
                    
                    # 从每个月份和类型选择代表性合约
                    # 例如，从每个月份中选择一个平值看涨和一个平值看跌期权
                    try:
                        # 按月份和期权类型分组
                        grouped_options = {}
                        for option in soybean_options:
                            # 提取月份，例如从 m2401-C-2600.DCE 中提取 2401
                            ts_code = option['ts_code']
                            month_match = None
                            call_put = option.get('call_put')
                            
                            # 尝试从ts_code中提取月份
                            try:
                                if 'm' in ts_code.lower():
                                    # 假设格式为 m2401-C-2600.DCE
                                    parts = ts_code.split('-')
                                    if len(parts) > 0:
                                        # 从第一部分提取月份，如 m2401
                                        first_part = parts[0]
                                        # 移除非数字字符
                                        month_part = ''.join(filter(str.isdigit, first_part))
                                        if len(month_part) >= 4:
                                            # 获取月份部分（后4位）
                                            month_match = month_part[-4:]
                            except Exception as e:
                                logger.debug(f"从ts_code提取月份出错: {str(e)}")
                            
                            if month_match and call_put:
                                key = f"{month_match}_{call_put}"
                                if key not in grouped_options:
                                    grouped_options[key] = []
                                grouped_options[key].append(option)
                        
                        # 从每个分组中选择平值期权（行权价最接近当前价格）
                        # 由于我们没有当前价格信息，暂时选择每组的第一个
                        selected_options = []
                        for key, options in grouped_options.items():
                            if options:
                                # 暂时选择每组的第一个
                                selected_options.append(options[0])
                        
                        # 如果选择结果不为空，使用选择的合约
                        if selected_options:
                            soybean_options = selected_options
                            logger.info(f"从各月份中选择了{len(selected_options)}个代表性期权合约")
                    except Exception as e:
                        logger.error(f"选择代表性期权合约失败: {str(e)}")
                    
                    # 选择最新上市的合约
                    try:
                        # 按上市日期排序（从新到旧）
                        soybean_options.sort(key=lambda x: x.get('list_date', ''), reverse=True)
                    except Exception as e:
                        logger.error(f"排序期权合约失败: {str(e)}")
                    
                    # 选择前几个合约
                    ts_codes = [option['ts_code'] for option in soybean_options[:6]]  # 选择最新的6个合约
                    logger.info(f"选择的期权合约: {ts_codes}")
                except Exception as e:
                    logger.error(f"获取期权合约列表失败: {str(e)}")
                    # 如果获取期权列表失败，使用默认的豆粕期权代码
                    # 尝试构造当前年月的期权代码
                    current_year = datetime.now().year % 100  # 取年份的后两位
                    current_month = datetime.now().month
                    
                    # 确定最近的1月、5月和9月
                    months = []
                    if current_month < 1:
                        months.append(f"{current_year-1}09")
                    elif current_month < 5:
                        months.append(f"{current_year}01")
                    elif current_month < 9:
                        months.append(f"{current_year}05")
                    else:
                        months.append(f"{current_year}09")
                    
                    # 构造默认期权代码
                    ts_codes = []
                    for month in months:
                        ts_codes.append(f"m{month}-C-3000.DCE")  # 看涨期权
                        ts_codes.append(f"m{month}-P-3000.DCE")  # 看跌期权
                    
                    logger.info(f"将使用默认期权代码: {ts_codes}")
            else:
                # 确保提供的ts_code是字符串
                ts_code = str(ts_code)
                # 检查是否是豆粕期权
                try:
                    if not ts_code.lower().startswith('m'):
                        logger.warning(f"指定的期权代码 {ts_code} 可能不是豆粕期权")
                except Exception as e:
                    logger.error(f"检查期权代码时出错: {str(e)}")
                ts_codes = [ts_code]
            
            all_daily_data = []
            
            for code in ts_codes:
                try:
                    logger.info(f"开始获取期权日线行情数据 - TS代码: {code}, 交易日期: {trade_date}, 交易所: {exchange}")
                    # 默认获取最近一个月的数据
                    if not start_date and not end_date and not trade_date:
                        end_date = datetime.now().strftime('%Y%m%d')
                        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                        logger.info(f"未指定日期范围，默认获取最近一个月数据: {start_date} - {end_date}")
                    
                    params = {'exchange': exchange, 'ts_code': code}
                    if trade_date:
                        params['trade_date'] = trade_date
                    if start_date:
                        params['start_date'] = start_date
                    if end_date:
                        params['end_date'] = end_date
                    
                    # 调用Tushare API获取期权日线行情
                    df = self.pro.opt_daily(**params)
                    
                    if df is None or df.empty:
                        logger.warning(f"获取期权日线行情数据为空: ts_code={code}, trade_date={trade_date}, exchange={exchange}")
                        continue
                    
                    # 按日期排序
                    try:
                        df = df.sort_values(by=['trade_date'])
                    except Exception as e:
                        logger.error(f"排序日期时出错: {str(e)}")
                        # 如果排序失败，继续处理
                    
                    # 将DataFrame转换为字典列表
                    result = df.to_dict('records')
                    
                    # 确保数值类型正确
                    for item in result:
                        for k, v in item.items():
                            if pd.isna(v):
                                item[k] = None
                            elif k in ['pre_settle', 'pre_close', 'open', 'high', 'low', 'close', 'settle', 'vol', 'amount', 'oi']:
                                try:
                                    item[k] = float(v) if v is not None else None
                                except (ValueError, TypeError):
                                    # 如果转换失败，设置为None
                                    item[k] = None
                    
                    all_daily_data.extend(result)
                    logger.info(f"成功获取期权 {code} 的日线数据，共{len(result)}条记录")
                except Exception as e:
                    logger.error(f"获取期权 {code} 的日线数据失败: {str(e)}")
                    # 继续处理下一个期权代码
            
            if not all_daily_data:
                logger.warning("未获取到任何豆粕期权日线行情数据")
                return []
                
            logger.info(f"成功获取期权日线行情数据，共{len(all_daily_data)}条记录")
            return all_daily_data
        except Exception as e:
            logger.error(f"获取期权日线行情数据失败: {str(e)}")
            return []

    async def get_option_basics(self, exchange: str = 'DCE', opt_code: str = None, call_put: str = None) -> List[OptionBasic]:
        """获取期权基础信息"""
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取期权基础信息")
                return []
                
            logger.info(f"开始获取豆粕期权基础信息 - 交易所: {exchange}")
            params = {'exchange': exchange}
            if opt_code:
                params['opt_code'] = opt_code
            if call_put:
                params['call_put'] = call_put

            df = self.pro.opt_basic(**params)
            
            if df is None or df.empty:
                logger.warning("获取期权基础信息为空")
                return []
            
            # 过滤只保留豆粕期权
            df = df[df['ts_code'].str.lower().str.startswith('m')]
            
            # 按到期日期排序
            if 'maturity_date' in df.columns:
                df = df.sort_values('maturity_date')
            
            result = []
            for _, row in df.iterrows():
                try:
                    option_basic = OptionBasic(
                        ts_code=row['ts_code'],
                        name=row['name'],
                        exercise_price=float(row['exercise_price']),
                        maturity_date=row.get('maturity_date', ''),
                        call_put=row['call_put'],
                        exchange=exchange,
                        opt_code=row.get('opt_code'),
                        underlying_code=row.get('underlying_code')
                    )
                    result.append(option_basic)
                except Exception as e:
                    logger.error(f"处理期权基础信息行数据失败: {e}, 数据: {row.to_dict()}")
                    continue
            
            logger.info(f"成功获取期权基础信息，共{len(result)}条记录")
            return result
        except Exception as e:
            logger.error(f"获取期权基础信息失败: {e}")
            raise

    async def get_option_daily(self, ts_code: str = None, trade_date: str = None,
                             start_date: str = None, end_date: str = None,
                             exchange: str = 'DCE') -> List[OptionDaily]:
        """获取期权日线数据"""
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取期权日线数据")
                return []

            params = {'exchange': exchange}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            else:
                # 默认获取最近一个月的数据
                params['end_date'] = datetime.now().strftime('%Y%m%d')
                params['start_date'] = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.pro.opt_daily(**params)
            if df is None or df.empty:
                return []

            # 按日期排序
            df = df.sort_values('trade_date')
            
            result = []
            for _, row in df.iterrows():
                try:
                    daily_data = OptionDaily(
                        ts_code=row['ts_code'],
                        trade_date=row['trade_date'],
                        exchange=exchange,  # 添加交易所信息
                        pre_settle=float(row['pre_settle']) if not pd.isna(row['pre_settle']) else None,
                        pre_close=float(row['pre_close']) if not pd.isna(row['pre_close']) else None,
                        open=float(row['open']) if not pd.isna(row['open']) else None,
                        high=float(row['high']) if not pd.isna(row['high']) else None,
                        low=float(row['low']) if not pd.isna(row['low']) else None,
                        close=float(row['close']) if not pd.isna(row['close']) else None,
                        settle=float(row['settle']) if not pd.isna(row['settle']) else None,
                        vol=float(row['vol']) if not pd.isna(row['vol']) else None,
                        amount=float(row['amount']) if not pd.isna(row['amount']) else None,
                        oi=float(row['oi']) if not pd.isna(row['oi']) else None
                    )
                    result.append(daily_data)
                except Exception as e:
                    logger.error(f"处理期权日线数据行失败: {e}")
                    continue
            
            return result
        except Exception as e:
            logger.error(f"获取期权日线数据失败: {e}")
            raise

    async def get_option_daily_by_code(self, ts_code: str, start_date: str, end_date: str) -> List[OptionDaily]:
        """获取指定期权的日线数据"""
        return await self.get_option_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        ) 