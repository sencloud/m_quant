export const calculateBasis = (spotPrice, futuresPrice) => {
  return futuresPrice - spotPrice
}

export const calculateBasisRate = (spotPrice, futuresPrice) => {
  return (futuresPrice - spotPrice) / spotPrice * 100
}

export const calculateContango = (nearFuturesPrice, farFuturesPrice, daysSpread) => {
  const annualRate = Math.log(farFuturesPrice / nearFuturesPrice) * 365 / daysSpread
  return annualRate * 100
}

export const calculateOIChange = (data) => {
  const absolute = []
  const percentage = []
  
  for (let i = 1; i < data.length; i++) {
    const change = data[i].openInterest - data[i-1].openInterest
    const changeRate = change / data[i-1].openInterest * 100
    
    absolute.push(change)
    percentage.push(changeRate)
  }
  
  return { absolute, percentage }
}

export const calculateSettlementPrice = (high, low, close) => {
  return (high + low + close * 2) / 4
} 