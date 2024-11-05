/**
 * 格式化数字为带千分位的字符串
 * @param {number} num 
 * @returns {string}
 */
export const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return num.toLocaleString()
}

/**
 * 格式化百分比
 * @param {number} num 
 * @param {number} digits 小数位数
 * @returns {string}
 */
export const formatPercent = (num, digits = 2) => {
  if (num === null || num === undefined) return '-'
  return `${(num * 100).toFixed(digits)}%`
}

/**
 * 格式化价格
 * @param {number} price 
 * @param {number} digits 小数位数
 * @returns {string}
 */
export const formatPrice = (price, digits = 2) => {
  if (price === null || price === undefined) return '-'
  return price.toFixed(digits)
}

/**
 * 格式化大数字（万、亿）
 * @param {number} num 
 * @returns {string}
 */
export const formatLargeNumber = (num) => {
  if (num === null || num === undefined) return '-'
  
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿'
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toLocaleString()
} 