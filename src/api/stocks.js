import { http } from '@/utils/http'

export const fetchStocks = () => {
  return http.get('/api/stocks')
}

export const fetchStockData = (params) => {
  return http.get(`/api/stocks/${params.code}/kline`, { params })
}

export const addStock = (stockData) => {
  return http.post('/api/stocks', stockData)
}

export const removeStock = (code) => {
  return http.delete(`/api/stocks/${code}`)
}

export const updateStockNotes = (code, notes) => {
  return http.patch(`/api/stocks/${code}/notes`, { notes })
}

export const syncStockData = (params) => {
  return http.post('/api/stocks/sync', params)
}

export const fetchAvailableStocks = () => {
  return http.get('/api/stocks/available')
}

export const addGroup = (groupData) => {
  return http.post('/api/groups', groupData)
}

/**
 * 应用因子筛选
 * @param {Object} params
 * @param {Object} params.factors - 选中的因子 { fundamental: [], technical: [], volume: [] }
 * @param {Object} params.weights - 因子权重 { factor_code: weight }
 * @returns {Promise}
 */
export const applyFactorFilter = (params) => {
  return http.post('/api/stocks/filter/factors', params)
} 