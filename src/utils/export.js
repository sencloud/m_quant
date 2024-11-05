export const exportToCSV = ({
  data,
  filename,
}) => {
  try {
    // 获取所有列名
    const headers = Object.keys(data[0])
    
    // 创建 CSV 内容
    const csvContent = [
      // 添加表头
      headers.join(','),
      // 添加数据行
      ...data.map(row => 
        headers.map(header => 
          // 处理包含逗号的内容
          typeof row[header] === 'string' && row[header].includes(',') 
            ? `"${row[header]}"`
            : row[header]
        ).join(',')
      )
    ].join('\n')
    
    // 创建 Blob
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    
    // 创建下载链接
    const link = document.createElement('a')
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `${filename}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    return true
  } catch (error) {
    console.error('Export failed:', error)
    throw error
  }
} 