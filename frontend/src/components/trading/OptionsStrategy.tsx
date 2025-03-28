import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Components } from 'react-markdown';

interface StrategyResponse {
  content: string;
  reasoning_content: string;
}

interface CodeProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
  [key: string]: any;
}

const OptionsStrategy: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [strategyData, setStrategyData] = useState<StrategyResponse | null>(null);

  const handleViewAnalysis = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(API_ENDPOINTS.trading.options, {
        params: { date: selectedDate }
      });
      setStrategyData(response.data);
    } catch (error) {
      console.error('获取策略分析失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const markdownComponents: Components = {
    code({ node, inline, className, children, ...props }: CodeProps) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={vscDarkPlus as any}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className="bg-gray-100 dark:bg-gray-800 rounded px-1 py-0.5" {...props}>
          {children}
        </code>
      );
    },
    h1: ({ children }) => <h1 className="text-2xl font-bold mb-4">{children}</h1>,
    h2: ({ children }) => <h2 className="text-xl font-bold mb-3">{children}</h2>,
    h3: ({ children }) => <h3 className="text-lg font-bold mb-2">{children}</h3>,
    p: ({ children }) => <p className="mb-4 leading-relaxed">{children}</p>,
    ul: ({ children }) => <ul className="list-disc pl-6 mb-4">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-6 mb-4">{children}</ol>,
    li: ({ children }) => <li className="mb-2">{children}</li>,
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 italic my-4">
        {children}
      </blockquote>
    ),
    table: ({ children }) => (
      <div className="overflow-x-auto mb-4">
        <table className="min-w-full divide-y divide-gray-200">
          {children}
        </table>
      </div>
    ),
    th: ({ children }) => (
      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {children}
      </td>
    ),
  };

  return (
    <div className="space-y-6">
      {/* 日期选择和查看分析按钮 */}
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label htmlFor="date" className="block text-sm font-medium text-gray-700">
              选择日期
            </label>
            <input
              type="date"
              id="date"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleViewAnalysis}
              disabled={isLoading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? '加载中...' : '查看分析'}
            </button>
          </div>
        </div>
      </div>

      {/* 策略内容 */}
      <div className="space-y-6">
        {/* 思维链内容 */}
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">思维链分析</h3>
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {strategyData?.reasoning_content || '暂无思维链分析'}
            </ReactMarkdown>
          </div>
        </div>

        {/* 最终回答 */}
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">最终策略建议</h3>
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {strategyData?.content || '暂无策略建议'}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptionsStrategy; 