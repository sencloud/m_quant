import dayjs from 'dayjs'

export const formatPrice = (value) => {
  return value?.toFixed(2) || '0.00'
}

export const formatVolume = (value) => {
  if (!value) return '0'
  
  if (value >= 100000000) {
    return (value / 100000000).toFixed(2) + '亿'
  }
  if (value >= 10000) {
    return (value / 10000).toFixed(2) + '万'
  }
  return value.toLocaleString()
}

export const formatChange = (value) => {
  if (!value) return '0.00%'
  return (value >= 0 ? '+' : '') + value.toFixed(2) + '%'
}

export const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

export const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined) return '-'
  
  if (Math.abs(value) < 0.000001) return '0'
  
  if (Math.abs(value) >= 100000000) {
    return (value / 100000000).toFixed(decimals) + '亿'
  }
  if (Math.abs(value) >= 10000) {
    return (value / 10000).toFixed(decimals) + '万'
  }
  
  return Number(value).toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export const formatPercent = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return (value >= 0 ? '+' : '') + value.toFixed(decimals) + '%'
}

export const formatPriceWithPrecision = (value, precision = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toFixed(precision)
}

export const formatTimestamp = (timestamp, format = 'YYYY-MM-DD HH:mm:ss') => {
  if (!timestamp) return '-'
  return dayjs(timestamp).format(format)
} 