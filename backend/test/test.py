import akshare as ak

futures_zh_spot_df = ak.futures_zh_spot(symbol='M2601', market="CF", adjust='0')
print(futures_zh_spot_df)

futures_zh_realtime_df = ak.futures_zh_realtime(symbol="豆粕")
print(futures_zh_realtime_df)