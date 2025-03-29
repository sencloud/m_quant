import React from 'react';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link to="/" className="flex items-center">
              <img src="/logo.png" alt="Logo" className="h-12 w-auto mr-3" />
              <div className="flex flex-col">
                <span className="text-2xl font-bold text-gray-900">豆粕组合策略</span>
                <span className="text-sm text-gray-500">豆粕ETF、期货、期权</span>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex space-x-8">
            {/* <Link to="/market" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
              市场数据
            </Link>
            <Link to="/analysis" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
              技术分析
            </Link> */}
            <Link to="/trading" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
              交易策略
            </Link>
            <Link to="/research" className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium">
              研究报告
            </Link>
          </nav>

          {/* Right side */}
          {/* <div className="flex items-center space-x-4">
            <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
              登录
            </button>
            <button className="border border-blue-600 text-blue-600 px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-50">
              注册
            </button>
          </div> */}
        </div>
      </div>
    </header>
  );
};

export default Header; 