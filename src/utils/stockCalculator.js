export const calculateMA = (days, data) => {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < days - 1) {
      result.push('-')
      continue
    }
    let sum = 0
    for (let j = 0; j < days; j++) {
      sum += data[i - j].close
    }
    result.push((sum / days).toFixed(2))
  }
  return result
}

export const calculateRSI = (data, period = 14) => {
  const gains = []
  const losses = []
  const result = []

  for (let i = 1; i < period + 1; i++) {
    const change = data[i].close - data[i - 1].close
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? -change : 0)
  }

  let avgGain = gains.reduce((a, b) => a + b) / period
  let avgLoss = losses.reduce((a, b) => a + b) / period

  for (let i = 0; i < period; i++) {
    result.push('-')
  }

  result.push(100 - (100 / (1 + avgGain / avgLoss)))

  for (let i = period + 1; i < data.length; i++) {
    const change = data[i].close - data[i - 1].close
    const gain = change > 0 ? change : 0
    const loss = change < 0 ? -change : 0

    avgGain = ((avgGain * (period - 1)) + gain) / period
    avgLoss = ((avgLoss * (period - 1)) + loss) / period

    result.push(100 - (100 / (1 + avgGain / avgLoss)))
  }

  return result
} 