import React from 'react';
import { Link, NavLink } from 'react-router-dom';

const Footer: React.FC = () => {
  // 定义活动链接的类名函数
  const getLegalLinkClass = ({ isActive }: { isActive: boolean }) => {
    return isActive 
      ? "text-white font-medium text-sm underline"
      : "text-gray-400 hover:text-white text-sm";
  };

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <h3 className="text-lg font-semibold mb-4">豆粕组合策略</h3>
            <p className="text-gray-400 text-sm">
              本站是豆粕品种量化交易策略平台，为您提供全方位的市场数据分析和交易策略服务。
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-lg font-semibold mb-4">快速链接</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/trading" className="text-gray-400 hover:text-white text-sm">
                  交易策略
                </Link>
              </li>
              <li>
                <Link to="/research" className="text-gray-400 hover:text-white text-sm">
                  研究报告
                </Link>
              </li>
              <li>
                <a href="http://www.dce.com.cn/" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white text-sm">
                  大连商品交易所
                </a>
              </li>
              <li>
                <a href="https://www.usda.gov/" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white text-sm">
                  美国农业部
                </a>
              </li>
              <li>
                <a href="http://www.customs.gov.cn/" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white text-sm">
                  中国海关总署
                </a>
              </li>
              <li>
                <a href="https://wallstreetcn.com/calendar" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white text-sm">
                  交易日历
                </a>
              </li>
              <li>
                <a href="https://tushare.pro/" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white text-sm">
                  Tushare
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-lg font-semibold mb-4">法律信息</h3>
            <ul className="space-y-2">
              <li>
                <NavLink to="/privacy" className={getLegalLinkClass}>
                  隐私政策
                </NavLink>
              </li>
              <li>
                <NavLink to="/terms" className={getLegalLinkClass}>
                  服务条款
                </NavLink>
              </li>
              <li>
                <NavLink to="/disclaimer" className={getLegalLinkClass}>
                  免责声明
                </NavLink>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-lg font-semibold mb-4">联系我们</h3>
            <ul className="space-y-2">
              <li className="text-gray-400 text-sm">
                邮箱：contact@singzquant.com
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-gray-800 text-center text-gray-400 text-sm">
          <p>© {new Date().getFullYear()} 新致智能量化. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 