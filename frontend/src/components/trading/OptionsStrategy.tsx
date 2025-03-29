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
  const [showReasoning, setShowReasoning] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const handleViewAnalysis = async () => {
    setIsLoading(true);
    setIsStreaming(false);
    setShowReasoning(false);
    try {
      const response = await fetch(`${API_ENDPOINTS.trading.options}?date=${selectedDate}`);
      
      // 检查响应类型
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('text/event-stream')) {
        // 处理流式响应
        setIsStreaming(true);
        const reader = response.body?.getReader();
        if (!reader) throw new Error('无法读取响应流');
        
        const decoder = new TextDecoder();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'reasoning') {
                setStrategyData(prev => ({ 
                  reasoning_content: data.content,
                  content: prev?.content || ''
                }));
              } else if (data.type === 'content') {
                setStrategyData(prev => ({ 
                  content: data.content,
                  reasoning_content: prev?.reasoning_content || ''
                }));
              } else if (data.type === 'done') {
                setIsLoading(false);
                setIsStreaming(false);
              } else if (data.type === 'error') {
                console.error('获取策略分析失败:', data.message);
                setIsLoading(false);
                setIsStreaming(false);
              }
            }
          }
        }
      } else {
        // 处理普通响应
        const data = await response.json();
        setStrategyData({
          content: data.content,
          reasoning_content: data.reasoning_content
        });
        setIsLoading(false);
      }
    } catch (error) {
      console.error('获取策略分析失败:', error);
      setIsLoading(false);
      setIsStreaming(false);
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
    h3: ({ children }) => <h3 className="text-lg font-medium text-gray-900 mb-2">{children}</h3>,
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
              {isLoading ? '加载中...' : '查看报告'}
            </button>
          </div>
        </div>
      </div>

      {/* 策略内容 */}
      {strategyData && (
        <div className="space-y-4">
          {/* 最终回答 */}
          <div className="bg-white border rounded-lg p-6 relative">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-medium text-gray-900">策略建议</h3>
              {!isStreaming && strategyData.reasoning_content && (
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {showReasoning ? '收起思维链' : '查看思维链'}
                </button>
              )}
            </div>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {strategyData.content}
              </ReactMarkdown>
            </div>
            
            {/* 思维链分析 */}
            {!isStreaming && strategyData.reasoning_content && (
              <div className={`mt-4 transition-all duration-300 ease-in-out overflow-hidden ${
                showReasoning ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
              }`}>
                <div className="border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">思维链分析</h4>
                  <div className="prose prose-sm max-w-none text-gray-500">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
                    >
                      {strategyData.reasoning_content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OptionsStrategy; 