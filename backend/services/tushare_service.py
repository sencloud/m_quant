from typing import List
from datetime import datetime, timedelta
from log import logger
from models.market_data import OptionDaily

class TushareService:
    async def get_option_daily(self) -> List[OptionDaily]:
        """获取期权日线数据"""
        try:
            df = self.pro.opt_daily(
                exchange='DCE',
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d')
            )
            return [OptionDaily(**row) for _, row in df.iterrows()]
        except Exception as e:
            logger.error(f"Error fetching option daily data: {e}")
            raise

    async def get_option_daily_by_code(self, ts_code: str, start_date: str, end_date: str) -> List[OptionDaily]:
        """获取指定期权的日线数据"""
        try:
            df = self.pro.opt_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            return [OptionDaily(**row) for _, row in df.iterrows()]
        except Exception as e:
            logger.error(f"Error fetching option daily data for {ts_code}: {e}")
            raise 