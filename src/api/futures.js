import { http } from '@/utils/http'

export const fetchContracts = (market) => {
  return http.get(`/api/futures/contracts`, {
    params: { market }
  })
}

export const fetchFuturesData = (params) => {
  return http.get(`/api/futures/${params.code}/kline`, {
    params: {
      granularity: params.granularity,
      startDate: params.startDate.toISOString(),
      endDate: params.endDate.toISOString()
    }
  })
}

export const syncFuturesData = () => {
  return http.post('/api/futures/sync')
}

export const getFuturesInfo = (code) => {
  return http.get(`/api/futures/${code}`)
}

// Get basic information for futures contracts with optional filters
export const fetchFuturesBasic = (params) => {
  return http.get('/api/futures/basic', {
    params: {
      exchange: params.exchange,
      futType: params.futType,
      futCode: params.futCode
    }
  })
}

// Get daily data for a specific futures contract
export const fetchFuturesDailyData = (params) => {
  return http.get(`/api/futures/${params.tsCode}/daily`, {
    params: {
      startDate: params.startDate?.toISOString(),
      endDate: params.endDate?.toISOString(),
      tradeDate: params.tradeDate
    }
  })
}

// Get minute-level data for a specific futures contract
export const fetchFuturesMinuteData = (params) => {
  return http.get(`/api/futures/${params.tsCode}/minutes`, {
    params: {
      freq: params.freq, // 1min/5min/15min/30min/60min
      startDate: params.startDate?.toISOString(),
      endDate: params.endDate?.toISOString()
    }
  })
}

// Get continuous contract mapping data
export const fetchFuturesMapping = (params) => {
  return http.get(`/api/futures/mapping`, {
    params: {
      tsCode: params.tsCode,
      startDate: params.startDate?.toISOString(),
      endDate: params.endDate?.toISOString(),
      tradeDate: params.tradeDate
    }
  })
}

export const getFuturesCategories = () => {
  return http.get('/api/futures/categories')
} 