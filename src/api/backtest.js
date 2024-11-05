import axios from 'axios'
import dayjs from 'dayjs'

export const runBacktest = async (params) => {
  try {
    const response = await axios.post('/api/backtest', {
      strategy: params.strategy,
      stock: params.stock,
      startDate: dayjs(params.dateRange[0]).format('YYYY-MM-DD'),
      endDate: dayjs(params.dateRange[1]).format('YYYY-MM-DD')
    })
    return response.data
  } catch (error) {
    throw error.response?.data?.error || 'Failed to run backtest'
  }
}

export const fetchStocks = async () => {
  try {
    const response = await axios.get('/api/stocks')
    return response.data
  } catch (error) {
    throw error.response?.data?.error || 'Failed to fetch stocks'
  }
}

export const addStock = async (stockSymbol) => {
  try {
    const response = await axios.post('/api/stocks', { symbol: stockSymbol })
    return response.data
  } catch (error) {
    throw error.response?.data?.error || 'Failed to add stock'
  }
}

export const syncStockData = async (stockSymbol, startDate, endDate) => {
  try {
    const response = await axios.post('/api/stocks/sync', {
      symbol: stockSymbol,
      startDate: dayjs(startDate).format('YYYY-MM-DD'),
      endDate: dayjs(endDate).format('YYYY-MM-DD')
    })
    return response.data
  } catch (error) {
    throw error.response?.data?.error || 'Failed to sync stock data'
  }
}

export const fetchAvailableStocks = async () => {
  try {
    const response = await axios.get('/api/stocks/available')
    return response.data.map(stock => ({
      value: stock.symbol,
      label: `${stock.symbol} - ${stock.name}`,
      market: stock.market // 'SH' for Shanghai, 'SZ' for Shenzhen
    }))
  } catch (error) {
    throw error.response?.data?.error || 'Failed to fetch available stocks'
  }
}

export const predictStock = async (params) => {
  console.log('Predict stock params:', params)
  try {
    const response = await axios.post('/api/stock/predict', {
      symbol: params.symbol,
      models: params.models,
      timePeriod: params.timePeriod,
      predictionDate: dayjs(params.predictionDate).format('YYYY-MM-DD')
    })
    return response.data
  } catch (error) {
    console.error('Prediction error:', error)
    throw error.response?.data?.error || 'Failed to predict stock'
  }
}

export const trainStockModel = async (params) => {
  console.log('Train model params:', params)
  try {
    const response = await axios.post('/api/stock/train', {
      symbol: params.symbol,
      models: params.models,
      timePeriod: params.timePeriod,
      predictionDate: dayjs(params.predictionDate).format('YYYY-MM-DD')
    })
    return response.data
  } catch (error) {
    console.error('Training error:', error)
    throw error.response?.data?.error || 'Failed to train model'
  }
}

export const predictStockPrice = async (params) => {
  console.log('Predict stock params:', params)
  try {
    const response = await axios.post('/api/stock/predict', {
      symbol: params.symbol,
      models: params.models,
      timePeriod: params.timePeriod,
      predictionDate: dayjs(params.predictionDate).format('YYYY-MM-DD')
    })
    return response.data
  } catch (error) {
    console.error('Prediction error:', error)
    throw error.response?.data?.error || 'Failed to predict stock'
  }
}
