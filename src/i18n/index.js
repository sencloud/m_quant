import { comma } from 'postcss/lib/list'
import { createI18n } from 'vue-i18n'

const messages = {
  en: {
    nav: {
      home: 'Home',
      backtest: 'Backtest',
      stocks: 'Stocks',
      trading: 'Trading',
      ai: 'AI Prediction',
      blog: 'Blog',
      about: 'About'
    },
    common: {
      cancel: 'Cancel',
      updated: 'Updated',
      uses: 'Uses',
      favorite: 'Add to Favorites',
      unfavorite: 'Remove from Favorites',
      tryNow: 'Try Now',
      viewMore: 'View More',
      startDate: 'Start Date',
      endDate: 'End Date',
      nextWeek: 'Next Week',
      nextMonth: 'Next Month',
      next3Months: 'Next 3 Months',
      strategies: 'Strategies'
    },
    home: {
      title: 'Singz Quantitative',
      subtitle: 'Professional-grade stock backtesting platform with multiple strategies, real-time visualization, and comprehensive performance analysis.',
      strategies: {
        shortTerm: {
          name: 'Short-term MA Cross',
          description: '5-day and 10-day moving average crossover strategy'
        },
        mediumTerm: {
          name: 'Medium-term Trend',
          description: '20-day and 60-day moving average trend following'
        },
        longTerm: {
          name: 'Quarterly Strategy',
          description: 'Long-term quarterly trend following strategy'
        },
        tryStrategy: 'Try Strategy',
        tags: {
          trend: 'Trend',
          momentum: 'Momentum',
          value: 'Value',
          volatility: 'Volatility',
          mean_reversion: 'Mean Reversion',
          arbitrage: 'Arbitrage',
          ml: 'Machine Learning',
          fundamental: 'Fundamental'
        }
      },
      favorites: 'My Favorites',
      categories: 'Browse by Category',
      allStrategies: 'All Strategies'
    },
    calendar: {
      today: 'Today',
      week: {
        sun: 'Sun',
        mon: 'Mon',
        tue: 'Tue',
        wed: 'Wed',
        thu: 'Thu',
        fri: 'Fri',
        sat: 'Sat'
      },
      month: {
        jan: 'Jan',
        feb: 'Feb',
        mar: 'Mar',
        apr: 'Apr',
        may: 'May',
        jun: 'Jun',
        jul: 'Jul',
        aug: 'Aug',
        sep: 'Sep',
        oct: 'Oct',
        nov: 'Nov',
        dec: 'Dec'
      },
      range: {
        separator: 'to',
        startDate: 'Start Date',
        endDate: 'End Date'
      }
    },
    stocks: {
      title: 'Stock Data',
      selectStock: 'Select Stock',
      noData: 'No data available',
      error: {
        loadFailed: 'Failed to load stock data',
        loadStocks: 'Failed to load stocks'
      },
      granularity: {
        minute: 'Minute',
        hour: 'Hour',
        day: 'Day',
        week: 'Week',
        month: 'Month',
        year: 'Year'
      },
      selectDate: 'Select Date',
      selectWeek: 'Select Week',
      selectMonth: 'Select Month',
      selectYear: 'Select Year',
      week: 'Week',
      actions: {
        sync: 'Sync Data',
        addStock: 'Add Stock'
      },
      syncDataDialog: {
        cancel: 'Cancel',
        title: 'Sync Stock Data',
        dateRange: 'Date Range',
        confirm: 'Sync Now',
        success: 'Data synchronized successfully',
        error: 'Failed to synchronize data',
        selectDateRange: 'Please select a date range'
      },
      addStockDialog: {
        title: 'Add New Stock',
        selectMarket: 'Select Market',
        selectStock: 'Select Stock',
        search: 'Search stocks...',
        code: 'Stock Code',
        name: 'Name',
        area: 'Area',
        industry: 'Industry',
        add: 'Add',
        success: 'Stock added successfully',
        error: 'Failed to add stock',
        loadError: 'Failed to load available stocks'
      },
      table: {
        date: 'Date',
        open: 'Open',
        high: 'High',
        low: 'Low',
        close: 'Close',
        volume: 'Volume',
        change: 'Change %'
      },
      chart: {
        kline: 'K-Line',
        ma: 'MA',
        price: 'Price',
        open: 'Open',
        close: 'Close',
        high: 'High',
        low: 'Low',
        volume: 'Volume'
      },
      exchanges: {
        sh: 'Shanghai Stock Exchange',
        sz: 'Shenzhen Stock Exchange',
        bj: 'Beijing Stock Exchange'
      },
      tabs: {
        pool: 'Trading Pool',
        stocks: 'Stock Data',
        futures: 'Futures Data'
      },
      pool: {
        title: 'Trading Pool Management',
        table: {
          code: 'Code',
          name: 'Name',
          industry: 'Industry',
          score: 'Score',
          actions: 'Actions',
          price: 'Price',
          change: 'Change',
          volume: 'Volume',
          turnover: 'Turnover',
          pe: 'P/E',
          pb: 'P/B',
          total_mv: 'Market Cap',
          notes: 'Notes',
          lastUpdate: 'Last Update',
          status: 'Status',
          view: 'View',
          edit: 'Edit',
          remove: 'Remove'
        },
        actions: {
          view: 'View Details',
          edit: 'Edit Notes',
          remove: 'Remove from Pool',
          removeConfirm: 'Are you sure you want to remove this stock?',
          removeSuccess: 'Successfully removed',
          removeError: 'Failed to remove'
        },
      },
      futures: {
        title: 'Futures Analysis',
        market: 'Exchange',
        contract: 'Contract',
        period: 'Period',
        dateRange: 'Date Range',
        sync: 'Sync Data',
        export: 'Export',
        indicators: 'Indicators',
        maLines: 'MA Lines',
        
        // Contract Info
        contractInfo: 'Contract Information',
        code: 'Code',
        name: 'Name',
        underlying: 'Underlying',
        multiplier: 'Contract Multiplier',
        lastTradeDate: 'Last Trading Date',
        deliveryDate: 'Delivery Date',
        margin: 'Margin Rate',
        unit: 'Trading Unit',
        
        // Price & Volume
        price: 'Price',
        open: 'Open',
        high: 'High',
        low: 'Low',
        close: 'Close',
        settle: 'Settlement',
        preClose: 'Previous Close',
        preSettle: 'Previous Settlement',
        volume: 'Volume',
        amount: 'Amount',
        openInterest: 'Open Interest',
        priceChange: 'Change',
        
        // Time Periods
        minutes: 'Minutes',
        hours: 'Hours',
        daily: 'Daily',
        min1: '1 Min',
        min5: '5 Min',
        min15: '15 Min',
        min30: '30 Min',
        hour1: '1 Hour',
        day: 'Daily',
        
        // Views
        kline: 'K-Line',
        timeline: 'Timeline',
        depth: 'Market Depth',
        trades: 'Recent Trades',
        
        // Markets
        exchanges: {
          CFFEX: 'China Financial Futures Exchange',
          SHFE: 'Shanghai Futures Exchange',
          DCE: 'Dalian Commodity Exchange',
          CZCE: 'Zhengzhou Commodity Exchange',
          INE: 'Shanghai International Energy Exchange'
        },
        
        // Categories
        categories: {
          commodity: 'Commodity Futures',
          financial: 'Financial Futures',
          stock_index: 'Stock Index Futures',
          bond: 'Bond Futures',
          currency: 'Currency Futures',
          energy: 'Energy Futures',
          metal: 'Metal Futures',
          agriculture: 'Agricultural Futures'
        },
        
        // Messages
        loadError: 'Failed to load futures data',
        syncSuccess: 'Data synchronization successful',
        syncError: 'Data synchronization failed',
        exportSuccess: 'Export successful',
        exportError: 'Export failed',
        noData: 'No data available',
        loadContractsError: 'Failed to load contracts',
        initError: 'Initialization failed',
        
        // Table Views
        normalView: 'Basic View',
        technicalView: 'Technical View',
        tradeData: 'Trading Data',
        
        // Technical Indicators
        technical: {
          ma: 'Moving Average',
          ema: 'Exponential MA',
          macd: 'MACD',
          kdj: 'KDJ',
          rsi: 'RSI',
          boll: 'Bollinger Bands',
          volume: 'Volume',
          openInterest: 'Open Interest'
        }
      },
      pool: {
        title: 'Stock Pool',
        search: 'Search stocks by code or name',
        addToPool: 'Add Stock',
        addGroup: 'Add Group',
        noNotes: 'No notes',
        view: 'View Details',
        editNotes: 'Edit Notes',
        remove: 'Remove',

        // Factor analysis
        factors: {
          title: 'Factor Analysis',
          apply: 'Apply Filter',
          reset: 'Reset',
          filterSuccess: 'Factor filtering successful',
          filterError: 'Factor filtering failed',
          weightTip: 'Adjust weight (0-100)',

          // Factor categories
          fundamental: 'Fundamental Factors',
          technical: 'Technical Factors',
          volume: 'Volume Factors',
          sentiment: 'Market Sentiment',
          macro: 'Macro Factors',

          // Preset combinations
          presets: {
            title: 'Common Combinations:',
            value: 'Value',
            growth: 'Growth',
            momentum: 'Momentum',
            quality: 'Quality'
          },

          // Factor descriptions
          descriptions: {
            pe: 'Price-to-Earnings Ratio: Measures stock valuation',
            pb: 'Price-to-Book Ratio: Compares market value to book value',
            roe: 'Return on Equity: Measures profitability efficiency',
            eps_growth: 'EPS Growth Rate: Earnings growth year-over-year',
            ma: 'Moving Average: Price trend indicator',
            rsi: 'Relative Strength Index: Overbought/oversold indicator',
            macd: 'MACD: Trend and momentum indicator',
            vol_ratio: 'Volume Ratio: Current vs 5-day average volume',
            turnover: 'Turnover Rate: Trading activity indicator',
            vol_change: 'Volume Change: Daily volume change rate'
          },

          items: {
            // Fundamental factors
            pe: 'P/E Ratio',
            pe_ttm: 'P/E Ratio(TTM)',
            pb: 'P/B Ratio',
            ps_ttm: 'P/S Ratio(TTM)',
            dv_ttm: 'Dividend Yield(TTM)',
            total_mv: 'Market Cap',
            roe: 'ROE',
            eps_growth: 'EPS Growth',

            // Technical factors
            ma5: '5-day MA',
            ma10: '10-day MA',
            ma20: '20-day MA',
            macd: 'MACD',
            rsi: 'RSI',
            volatility: 'Volatility',

            // Volume factors
            turnover_rate: 'Turnover Rate',
            volume_ratio: 'Volume Ratio',
            volume_ma5: '5-day Volume MA',
            volume_ma20: '20-day Volume MA'
          },

          groups: {
            fundamental: 'Fundamental',
            technical: 'Technical',
            volume: 'Volume'
          }
        },

        table: {
          code: 'Code',
          name: 'Name',
          group: 'Group',
          latestPrice: 'Latest Price',
          change: 'Change',
          notes: 'Notes',
          addedDate: 'Added Date',
          lastUpdated: 'Last Updated',
          actions: 'Actions'
        }
      }
    },
    backtest: {
      title: 'Strategy Configuration',
      form: {
        // Basic settings
        strategy: 'Strategy',
        stock: 'Stock',
        dateRange: 'Date Range',
        startDate: 'Start Date',
        endDate: 'End Date',
        runBacktest: 'Run Backtest',
        
        // Backtest settings sections
        settings: 'Backtest Settings',
        capitalAndFees: 'Capital & Fees',
        initialCapital: 'Initial Capital',
        commission: 'Commission Rate',
        slippage: 'Slippage',
        
        // Position settings
        position: {
          title: 'Position Settings',
          sizeType: 'Position Size Type',
          fixedSize: 'Fixed Size',
          percentageSize: 'Percentage of Capital',
          size: 'Position Size',
        },
        
        // Risk management settings
        risk: {
          title: 'Risk Management',
          stopLoss: 'Stop Loss (%)',
          takeProfit: 'Take Profit (%)',
          trailingStop: 'Trailing Stop (%)'
        }
      },
      strategies: {
        shortTerm: 'Short Term MA Cross',
        mediumTerm: 'Medium Term MA Cross',
        longTerm: 'Long Term Quarterly'
      },
      validation: {
        selectStrategy: 'Please select a strategy',
        selectStock: 'Please select a stock',
        selectDateRange: 'Please select a date range',
        initialCapital: 'Please enter initial capital',
        commission: 'Commission rate must be between 0 and 1',
        slippage: 'Slippage must be between 0 and 1',
        positionSize: 'Please enter position size',
        stopLoss: 'Stop loss must be between 0 and 100',
        takeProfit: 'Take profit must be between 0 and 100',
        trailingStop: 'Trailing stop must be between 0 and 100'
      },
      error: {
        failed: 'Failed to run backtest',
        validation: 'Please fill in all required fields',
        loadStocks: 'Failed to load stocks'
      },
      results: {
        performance: 'Performance Summary',
        metrics: {
          totalReturn: 'Total Return',
          winRate: 'Win Rate',
          sharpeRatio: 'Sharpe Ratio',
          maxDrawdown: 'Max Drawdown',
          profitFactor: 'Profit Factor',
          totalTrades: 'Total Trades',
          wonTrades: 'Won Trades',
          lostTrades: 'Lost Trades',
          avgTrade: 'Average Trade'
        },
        chart: {
          title: 'Price Chart & Signals',
          price: 'Price',
          equity: 'Equity',
          ma5: '5-day MA',
          ma10: '10-day MA',
          ma20: '20-day MA',
          volume: 'Volume',
          buy: 'Buy',
          sell: 'Sell',
          zoomTip: 'Zoom: Mouse wheel or slider'
        },
        trades: {
          title: 'Trade History',
          entryDate: 'Entry Date',
          exitDate: 'Exit Date',
          type: 'Type',
          quantity: 'Quantity',
          entryPrice: 'Entry Price',
          exitPrice: 'Exit Price',
          profit: 'Profit/Loss',
          return: 'Return %',
          status: 'Status',
          long: 'LONG',
          short: 'SHORT',
          open: 'OPEN',
          closed: 'CLOSED'
        }
      }
    },
    trading: {
      simnow: {
        title: 'SimNow Demo Trading',
        account: 'Account',
        password: 'Password',
        description: 'Practice trading in simulation environment'
      },
      live: {
        title: 'Live Trading',
        account: 'Account',
        password: 'Password',
        description: 'Real market trading'
      },
      startButton: 'Start Trading',
      stopButton: 'Stop Trading',
      logs: 'Trading Logs',
      status: {
        connected: 'Connected',
        disconnected: 'Disconnected',
        connecting: 'Connecting...'
      },
      messages: {
        startSuccess: 'Trading started successfully',
        startFailed: 'Failed to start trading',
        stopSuccess: 'Trading stopped successfully',
        stopFailed: 'Failed to stop trading',
        connectionError: 'Connection error'
      }
    },
    ai: {
      title: 'Stock Price Prediction',
      modelConfig: 'Model Configuration',
      stockSymbol: 'Stock Symbol',
      symbolRequired: 'Symbol is required',
      selectModels: 'Select Models',
      trainingPeriod: 'Training Period (days)',
      trainModel: 'Train Model',
      modelMetrics: 'Model Metrics',
      predictionChart: 'Price Prediction Chart',
      backtesting: 'Backtesting Results',
      noMetrics: 'Train a model to see metrics',
      noPredictions: 'Train a model to see predictions',
      noBacktest: 'Run backtest to see results',
      predictionPeriod: 'Prediction Period',
      pleasePredictionRange: 'Please select a prediction range',
      predictions: 'Prediction Results',
      predict: 'Predict',
      chart: {
        actual: 'Actual Price',
        predicted: 'Predicted Price',
        price: 'Price',
        kline: 'K-Line Chart',
        open: 'Open',
        close: 'Close',
        high: 'High',
        low: 'Low',
        volume: 'Volume',
        tooltip: {
          date: 'Date',
          price: 'Price',
          volume: 'Volume'
        },
        ma: 'Moving Average',
        ema: 'EMA',
        indicators: 'Indicators',
        sma5: '5-day MA',
        sma20: '20-day MA',
        ema5: '5-day EMA',
        ema20: '20-day EMA',
        momentum: 'Momentum',
        volatility: 'Volatility',
        returns: 'Returns'
      },
      metrics: {
        mae: 'Mean Absolute Error',
        mse: 'Mean Squared Error',
        rmse: 'Root Mean Square Error',
        r2: 'R² Score',
        predictionAccuracy: 'Prediction Accuracy',
        directionAccuracy: 'Direction Accuracy',
        mape: 'Mean Absolute Percentage Error'
      },
      models: {
        lstm: 'LSTM Neural Network',
        gru: 'GRU Neural Network',
        rnn: 'RNN Neural Network'
      },
      backtest: {
        model: 'Model',
        actual: 'Actual Price',
        predicted: 'Predicted',
        confidence: 'Confidence',
        error: 'Error Rate',
        predictionDate: 'Prediction Date'
      },
      messages: {
        trainingSuccess: 'Model training completed',
        trainingFailed: 'Model training failed',
        predictionSuccess: 'Prediction completed',
        predictionFailed: 'Prediction failed',
        modelNotFound: 'Model not found. Please train the model first.'
      }
    },
    blog: {
      title: 'Latest Articles',
      subtitle: 'Sharing Trading Experience and Market Insights',
      minuteRead: 'min read',
      readMore: 'Read More',
      noArticles: 'No articles available',
      categories: {
        strategy: 'Trading Strategy',
        analysis: 'Market Analysis',
        technology: 'Technical Research',
        tutorial: 'Tutorials'
      },
      tags: {
        quantitative: 'Quantitative Trading',
        ai: 'Artificial Intelligence',
        technical: 'Technical Analysis',
        fundamental: 'Fundamental Analysis',
        risk: 'Risk Management',
        beginner: 'Beginner Guide'
      },
      createNew: 'Create New Post',
      create: {
        title: 'Create New Blog Post',
        titleLabel: 'Title',
        tagsLabel: 'Tags',
        contentLabel: 'Content',
        contentPlaceholder: 'Write your post in Markdown...',
        write: 'Write',
        preview: 'Preview',
        publish: 'Publish'
      }
    },
    about: {
      title: 'About Us',
      introduction: 'Platform Introduction',
      introText: 'We are a comprehensive platform focused on stock market analysis and trading, dedicated to providing professional quantitative trading tools and market insights for investors.',
      features: 'Core Features',
      featureList: [
        'Real-time Stock Data Monitoring and Analysis',
        'AI-Driven Market Predictions',
        'Professional Backtesting System',
        'Diverse Trading Strategies',
        'Complete Risk Management Tools',
        'Rich Learning Resources'
      ],
      contact: 'Contact Us',
      contactText: 'If you have any questions or suggestions, please contact us through:\nEmail: support@example.com\nWorking Hours: Monday-Friday 9:00-18:00'
    },
    categories: {
      trend: 'Trend Following',
      momentum: 'Momentum Trading',
      value: 'Value Investment',
      volatility: 'Volatility Trading',
      mean_reversion: 'Mean Reversion',
      arbitrage: 'Arbitrage Trading',
      ml: 'Machine Learning',
      fundamental: 'Fundamental Analysis'
    },
    tags: {
      trend: 'Trend',
      momentum: 'Momentum',
      value: 'Value',
      volatility: 'Volatility',
      mean_reversion: 'Mean Reversion',
      arbitrage: 'Arbitrage',
      ml: 'ML',
      fundamental: 'Fundamental'
    }
  },
  zh: {
    nav: {
      home: '首页',
      backtest: '回测',
      stocks: '数据',
      trading: '实盘',
      ai: '预测',
      blog: '文章',
      about: '关于'
    },
    common: {
      cancel: '取消',
      updated: '更新于',
      uses: '使用次数',
      favorite: '添加收藏',
      unfavorite: '取消收藏',
      tryNow: '立即试用',
      viewMore: '查看更多',
      startDate: '开始日期',
      endDate: '结束日期',
      nextWeek: '未来一周',
      nextMonth: '未来一个月',
      next3Months: '未来三个月',
      strategies: '个策略'
    },
    home: {
      title: '新致量化',
      subtitle: '专业级股票回测平台，提供多种策略、实时可视化和全面的性能分析。',
      strategies: {
        shortTerm: {
          name: '短期均线交叉',
          description: '5日和10日移动平均线交叉策略'
        },
        mediumTerm: {
          name: '中期趋势',
          description: '20日和60日移动平均线趋势跟踪'
        },
        longTerm: {
          name: '季度策略',
          description: '长期季度趋势跟踪策略'
        },
        tryStrategy: '试用策略',
        tags: {
          trend: '趋势',
          momentum: '动量',
          value: '价值',
          volatility: '波动',
          mean_reversion: '均值回归',
          arbitrage: '套利',
          ml: '机器学习',
          fundamental: '基本面'
        }
      },
      favorites: '我的收藏',
      categories: '分类浏览',
      allStrategies: '所有策略'
    },
    calendar: {
      today: '今天',
      week: {
        sun: '日',
        mon: '一',
        tue: '二',
        wed: '三',
        thu: '四',
        fri: '五',
        sat: '六'
      },
      month: {
        jan: '一月',
        feb: '二月',
        mar: '三月',
        apr: '四月',
        may: '五月',
        jun: '六月',
        jul: '七月',
        aug: '八月',
        sep: '九月',
        oct: '十月',
        nov: '十一月',
        dec: '十二月'
      },
      range: {
        separator: '至',
        startDate: '开始日期',
        endDate: '结束日期'
      }
    },
    stocks: {
      title: '股票数据',
      selectStock: '选择股票',
      noData: '暂无数据',
      error: {
        loadFailed: '加载股票数据失败',
        loadStocks: '加载股票列表失败'
      },
      granularity: {
        minute: '分钟',
        hour: '小时',
        day: '天',
        week: '周',
        month: '月',
        year: '年'
      },
      selectDate: '选择日期',
      selectWeek: '选择周',
      selectMonth: '选择月份',
      selectYear: '选择年份',
      week: '周',
      actions: {
        sync: '同步数据',
        addStock: '添加股票'
      },
      syncDataDialog: {
        cancel: '取消',
        title: '同步股票数据',
        dateRange: '日期范围',
        confirm: '立即同步',
        success: '数据同步成功',
        error: '数据同步失败',
        selectDateRange: '请选择日期范围'
      },
      addStockDialog: {
        title: '添加新股票',
        selectMarket: '选择交易所',
        selectStock: '选择股票',
        search: '搜索股票...',
        code: '股票代码',
        name: '名称',
        area: '地区',
        industry: '行业',
        add: '添加',
        success: '股票添加成功',
        error: '添加股票失败',
        loadError: '加载可用股票列表失败'
      },
      table: {
        date: '日期',
        open: '开盘价',
        high: '最高价',
        low: '最低价',
        close: '收盘价',
        volume: '成交量',
        change: '涨跌幅'
      },
      chart: {
        kline: 'K线图',
        ma: '均线',
        price: '价格',
        open: '开盘价',
        close: '收盘价',
        high: '最高价',
        low: '最低价',
        volume: '成交量'
      },
      exchanges: {
        sh: '上海证券交易所',
        sz: '深圳证券交易所',
        bj: '北京证券交易所'
      },
      tabs: {
        pool: '交易池',
        stocks: '股票数据',
        futures: '期货数据'
      },
      futures: {
        title: '期货分析',
        market: '交易所',
        contract: '合约',
        period: '周期',
        dateRange: '日期范围',
        sync: '同步数据',
        export: '导出',
        indicators: '指标',
        maLines: '均线',
        other: '其他',
        retry: '重试',
        
        // Contract Info
        contractInfo: '合约信息',
        selectContract: '选择合约',
        code: '代码',
        name: '名称',
        underlying: '标的',
        multiplier: '合约乘数',
        lastTradeDate: '最后交易日',
        deliveryDate: '交割日',
        margin: '保证金率',
        unit: '交易单位',
        
        // Price & Volume
        price: '价格',
        open: '开盘价',
        high: '最高价',
        low: '最低价',
        close: '收盘价',
        settle: '结算价',
        preClose: '昨收价',
        preSettle: '昨结算',
        volume: '成交量',
        amount: '成交额',
        openInterest: '持仓量',
        priceChange: '涨跌幅',
        
        // Time Periods
        minutes: '分钟线',
        hours: '小时线',
        daily: '日线',
        min1: '1分钟',
        min5: '5分钟',
        min15: '15分钟',
        min30: '30分钟',
        hour1: '1小时',
        day: '日线',
        
        // Views
        kline: 'K线图',
        timeline: '分时图',
        depth: '深度图',
        trades: '成交记录',
        
        // Markets
        exchanges: {
          CFFEX: '中国金融期货交易所',
          SHFE: '上海期货交易所',
          DCE: '大连商品交易所',
          CZCE: '郑州商品交易所',
          INE: '上海国际能源交易中心'
        },
        
        // Categories
        categories: {
          commodity: '商品期货',
          financial: '金融期货',
          stock_index: '股指期货',
          bond: '国债期货',
          currency: '货币期货',
          energy: '能源期货',
          metal: '金属期货',
          agriculture: '农产品期货',
          other: '其他'
        },
        
        // Messages
        loadError: '加载期货数据失败',
        syncSuccess: '数据同步成功',
        syncError: '数据同步失败',
        exportSuccess: '导出成功',
        exportError: '导出失败',
        noData: '暂无数据',
        loadContractsError: '加载合约列表失败',
        initError: '初始化失败',
        
        // Table Views
        normalView: '基础视图',
        technicalView: '技术视图',
        tradeData: '交易数据',
        
        // Technical Indicators
        technical: {
          ma: '移动平均线',
          ema: '指数移动平均',
          macd: 'MACD指标',
          kdj: 'KDJ指标',
          rsi: '相对强弱指标',
          boll: '布林带',
          volume: '成交量',
          openInterest: '持仓量'
        }
      },
      pool: {
        title: '交易池管理',
        search: '搜索股票代码或名称',
        addToPool: '添加股票',
        addGroup: '添加分组',
        noNotes: '暂无备注',
        view: '查看详情',
        editNotes: '编辑备注',
        remove: '移除',

        // 因子分析
        factors: {
          title: '因子分析',
          apply: '应用筛选',
          reset: '重置',
          filterSuccess: '因子筛选成功',
          filterError: '因子筛选失败',
          weightTip: '调整权重 (0-100)',

          // 因子分类
          fundamental: '基本面因子',
          technical: '技术面因子',
          volume: '成交量因子',
          sentiment: '市场情绪',
          macro: '宏观因子',

          // 预设组合
          presets: {
            title: '常用组合：',
            value: '价值型',
            growth: '成长型',
            momentum: '动量型',
            quality: '质量型'
          },

          // 因子描述
          descriptions: {
            pe: '市盈率：衡量股票估值水平',
            pb: '市净率：市值与账面价值的比较',
            roe: '净资产收益率：衡量公司利润效率',
            eps_growth: 'EPS增长率：每股收益同比增长',
            ma: '移动平均线：价格趋势指标',
            rsi: '相对强弱指标：超买超卖判断',
            macd: 'MACD指标：趋势和动量指标',
            vol_ratio: '量比：当日与5日平均成交量比值',
            turnover: '换手率：交易活跃度指标',
            vol_change: '成交量变化率：日成交量变化'
          },

          items: {
            // Fundamental factors
            pe: '市盈率',
            pe_ttm: '市盈率(TTM)',
            pb: '市净率',
            ps_ttm: '市销率(TTM)',
            dv_ttm: '股息率(TTM)',
            total_mv: '总市值（亿）',
            roe: '净资产收益率',
            eps_growth: 'EPS增长率',

            // Technical factors
            ma5: '5日均线',
            ma10: '10日均线',
            ma20: '20日均线',
            macd: 'MACD',
            rsi: 'RSI',
            volatility: '波动率',

            // Volume factors
            turnover_rate: '换手率',
            volume_ratio: '量比',
            volume_ma5: '5日成交量均线',
            volume_ma20: '20日成交量均线'
          },

          groups: {
            fundamental: '基本面因子',
            technical: '技术面因子',
            volume: '成交量因子'
          }
        },
        actions: {
          view: '查看详情',
          edit: '编辑笔记',
          remove: '从池中移除',
          removeConfirm: '确定要移除该股票吗？',
          removeSuccess: '已成功移除',
          removeError: '移除失败'
        },
        table: {
          code: '代码',
          name: '名称',
          industry: '所属行业',
          score: '综合评分',
          actions: '操作',
          price: '最新价',
          change: '涨跌幅',
          volume: '成交量',
          turnover: '换手率',
          pe: '市盈率',
          pb: '市净率',
          total_mv: '总市值',
          notes: '备注',
          lastUpdate: '更新时间',
          status: '状态',
          view: '查看',
          edit: '编辑',
          remove: '移除'
        },
      }
    },
    backtest: {
      title: '策略配置',
      form: {
        // Basic settings
        strategy: '策略',
        stock: '股票',
        dateRange: '日期范围',
        startDate: '开始日期',
        endDate: '结束日期',
        runBacktest: '运行回测',
        
        // Backtest settings sections
        settings: '回测设置',
        capitalAndFees: '资金和费用',
        initialCapital: '初始资金',
        commission: '手续费率',
        slippage: '滑点',
        
        // Position settings
        position: {
          title: '仓位设置',
          sizeType: '仓位大小类型',
          fixedSize: '固定数量',
          percentageSize: '资金比例',
          size: '仓位大小',
        },
        
        // Risk management settings
        risk: {
          title: '风险管理',
          stopLoss: '止损比例 (%)',
          takeProfit: '止盈比例 (%)',
          trailingStop: '追踪止损 (%)'
        }
      },
      strategies: {
        shortTerm: '短期均线交叉',
        mediumTerm: '中期均线交叉',
        longTerm: '长期季度策略'
      },
      validation: {
        selectStrategy: '请选择策略',
        selectStock: '请选择股票',
        selectDateRange: '请选择日期范围',
        initialCapital: '请输入初始资金',
        commission: '手续费率必须在0到1之间',
        slippage: '滑点必须在0到1之间',
        positionSize: '请输入仓位大小',
        stopLoss: '止损比例必须在0到100之间',
        takeProfit: '止盈比例必须在0到100之间',
        trailingStop: '追踪止损必须在0到100之间'
      },
      error: {
        failed: '回测运行失败',
        validation: '请填写所有必填字段',
        loadStocks: '加载股票列表失败'
      },
      results: {
        performance: '绩效总结',
        metrics: {
          totalReturn: '总收益',
          winRate: '胜率',
          sharpeRatio: '夏普比率',
          maxDrawdown: '最大回撤',
          profitFactor: '盈亏比',
          totalTrades: '总交易次数',
          wonTrades: '盈利交易',
          lostTrades: '亏损交易',
          avgTrade: '平均收益'
        },
        chart: {
          title: '价格图表与信号',
          price: '价格',
          equity: '权益',
          ma5: '5日均线',
          ma10: '10日均线',
          ma20: '20日均线',
          volume: '成交量',
          buy: '买入',
          sell: '卖出',
          zoomTip: '缩放：鼠标滚轮或滑块'
        },
        trades: {
          title: '交易历史',
          entryDate: '入场日期',
          exitDate: '出场日期',
          type: '类型',
          quantity: '数量',
          entryPrice: '入场价格',
          exitPrice: '出场价格',
          profit: '盈亏',
          return: '收益率',
          status: '状态',
          long: '做多',
          short: '做空',
          open: '持仓中',
          closed: '已平仓'
        }
      }
    },
    trading: {
      simnow: {
        title: 'SimNow模拟交易',
        account: '账号',
        password: '密码',
        description: '在模拟环境中练习交易'
      },
      live: {
        title: '实盘交易',
        account: '账号',
        password: '密码',
        description: '真实市场交易'
      },
      startButton: '开始交易',
      stopButton: '停止交易',
      logs: '交易日志',
      status: {
        connected: '已连接',
        disconnected: '未连接',
        connecting: '连接中...'
      },
      messages: {
        startSuccess: '交易启动成功',
        startFailed: '交易启动失败',
        stopSuccess: '交易已停止',
        stopFailed: '停止交易失败',
        connectionError: '连接错误'
      }
    },
    ai: {
      title: '股票价格预测',
      modelConfig: '模型配置',
      stockSymbol: '股票代码',
      symbolRequired: '请输入股票代码',
      selectModels: '选择模型',
      trainingPeriod: '训练周期（天）',
      trainModel: '训练模型',
      modelMetrics: '模型评估指标',
      predictionChart: '价格预测图表',
      backtesting: '回测结果',
      noMetrics: '暂无评估指标',
      noPredictions: '暂无预测数据',
      noBacktest: '运行模型后查看回测结果',
      predictionPeriod: '预测时间',
      pleasePredictionRange: '请选择预测时间',
      predictions: '预测结果',
      predict: '预测收盘价',
      chart: {
        actual: '实际价格',
        predicted: '预测价格',
        price: '价格',
        kline: 'K线图',
        open: '开盘价',
        close: '收盘价',
        high: '最高价',
        low: '最低价',
        volume: '成交量',
        tooltip: {
          date: '日期',
          price: '价格',
          volume: '成交量'
        },
        ma: '移动平均线',
        ema: '指数移动平均',
        indicators: '技术指标',
        sma5: '5日均线',
        sma20: '20日均线',
        ema5: '5日EMA',
        ema20: '20日EMA',
        momentum: '动量',
        volatility: '波动率',
        returns: '收益率'
      },
      metrics: {
        mae: '平均绝对误差',
        mse: '均方误差',
        rmse: '均方根误差',
        r2: 'R²评分',
        predictionAccuracy: '预测准确度',
        directionAccuracy: '方向准确率',
        mape: '平均绝对百分比误差'
      },
      models: {
        lstm: 'LSTM神经网络',
        gru: 'GRU神经网络',
        rnn: 'RNN神经网络'
      },
      backtest: {
        model: '模型',
        actual: '实际价格',
        predicted: '预测价格',
        confidence: '置信度',
        error: '误差率',
        predictionDate: '预测日期'
      },
      messages: {
        trainingSuccess: '模型训练完成',
        trainingFailed: '模型训练失败',
        predictionSuccess: '预测完成',
        predictionFailed: '预测失败',
        modelNotFound: '模型未找到，请先训练模型'
      }
    },
    blog: {
      title: '最新文章',
      subtitle: '分享交易经验与市场洞察',
      minuteRead: '分钟阅读',
      readMore: '阅读更多',
      noArticles: '暂无文章',
      categories: {
        strategy: '交易策略',
        analysis: '市场分析',
        technology: '技术研究',
        tutorial: '教程指南'
      },
      tags: {
        quantitative: '量化交易',
        ai: '人工智能',
        technical: '技术分析',
        fundamental: '基本面分析',
        risk: '风险管理',
        beginner: '新手入门'
      },
      createNew: '新建文章',
      create: {
        title: '创建新文章',
        titleLabel: '标题',
        tagsLabel: '标签',
        contentLabel: '内容',
        contentPlaceholder: '使用 Markdown 编写文章...',
        write: '编写',
        preview: '预览',
        publish: '发布'
      }
    },
    about: {
      title: '关于我们',
      introduction: '平台简介',
      introText: '我们是一个专注于股票市场分析和交易的综平台，致力于为投资者提供专业的量化交易工具和市场洞察。',
      features: '核心功能',
      featureList: [
        '实时股票数据监控与分析',
        'AI驱动的市场预测',
        '专业的回测系统',
        '多样化的交易策略',
        '完整的风险管理工具',
        '丰富的学习资源'
      ],
      contact: '联系方式',
      contactText: '如果您有任何问题或建议，欢迎通过以下方式联系我们：\n邮箱：support@example.com\n工作时间：周一至周五 9:00-18:00'
    },
    categories: {
      trend: '趋势跟踪',
      momentum: '动量交易',
      value: '价值投资',
      volatility: '波动率交易',
      mean_reversion: '均值回归',
      arbitrage: '套利交易',
      ml: '机器学习',
      fundamental: '基本面分析'
    },
    tags: {
      trend: '趋势',
      momentum: '动量',
      value: '价值',
      volatility: '波动',
      mean_reversion: '均值回归',
      arbitrage: '套利',
      ml: '机器学习',
      fundamental: '基本面'
    }
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  fallbackLocale: 'en',
  messages
})
