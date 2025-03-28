export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const API_ENDPOINTS = {
  market: {
    futures: `${API_BASE_URL}/market/futures`,
    etf: `${API_BASE_URL}/market/etf`,
    options: `${API_BASE_URL}/market/options`,
    futuresContracts: `${API_BASE_URL}/market/futures/contracts`,
    futuresInventory: `${API_BASE_URL}/market/futures/inventory`
  },
  analysis: {
    daily: `${API_BASE_URL}/analysis/daily`
  },
  model: {
    predict: `${API_BASE_URL}/model/predict`
  },
  trading: {
    options: `${API_BASE_URL}/trading/options`,
    generateStrategy: `${API_BASE_URL}/trading/generate-strategy`
  }
}; 