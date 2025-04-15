import React, { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Dropdown } from 'antd';
import { DownOutlined, CrownOutlined } from '@ant-design/icons';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // 定义活动链接的类名函数
  const getNavLinkClass = ({ isActive }: { isActive: boolean }) => {
    return isActive 
      ? "text-blue-600 border-b-2 border-blue-600 hover:text-blue-700 px-3 py-2 text-sm font-medium"
      : "text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium";
  };

  // PRO功能菜单项
  const proMenuItems = [
    {
      key: 'pro-analysis',
      label: <Link to="/pro-analysis">历史分析</Link>,
      icon: <CrownOutlined />
    }
  ];

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

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            {/* <NavLink to="/market" className={getNavLinkClass}>
              市场数据
            </NavLink>
            <NavLink to="/analysis" className={getNavLinkClass}>
              技术分析
            </NavLink> */}
            <NavLink to="/trading" className={getNavLinkClass}>
              交易策略
            </NavLink>
            <NavLink to="/research" className={getNavLinkClass}>
              研究报告
            </NavLink>
            <Dropdown menu={{ items: proMenuItems }} placement="bottomRight">
              <a className="text-yellow-600 hover:text-yellow-700 px-3 py-2 text-sm font-medium flex items-center">
                <CrownOutlined className="mr-1" />
                PRO
                <DownOutlined className="ml-1" />
              </a>
            </Dropdown>
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            >
              <span className="sr-only">打开主菜单</span>
              {!isMenuOpen ? (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              ) : (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu panel */}
      <div className={`${isMenuOpen ? 'block' : 'hidden'} md:hidden`}>
        <div className="px-2 pt-2 pb-3 space-y-1">
          <NavLink
            to="/trading"
            className={getNavLinkClass}
            onClick={() => setIsMenuOpen(false)}
          >
            交易策略
          </NavLink>
          <NavLink
            to="/research"
            className={getNavLinkClass}
            onClick={() => setIsMenuOpen(false)}
          >
            研究报告
          </NavLink>
          <NavLink
            to="/pro-analysis"
            className={getNavLinkClass}
            onClick={() => setIsMenuOpen(false)}
          >
            <span className="flex items-center">
              <CrownOutlined className="mr-1 text-yellow-600" />
              PRO 历史分析
            </span>
          </NavLink>
        </div>
      </div>
    </header>
  );
};

export default Header; 