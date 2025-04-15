import tushare as ts
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from config import settings
from utils.logger import logger
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models.news import FlashNews, NewsArticle

Base = declarative_base()

class FlashNewsDB(Base):
    """快讯数据库表"""
    __tablename__ = "flash_news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    analysis = Column(Text)
    remarks = Column(Text)

class NewsArticleDB(Base):
    """资讯数据库表"""
    __tablename__ = "news_article"

    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    analysis = Column(Text)
    remarks = Column(Text)

class NewsService:
    """新闻数据服务"""
    
    def __init__(self):
        """初始化新闻数据服务"""
        try:
            self.token = settings.TUSHARE_TOKEN
            if not self.token:
                logger.error("未找到 TUSHARE_TOKEN，请在 .env 文件中设置")
                self.pro = None
            else:
                ts.set_token(self.token)
                self.pro = ts.pro_api()
                logger.info("新闻数据服务初始化完成")
                
            # 初始化数据库连接
            self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("新闻数据库连接初始化完成")
        except Exception as e:
            logger.error(f"新闻数据服务初始化失败: {e}")
            self.pro = None
            self.engine = None
            self.SessionLocal = None

    def get_news(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """获取新闻数据
        
        Args:
            start_date: 开始日期，格式：YYYYMMDD
            end_date: 结束日期，格式：YYYYMMDD
            
        Returns:
            新闻数据列表
        """
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取新闻数据")
                return []
                
            # 如果未指定日期，默认获取过去1个月的数据
            if not start_date and not end_date:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            else:
                end_date = datetime.strptime(end_date, '%Y%m%d')
                start_date = datetime.strptime(start_date, '%Y%m%d') if start_date else end_date - timedelta(days=30)
            
            # 检查数据库中是否有数据
            db = self.SessionLocal()
            db_news = db.query(FlashNewsDB).all()
            
            # 如果数据库中没有数据，则获取并保存
            if not db_news:
                logger.info("数据库中无快讯数据，开始获取并保存")
                all_news = self._fetch_news_from_tushare(start_date, end_date)
                self._save_flash_news_to_db(all_news)
                db_news = db.query(FlashNewsDB).all()
            else:
                # 获取最近12小时的数据
                recent_end = datetime.now()
                recent_start = recent_end - timedelta(hours=12)
                logger.info(f"获取最近12小时的新闻数据: {recent_start} 到 {recent_end}")
                
                recent_news = self._fetch_news_from_tushare(recent_start, recent_end)
                if recent_news:
                    self._upsert_flash_news_to_db(recent_news)
            
            # 从数据库获取所有快讯
            db_news = db.query(FlashNewsDB).order_by(FlashNewsDB.datetime.desc()).all()
            
            # 转换为字典列表
            result = []
            for news in db_news:
                result.append({
                    'id': news.id,
                    'datetime': news.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'content': news.content,
                    'analysis': news.analysis,
                    'remarks': news.remarks
                })
            
            logger.info(f"成功获取快讯数据，共{len(result)}条记录")
            return result
            
        except Exception as e:
            logger.error(f"获取新闻数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if 'db' in locals():
                db.close()

    def _fetch_news_from_tushare(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """从Tushare获取新闻数据"""
        all_news = []
        current_end = end_date
        
        # 按12小时轮询获取数据
        while current_end > start_date:
            current_start = max(current_end - timedelta(hours=12), start_date)
            
            # 转换日期格式为 'YYYY-MM-DD HH:MM:SS'
            formatted_start = current_start.strftime('%Y-%m-%d %H:%M:%S')
            formatted_end = current_end.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"获取新闻数据: {formatted_start} 到 {formatted_end}")
            df = self.pro.news(src='sina', start_date=formatted_start, end_date=formatted_end)
            
            if df is not None and not df.empty:
                # 过滤相关新闻
                keywords = ['南美', '大豆', '豆粕', '豆油', '菜粕', '生猪', 'USDA', '美国农业', '农业部', '猪肉', '南美航线', '南美天气', '巴西大豆']
                df['matched_keyword'] = df['content'].apply(lambda x: next((k for k in keywords if k in str(x)), None))
                df['is_relevant'] = df['matched_keyword'].notna()
                df = df[df['is_relevant']]
                
                # 排除不相关的市场动态关键词
                exclude_keywords = ['夜盘', '早盘', '沪指', '收盘', '开盘', '股市', 'A股', '港股', 'ETF', '股价', '公司', '英国', '酒']
                df['has_exclude_keyword'] = df['content'].apply(lambda x: any(k in str(x) for k in exclude_keywords))
                df = df[~df['has_exclude_keyword']]
                
                if len(df) > 0:
                    all_news.append(df)
                    logger.info(f"时间段 {formatted_start} 到 {formatted_end} 获取到 {len(df)} 条相关新闻")
            
            current_end = current_start
        
        if not all_news:
            logger.warning("未获取到任何新闻数据")
            return []
        
        # 合并所有数据
        final_df = pd.concat(all_news, ignore_index=True)
        
        # 按日期排序
        final_df = final_df.sort_values('datetime', ascending=False)
        
        # 去除重复内容
        final_df = final_df.drop_duplicates(subset=['content'], keep='first')
        
        # 转换为字典列表
        result = final_df.to_dict('records')
        return result

    def _save_news_to_db(self, news_list: List[Dict[str, Any]]) -> None:
        """保存新闻到数据库"""
        if not news_list:
            return
            
        try:
            db = self.SessionLocal()
            for news in news_list:
                # 转换日期字符串为datetime对象
                news_datetime = datetime.strptime(news['datetime'], '%Y-%m-%d %H:%M:%S')
                
                # 创建快讯对象
                flash_news = FlashNewsDB(
                    datetime=news_datetime,
                    content=news['content'],
                    analysis=None,
                    remarks=None
                )
                
                db.add(flash_news)
            
            db.commit()
            logger.info(f"成功保存 {len(news_list)} 条快讯到数据库")
        except Exception as e:
            logger.error(f"保存快讯到数据库失败: {e}")
            db.rollback()
        finally:
            db.close()

    def _save_flash_news_to_db(self, news_list: List[Dict[str, Any]]) -> None:
        """保存快讯到数据库"""
        if not news_list:
            return
            
        try:
            db = self.SessionLocal()
            for news in news_list:
                # 转换日期字符串为datetime对象
                news_datetime = datetime.strptime(news['datetime'], '%Y-%m-%d %H:%M:%S')
                
                # 创建快讯对象
                flash_news = FlashNewsDB(
                    datetime=news_datetime,
                    content=news['content'],
                    analysis=None,
                    remarks=None
                )
                
                db.add(flash_news)
            
            db.commit()
            logger.info(f"成功保存 {len(news_list)} 条快讯到数据库")
        except Exception as e:
            logger.error(f"保存快讯到数据库失败: {e}")
            db.rollback()
        finally:
            db.close()

    def _upsert_news_to_db(self, news_list: List[Dict[str, Any]]) -> None:
        """更新或插入新闻到数据库"""
        if not news_list:
            return
            
        try:
            db = self.SessionLocal()
            for news in news_list:
                # 转换日期字符串为datetime对象
                news_datetime = datetime.strptime(news['datetime'], '%Y-%m-%d %H:%M:%S')
                
                # 检查是否存在相同内容的新闻
                existing_news = db.query(NewsArticleDB).filter(
                    NewsArticleDB.content == news['content']
                ).first()
                
                if existing_news:
                    # 更新现有新闻
                    existing_news.datetime = news_datetime
                    existing_news.title = news.get('title', '')
                    logger.info(f"更新新闻: {news.get('title', '')}")
                else:
                    # 添加新新闻
                    news_article = NewsArticleDB(
                        datetime=news_datetime,
                        title=news.get('title', ''),
                        content=news['content'],
                        analysis=None,
                        remarks=None
                    )
                    db.add(news_article)
                    logger.info(f"添加新新闻: {news.get('title', '')}")
            
            db.commit()
            logger.info(f"成功更新/插入 {len(news_list)} 条新闻到数据库")
        except Exception as e:
            logger.error(f"更新/插入新闻到数据库失败: {e}")
            db.rollback()
        finally:
            db.close()

    def _upsert_flash_news_to_db(self, news_list: List[Dict[str, Any]]) -> None:
        """更新或插入快讯到数据库"""
        if not news_list:
            return
            
        try:
            db = self.SessionLocal()
            for news in news_list:
                # 转换日期字符串为datetime对象
                news_datetime = datetime.strptime(news['datetime'], '%Y-%m-%d %H:%M:%S')
                
                # 检查是否存在相同内容的快讯
                existing_news = db.query(FlashNewsDB).filter(
                    FlashNewsDB.content == news['content']
                ).first()
                
                if existing_news:
                    # 更新现有快讯
                    existing_news.datetime = news_datetime
                    logger.info(f"更新快讯: {news['content'][:30]}...")
                else:
                    # 添加新快讯
                    flash_news = FlashNewsDB(
                        datetime=news_datetime,
                        content=news['content'],
                        analysis=None,
                        remarks=None
                    )
                    db.add(flash_news)
                    logger.info(f"添加新快讯: {news['content'][:30]}...")
            
            db.commit()
            logger.info(f"成功更新/插入 {len(news_list)} 条快讯到数据库")
        except Exception as e:
            logger.error(f"更新/插入快讯到数据库失败: {e}")
            db.rollback()
        finally:
            db.close()

    def analyze_news_impact(self, news_date: str) -> Dict[str, Any]:
        """分析新闻对期货价格的影响
        
        Args:
            news_date: 新闻日期，格式：YYYYMMDD
            
        Returns:
            分析结果
        """
        try:
            if self.engine is None:
                logger.error("数据库未初始化，无法分析新闻影响")
                return {}
                
            # 转换日期格式
            start_date = datetime.strptime(news_date, '%Y%m%d')
            end_date = start_date + timedelta(days=1)
                
            # 从数据库获取指定日期的新闻数据
            db = self.SessionLocal()
            news_articles = db.query(NewsArticleDB).filter(
                NewsArticleDB.datetime >= start_date,
                NewsArticleDB.datetime < end_date
            ).order_by(NewsArticleDB.datetime.desc()).all()
            
            if not news_articles:
                logger.warning(f"未找到{news_date}的新闻数据")
                return {}
                
            # 获取期货价格数据
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取期货价格数据")
                return {}
                
            futures_df = self.pro.fut_daily(trade_date=news_date)
            if futures_df is None or futures_df.empty:
                return {}
                
            # 分析新闻影响
            result = {
                'date': news_date,
                'news_count': len(news_articles),
                'price_change': None,
                'volume_change': None,
                'analysis': []
            }
            
            # 计算价格变化
            if len(futures_df) > 0:
                result['price_change'] = futures_df['close'].iloc[0] - futures_df['open'].iloc[0]
                result['volume_change'] = futures_df['vol'].iloc[0]
                
            # 分析每条新闻
            for article in news_articles:
                impact = {
                    'title': article.title,
                    'content': article.content,
                    'datetime': article.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'sentiment': 'positive' if result['price_change'] > 0 else 'negative' if result['price_change'] < 0 else 'neutral'
                }
                result['analysis'].append(impact)
                
            logger.info(f"成功分析{news_date}的新闻影响，共{len(news_articles)}条新闻")
            return result
            
        except Exception as e:
            logger.error(f"分析新闻影响失败: {e}")
            return {}
        finally:
            if 'db' in locals():
                db.close()

    def get_flash_news(self) -> List[Dict[str, Any]]:
        """获取快讯数据"""
        try:
            if self.engine is None:
                logger.error("数据库未初始化，无法获取快讯数据")
                return []
                
            db = self.SessionLocal()
            flash_news = db.query(FlashNewsDB).order_by(FlashNewsDB.datetime.desc()).all()
            
            result = []
            for news in flash_news:
                result.append({
                    'id': news.id,
                    'datetime': news.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'content': news.content,
                    'analysis': news.analysis,
                    'remarks': news.remarks
                })
            
            logger.info(f"成功获取快讯数据，共{len(result)}条记录")
            return result
        except Exception as e:
            logger.error(f"获取快讯数据失败: {e}")
            return []
        finally:
            if 'db' in locals():
                db.close()

    def get_news_articles(self) -> List[Dict[str, Any]]:
        """获取资讯文章数据"""
        try:
            if self.engine is None:
                logger.error("数据库未初始化，无法获取资讯文章数据")
                return []
                
            db = self.SessionLocal()
            articles = db.query(NewsArticleDB).order_by(NewsArticleDB.datetime.desc()).all()
            
            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'datetime': article.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'title': article.title,
                    'content': article.content,
                    'analysis': article.analysis,
                    'remarks': article.remarks
                })
            
            logger.info(f"成功获取资讯文章数据，共{len(result)}条记录")
            return result
        except Exception as e:
            logger.error(f"获取资讯文章数据失败: {e}")
            return []
        finally:
            if 'db' in locals():
                db.close()

    def create_flash_news(self, flash_news: FlashNews) -> Dict[str, Any]:
        """创建快讯"""
        try:
            if self.engine is None:
                logger.error("数据库未初始化，无法创建快讯")
                return {}
                
            db = self.SessionLocal()
            
            # 创建快讯对象
            db_flash_news = FlashNewsDB(
                datetime=flash_news.datetime,
                content=flash_news.content,
                analysis=flash_news.analysis,
                remarks=flash_news.remarks
            )
            
            db.add(db_flash_news)
            db.commit()
            
            result = {
                'id': db_flash_news.id,
                'datetime': db_flash_news.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'content': db_flash_news.content,
                'analysis': db_flash_news.analysis,
                'remarks': db_flash_news.remarks
            }
            
            logger.info(f"成功创建快讯，ID: {db_flash_news.id}")
            return result
        except Exception as e:
            logger.error(f"创建快讯失败: {e}")
            db.rollback()
            return {}
        finally:
            if 'db' in locals():
                db.close()

    def create_news_article(self, article: NewsArticle) -> Dict[str, Any]:
        """创建资讯文章"""
        try:
            if self.engine is None:
                logger.error("数据库未初始化，无法创建资讯文章")
                return {}
                
            db = self.SessionLocal()
            
            # 创建资讯文章对象
            db_article = NewsArticleDB(
                datetime=article.datetime,
                title=article.title,
                content=article.content,
                analysis=article.analysis,
                remarks=article.remarks
            )
            
            db.add(db_article)
            db.commit()
            
            result = {
                'id': db_article.id,
                'datetime': db_article.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'title': db_article.title,
                'content': db_article.content,
                'analysis': db_article.analysis,
                'remarks': db_article.remarks
            }
            
            logger.info(f"成功创建资讯文章，ID: {db_article.id}")
            return result
        except Exception as e:
            logger.error(f"创建资讯文章失败: {e}")
            db.rollback()
            return {}
        finally:
            if 'db' in locals():
                db.close() 