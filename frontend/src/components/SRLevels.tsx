import React from 'react';

interface SRLevel {
  price: number;
  type: 'Support' | 'Resistance';
  strength: number;
  start_time: string;
  break_time: string | null;
  retest_times: string[];
  timeframe: string;
}

interface SRLevelsProps {
  levels: SRLevel[];
}

const SRLevels: React.FC<SRLevelsProps> = ({ levels }) => {
  // 只显示最近90天的数据，并且只显示未突破的支撑阻力位
  const ninetyDaysAgo = new Date();
  ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);

  const recentLevels = levels.filter(level => {
    const startTime = new Date(level.start_time);
    return startTime >= ninetyDaysAgo && !level.break_time; // 只显示未突破的
  });

  // 按强度排序
  const sortedLevels = recentLevels.sort((a, b) => b.strength - a.strength);

  const supportLevels = sortedLevels.filter(level => level.type === 'Support');
  const resistanceLevels = sortedLevels.filter(level => level.type === 'Resistance');

  const renderLevel = (level: SRLevel) => {
    const isRetesting = level.retest_times.length > 0;

    return (
      <div key={`${level.type}-${level.price}`} 
           className="p-3 rounded-lg border border-green-200 bg-green-50">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              level.type === 'Support' ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className={`text-lg font-semibold ${
              level.type === 'Support' ? 'text-green-600' : 'text-red-600'
            }`}>
              {level.price.toFixed(2)}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
              有效
            </span>
            {isRetesting && (
              <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                回测中
              </span>
            )}
            <div className="flex">
              {[...Array(level.strength)].map((_, i) => (
                <div key={i} className="w-1.5 h-1.5 rounded-full bg-blue-500 mx-0.5" />
              ))}
            </div>
          </div>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          <div>开始: {new Date(level.start_time).toLocaleDateString()}</div>
          {isRetesting && (
            <div className="mt-1">
              最近回测: {new Date(level.retest_times[level.retest_times.length - 1]).toLocaleDateString()}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium text-green-600 mb-2">支撑位</h4>
        <div className="space-y-2">
          {supportLevels.map(renderLevel)}
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-red-600 mb-2">阻力位</h4>
        <div className="space-y-2">
          {resistanceLevels.map(renderLevel)}
        </div>
      </div>
    </div>
  );
};

export default SRLevels; 