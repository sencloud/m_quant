import dayjs from 'dayjs'

/**
 * 格式化日期
 * @param {string|Date} date 
 * @param {string} format 
 * @returns {string}
 */
export const formatDate = (date, format = 'YYYY-MM-DD') => {
  if (!date) return '-'
  return dayjs(date).format(format)
}

/**
 * 格式化日期时间
 * @param {string|Date} date 
 * @returns {string}
 */
export const formatDateTime = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 获取当前日期
 * @param {string} format 
 * @returns {string}
 */
export const getCurrentDate = (format = 'YYYY-MM-DD') => {
  return dayjs().format(format)
}

/**
 * 获取过去N天的日期
 * @param {number} days 
 * @param {string} format 
 * @returns {string}
 */
export const getPastDate = (days, format = 'YYYY-MM-DD') => {
  return dayjs().subtract(days, 'day').format(format)
}

/**
 * 判断日期是否有效
 * @param {string|Date} date 
 * @returns {boolean}
 */
export const isValidDate = (date) => {
  return dayjs(date).isValid()
}

/**
 * 计算两个日期之间的天数
 * @param {string|Date} date1 
 * @param {string|Date} date2 
 * @returns {number}
 */
export const getDaysDiff = (date1, date2) => {
  return dayjs(date2).diff(dayjs(date1), 'day')
} 