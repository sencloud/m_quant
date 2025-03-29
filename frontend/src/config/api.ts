export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const API_ENDPOINTS = {
  market: {
    futures: `${API_BASE_URL}/market/futures`,
    etf: `${API_BASE_URL}/market/etf`,
    options: `${API_BASE_URL}/market/options`,
    futuresContracts: `${API_BASE_URL}/market/futures/contracts`,
    futuresInventory: `${API_BASE_URL}/market/futures/inventory`,
    inventory: `${API_BASE_URL}/market/inventory`,
    technical: `${API_BASE_URL}/market/technical`
  },
  analysis: {
    daily: `${API_BASE_URL}/analysis/daily`,
    fundamental: `${API_BASE_URL}/fundamental/analysis`,
    supplyDemand: `${API_BASE_URL}/fundamental/supply-demand`,
    seasonal: `${API_BASE_URL}/fundamental/seasonal`,
    weather: `${API_BASE_URL}/fundamental/weather`,
    crushProfit: `${API_BASE_URL}/fundamental/crush-profit`,
    overall: `${API_BASE_URL}/fundamental/overall`
  },
  model: {
    predict: `${API_BASE_URL}/model/predict`
  },
  trading: {
    options: `${API_BASE_URL}/trading/options`,
    generateStrategy: `${API_BASE_URL}/trading/generate-strategy`
  }
}; 