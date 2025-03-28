import React from 'react';

interface TimeRangeSelectorProps {
  timeRange: '1m' | '3m' | '6m' | '1y';
  onTimeRangeChange: (range: '1m' | '3m' | '6m' | '1y') => void;
}

const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({ timeRange, onTimeRangeChange }) => {
  return (
    <section className="py-12 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900">时间范围</h2>
          <p className="mt-4 text-lg text-gray-500">
            选择要查看的时间范围
          </p>
        </div>

        <div className="flex space-x-4">
          <button
            onClick={() => onTimeRangeChange('1m')}
            className={`px-4 py-2 rounded-md ${
              timeRange === '1m' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            1个月
          </button>
          <button
            onClick={() => onTimeRangeChange('3m')}
            className={`px-4 py-2 rounded-md ${
              timeRange === '3m' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            3个月
          </button>
          <button
            onClick={() => onTimeRangeChange('6m')}
            className={`px-4 py-2 rounded-md ${
              timeRange === '6m' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            6个月
          </button>
          <button
            onClick={() => onTimeRangeChange('1y')}
            className={`px-4 py-2 rounded-md ${
              timeRange === '1y' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            1年
          </button>
        </div>
      </div>
    </section>
  );
};

export default TimeRangeSelector; 