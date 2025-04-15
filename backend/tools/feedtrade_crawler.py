import re
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Dict, Optional
import asyncio
import sys
import os
from loguru import logger
import sqlite3

# 添加父目录到系统路径，以便导入backend模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.news import NewsArticle

class FeedTradeCrawler:
    def __init__(self):
        self.base_urls = ["https://www.feedtrade.com.cn/sbm/news/index.html",
                         "https://www.feedtrade.com.cn/sbm/stat/index.html",
                         "https://www.feedtrade.com.cn/sbm/forecast/index.html",
                         "https://www.feedtrade.com.cn/sbm/future/index.html",
                         "https://www.feedtrade.com.cn/sbm/policy/index.html",
                         "https://www.feedtrade.com.cn/sbm/now/index.html",
                         "https://www.feedtrade.com.cn/sbm/zaoping/index.html",
                         "https://www.feedtrade.com.cn/sbm/weekly/index.html",
                         "https://www.feedtrade.com.cn/sbm/daily/index.html",
                         "https://www.feedtrade.com.cn/soybean/zaobao/index.html",
                         "https://www.feedtrade.com.cn/soybean/soybean_stat/index.html",
                         "https://www.feedtrade.com.cn/soybean/soybean_forecast/index.html",
                         'https://www.feedtrade.com.cn/soybean/soybean_internation/index.html'
                         ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # 数据库路径
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trading.db")
        logger.info(f"初始化爬虫，基础URL数量: {len(self.base_urls)}")
        logger.info(f"数据库路径: {self.db_path}")

    async def fetch_page(self, url: str) -> Optional[str]:
        logger.info(f"开始获取页面: {url}")
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"发送GET请求，请求头: {self.headers}")
                response = await client.get(url, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                logger.info(f"页面获取成功，状态码: {response.status_code}")
                logger.debug(f"响应内容长度: {len(response.text)}")
                return response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP错误，获取页面失败 {url}: {str(e)}")
            return None
        except httpx.TimeoutException as e:
            logger.error(f"请求超时，获取页面失败 {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"未知错误，获取页面失败 {url}: {str(e)}")
            return None

    def parse_news_list(self, html: str) -> List[Dict]:
        logger.info("开始解析新闻列表")
        soup = BeautifulSoup(html, 'html.parser')
        news_list = []
        
        # 找到新闻列表容器
        news_container = soup.find('div', class_='category-article-page-list')
        if not news_container:
            logger.warning("未找到新闻列表容器 category-article-page-list")
            logger.debug(f"HTML内容片段: {html[:500]}...")  # 只打印前500个字符避免日志过长
            return news_list

        logger.info("找到新闻容器，开始搜索新闻项")
        news_items = news_container.find_all('li')
        logger.info(f"找到 {len(news_items)} 条新闻")

        # 解析每条新闻
        for index, news_item in enumerate(news_items, 1):
            try:
                logger.debug(f"正在处理第 {index}/{len(news_items)} 条新闻")
                
                # 直接查找a标签获取链接和标题
                a_elem = news_item.find('a')
                if not a_elem:
                    logger.warning(f"第 {index} 条新闻未找到链接元素")
                    continue

                title = a_elem.text.strip()
                link = a_elem.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://www.feedtrade.com.cn{link}"
                    logger.debug(f"转换相对链接为绝对链接: {link}")

                # 查找日期，日期在li标签内的span标签中
                date_elem = news_item.find('span')
                date_str = date_elem.text.strip() if date_elem else ''
                
                news_data = {
                    'title': title,
                    'link': link,
                    'date': date_str,
                    'source': 'feedtrade'
                }
                logger.debug(f"成功解析新闻项: {news_data}")
                news_list.append(news_data)
            except Exception as e:
                logger.error(f"解析第 {index} 条新闻时出错: {str(e)}")
                logger.debug(f"问题新闻HTML: {news_item}")
                continue

        logger.info(f"新闻列表解析完成，共解析 {len(news_list)} 条新闻")
        return news_list

    async def fetch_article_content(self, url: str) -> Optional[Dict]:
        logger.info(f"开始获取文章内容: {url}")
        html = await self.fetch_page(url)
        if not html:
            logger.error(f"获取文章内容失败: {url}")
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')
            content_div = soup.find('div', class_='prose-lg')
            if not content_div:
                logger.warning(f"未找到文章内容div: {url}")
                return None

            content = content_div.get_text(strip=True)
            
            # 提取更新时间
            date_obj = datetime.now()  # 默认使用当前时间
            time_pattern = r'<div class="flex-auto text-12px grey !h-24px text-center">.*?更新时间：(\d{4})年(\d{1,2})月(\d{1,2})日.*?</div>'
            time_match = re.search(time_pattern, html, re.DOTALL)
            
            if time_match:
                year = int(time_match.group(1))
                month = int(time_match.group(2))
                day = int(time_match.group(3))
                date_obj = datetime(year, month, day)
                logger.info(f"从文章内容提取到更新时间: {date_obj}")
            
            result = {
                'content': content,
                'date_obj': date_obj
            }
            
            logger.info(f"成功提取文章内容: {url}")
            return result
        except Exception as e:
            logger.error(f"解析文章内容时出错: {url}: {str(e)}")
            return None

    def save_to_db(self, article: NewsArticle) -> bool:
        """直接保存到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在相同标题的新闻
            cursor.execute("SELECT id FROM news_article WHERE title = ?", (article.title,))
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"新闻已存在，跳过: {article.title}")
                return False
                
            # 插入新新闻
            cursor.execute(
                "INSERT INTO news_article (datetime, title, content, analysis, remarks) VALUES (?, ?, ?, ?, ?)",
                (article.datetime, article.title, article.content, article.analysis, article.remarks)
            )
            
            conn.commit()
            logger.info(f"成功保存新闻到数据库: {article.title}")
            return True
        except Exception as e:
            logger.error(f"保存新闻到数据库失败: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    async def get_latest_news(self) -> List[Dict]:
        logger.info("开始获取最新新闻")
        all_news = []
        
        # 从所有URL获取新闻
        for url in self.base_urls:
            logger.info(f"从URL获取新闻: {url}")
            html = await self.fetch_page(url)
            if not html:
                logger.error(f"获取HTML内容失败: {url}")
                continue
            
            logger.info(f"成功获取HTML，开始解析新闻列表: {url}")
            news_list = self.parse_news_list(html)
            logger.info(f"从 {url} 获取到 {len(news_list)} 条新闻")
            
            # 获取每篇文章的内容
            for news in news_list:
                article_data = await self.fetch_article_content(news['link'])
                
                # 将新闻保存到数据库
                if article_data:
                    try:
                        news['content'] = article_data.get('content', '')
                        
                        # 使用文章数据中的日期或尝试解析
                        date_obj = datetime.now()  # 默认使用当前时间
                        
                        if 'date_obj' in article_data and article_data['date_obj']:
                            # 直接使用解析好的日期
                            date_obj = article_data['date_obj']
                            logger.info(f"使用解析好的日期: {date_obj}")
                        else:
                            # 如果没有解析好的日期，尝试使用news中的date
                            date_str = news['date']
                            try:
                                # 尝试不同的日期格式
                                if '[' in date_str and ']' in date_str:
                                    # 处理 [04-07] 格式
                                    month_day = date_str.strip('[]')
                                    current_year = datetime.now().year
                                    date_str_with_year = f"{current_year}-{month_day}"
                                    date_obj = datetime.strptime(date_str_with_year, '%Y-%m-%d')
                                elif '-' in date_str:
                                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                else:
                                    date_obj = datetime.strptime(date_str, '%Y/%m/%d')
                            except ValueError:
                                logger.warning(f"无法解析日期: {date_str}，使用当前日期")
                        
                        # 创建NewsArticle对象
                        article = NewsArticle(
                            datetime=date_obj,
                            title=news['title'],
                            content=news['content'],
                            analysis=None,
                            remarks=f"来源: {url}"
                        )
                        
                        # 保存到数据库
                        self.save_to_db(article)
                    except Exception as e:
                        logger.error(f"保存新闻到数据库失败: {str(e)}")
            
            all_news.extend(news_list)
        
        logger.info(f"总共获取到 {len(all_news)} 条新闻")
        return all_news

async def main():
    logger.info("开始运行爬虫主函数")
    crawler = FeedTradeCrawler()
    news = await crawler.get_latest_news()
    logger.info(f"总共获取到 {len(news)} 条新闻")
    for item in news:
        print(f"标题: {item['title']}")
        print(f"链接: {item['link']}")
        print(f"日期: {item['date']}")
        print(f"内容: {item.get('content', '无内容')[:200]}...")  # 只打印前200个字符
        print("-" * 50)

if __name__ == "__main__":
    logger.info("脚本开始运行")
    asyncio.run(main())
    logger.info("脚本运行完成") 