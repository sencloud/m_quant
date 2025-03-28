import React, { useState, useEffect, useRef } from 'react';
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
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [strategyContent, setStrategyContent] = useState<StrategyResponse>({
    content: '',
    reasoning_content: ''
  });
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const processStream = async (reader: ReadableStreamDefaultReader<Uint8Array>, signal: AbortSignal) => {
    const decoder = new TextDecoder();
    
    try {
      while (true) {
        if (signal.aborted) {
          break;
        }
        
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'reasoning') {
                setStrategyContent(prev => ({
                  ...prev,
                  reasoning_content: data.content
                }));
              } else if (data.type === 'content') {
                setStrategyContent(prev => ({
                  ...prev,
                  content: data.content
                }));
              } else if (data.type === 'done') {
                setIsStreaming(false);
                setError(null);
              } else if (data.type === 'error') {
                setError(data.message);
                setIsStreaming(false);
              }
            } catch (e) {
              console.error('解析数据失败:', e);
              setError('解析响应数据失败');
              setIsStreaming(false);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('请求被取消');
        return;
      }
      console.error('读取流失败:', error);
      setError('读取响应流失败');
      setIsStreaming(false);
    } finally {
      reader.releaseLock();
    }
  };

  const fetchStrategy = async (signal: AbortSignal) => {
    setIsStreaming(true);
    setError(null);
    setStrategyContent({ content: '', reasoning_content: '' });
    
    try {
      const response = await fetch(API_ENDPOINTS.trading.options, { signal });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');
      
      await processStream(reader, signal);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('请求被取消');
        return;
      }
      console.error('获取策略失败:', error);
      setError(error instanceof Error ? error.message : '获取策略失败');
      setIsStreaming(false);
    }
  };

  useEffect(() => {
    // 创建新的 AbortController
    abortControllerRef.current = new AbortController();
    
    // 发起请求
    fetchStrategy(abortControllerRef.current.signal);
    
    // 清理函数
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    
    setIsLoading(true);
    setError(null);
    setStrategyContent({ content: '', reasoning_content: '' });
    
    try {
      const response = await fetch(API_ENDPOINTS.trading.generateStrategy, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
        signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');
      
      setIsStreaming(true);
      await processStream(reader, abortControllerRef.current.signal);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('请求被取消');
        return;
      }
      console.error('生成策略失败:', error);
      setError(error instanceof Error ? error.message : '生成策略失败');
      setIsStreaming(false);
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
      {/* 策略生成器 */}
      <div className="bg-white border rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">AI策略生成器</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
              描述您的交易需求
            </label>
            <textarea
              id="prompt"
              rows={4}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="例如：我想在豆粕期货市场寻找一个低风险的期权策略，预期收益在10-15%之间..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isLoading ? '生成中...' : '生成策略'}
          </button>
        </form>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

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
              {strategyContent.reasoning_content || '暂无思维链分析'}
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
              {strategyContent.content || '暂无策略建议'}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptionsStrategy; 