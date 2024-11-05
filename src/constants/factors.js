export const fundamentalFactors = [
  { code: 'pe', name: '市盈率', description: '每股市价为每股收益的倍数', isHigherBetter: false },
  { code: 'pe_ttm', name: '市盈率(TTM)', description: '每股市价为每股收益的倍数(TTM)', isHigherBetter: false },
  { code: 'pb', name: '市净率', description: '每股市价与每股净资产的比率', isHigherBetter: false },
  { code: 'ps_ttm', name: '市销率(TTM)', description: '每股市价为每股销售收入的倍数', isHigherBetter: false },
  { code: 'dv_ttm', name: '股息率(TTM)', description: '每股股息与股票价格的比率', isHigherBetter: true },
  { code: 'total_mv', name: '总市值', description: '股票总市值', isHigherBetter: null }
]

export const technicalFactors = [
  { code: 'ma5', name: '5日均线', description: '5日移动平均线', isHigherBetter: null },
  { code: 'ma10', name: '10日均线', description: '10日移动平均线', isHigherBetter: null },
  { code: 'ma20', name: '20日均线', description: '20日移动平均线', isHigherBetter: null },
  { code: 'macd', name: 'MACD', description: '指数平滑异同移动平均线', isHigherBetter: true },
  { code: 'rsi', name: 'RSI', description: '相对强弱指标', isHigherBetter: null },
  { code: 'volatility', name: '波动率', description: '股价波动的剧烈程度', isHigherBetter: false }
]

export const volumeFactors = [
  { code: 'turnover_rate', name: '换手率', description: '成交量与流通股本的比率', isHigherBetter: null },
  { code: 'volume_ratio', name: '量比', description: '当日成交量与过去5日平均成交量的比值', isHigherBetter: true }
] 