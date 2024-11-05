import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  fetchFuturesBasic, 
  fetchFuturesData as apiFetchFuturesData,
  syncFuturesData as apiSyncFuturesData
} from '@/api/futures'

export const useFuturesStore = defineStore('futures', () => {
  // 状态
  const contracts = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdated = ref(null)
  const contractsCache = ref({})

  // 计算属性
  const getContractsByMarket = computed(() => (market) => {
    return contractsCache.value[market] || []
  })

  // 加载合约基础信息
  const loadContracts = async (exchange) => {
    // 如果缓存中已有数据且未过期（比如1小时内），直接返回
    if (contractsCache.value[exchange] && 
        lastUpdated.value && 
        Date.now() - lastUpdated.value < 3600000) {
      contracts.value = contractsCache.value[exchange]
      return
    }

    loading.value = true
    error.value = null
    
    try {
      const response = await fetchFuturesBasic({ exchange })
      if (response.success) {
        const formattedContracts = response.data.map(item => ({
          code: item.ts_code,
          name: item.name,
          symbol: item.symbol,
          exchange: item.exchange,
          category: mapContractCategory(item.fut_code), // 根据合约代码映射品种
          multiplier: item.multiplier,
          tradeUnit: item.trade_unit,
          quoteUnit: item.quote_unit,
          listDate: item.list_date,
          delistDate: item.delist_date
        }))
        
        // 更新缓存
        contractsCache.value[exchange] = formattedContracts
        contracts.value = formattedContracts
        lastUpdated.value = Date.now()
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 根据合约代码映射品种类别
  const mapContractCategory = (futCode) => {
    // 这里根据实际情况补充映射规则
    const categoryMap = {
      'IF': 'stock_index', // 沪深300股指期货
      'IC': 'stock_index', // 中证500股指期货
      'IH': 'stock_index', // 上证50股指期货
      'IM': 'stock_index', // 中证1000股指期货
      'T': 'bond',  // 国债期货
      'TF': 'bond', // 5年期国债期货
      'TS': 'bond', // 2年期国债期货
      'AU': 'metal', // 黄金期货
      'AG': 'metal', // 白银期货
      'CU': 'metal', // 铜期货
      'AL': 'metal', // 铝期货
      'M': 'agriculture', // 豆粕期货
      'Y': 'agriculture', // 豆油期货
      'P': 'agriculture', // 棕榈油期货
      'I': 'commodity', // 铁矿期货
      'RB': 'commodity', // 螺纹钢期货
      'SC': 'energy', // 原油期货
      'LU': 'energy', // 低硫燃料油期货
      // ... 可以继续添加更多品种映射
    }
    
    // 提取合约代码的字母部分作为品种代码
    const productCode = futCode.match(/[A-Z]+/)?.[0]
    return categoryMap[productCode] || 'other'
  }

  // 获取期货数据
  const getFuturesData = async (params) => {
    console.log('Store getFuturesData called with:', params);
    try {
      const response = await apiFetchFuturesData({
        code: params.code,
        granularity: params.granularity,
        startDate: params.startDate,
        endDate: params.endDate
      });
      
      if (response.success) {
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to fetch futures data');
      }
    } catch (err) {
      console.error('Store getFuturesData error:', err);
      error.value = err.message;
      throw err;
    }
  };

  // 同步数据
  const syncData = async (code) => {
    try {
      const response = await apiSyncFuturesData(code)
      if (!response.success) {
        throw new Error(response.error || 'Failed to sync futures data')
      }
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // 返回所有需要暴露的状态和方法
  return {
    // 状态
    contracts,
    loading,
    error,
    // 计算属性
    getContractsByMarket,
    // 方法
    loadContracts,
    getFuturesData,  // 确保这里导出了方法
    syncData
  }
}) 