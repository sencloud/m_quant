import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Singz Quant</h3>
            <p className="text-gray-400 text-sm">
              专业的量化交易平台，为您提供全方位的市场数据分析和交易策略服务。
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-lg font-semibold mb-4">快速链接</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/market" className="text-gray-400 hover:text-white text-sm">
                  市场数据
                </Link>
              </li>
              <li>
                <Link to="/analysis" className="text-gray-400 hover:text-white text-sm">
                  技术分析
                </Link>
              </li>
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
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-lg font-semibold mb-4">法律信息</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/privacy" className="text-gray-400 hover:text-white text-sm">
                  隐私政策
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-gray-400 hover:text-white text-sm">
                  服务条款
                </Link>
              </li>
              <li>
                <Link to="/disclaimer" className="text-gray-400 hover:text-white text-sm">
                  免责声明
                </Link>
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
              <li className="text-gray-400 text-sm">
                电话：+86 123 4567 8900
              </li>
              <li className="text-gray-400 text-sm">
                地址：北京市朝阳区xxx大厦
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-gray-800 text-center text-gray-400 text-sm">
          <p>© {new Date().getFullYear()} Singz Quant. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 