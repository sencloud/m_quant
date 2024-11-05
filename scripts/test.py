import tushare as ts

# Initialize Tushare with your token
ts.set_token('')
pro = ts.pro_api()

# df = pro.fut_basic(exchange='DCE', fut_type='1', fields='ts_code,symbol,name,list_date,delist_date')
# print(df)
# df = pro.fut_mapping(ts_code='RB.XSGE')
# print(df)

df = pro.df = pro.ft_mins(ts_code='CU2501.SHF', freq='1min', start_date='2024-09-25 09:00:00', end_date='2024-09-25 10:00:00')
print(df)
