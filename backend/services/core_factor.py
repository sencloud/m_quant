from datetime import datetime
import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from utils.logger import logger
from models.core_factor import Base, CoreFactorAnalysisDB, CoreFactorAnalysis

class CoreFactorAnalyzer:
    def __init__(self):
        self.logger = logger
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://ark.cn-beijing.volces.com/api/v3/bots"
        )
        self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    async def _get_deepseek_response(self, prompt: str) -> Dict[str, Any]:
        """通用方法获取Deepseek响应"""
        try:
            response = self.client.chat.completions.create(
                model="bot-20250329163710-8zcqm",
                messages=[
                    {"role": "system", "content": "你是一个大豆和豆粕市场分析专家，请以JSON格式回答问题"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            content = response.choices[0].message.content
            self.logger.info(f"Deepseek原始响应：{content}")

            # 清理引用标记 [1], [2] 等
            content = re.sub(r'\[\d+\]', '', content)
            content = re.sub(r'\[\s*参考\s*\d+\s*\]', '', content)
            # 清理[参考资料]及其后面的内容
            content = re.sub(r'\[参考资料\][\s\S]*$', '', content)

            self.logger.info(f"清理后的响应：{content}")
            
            # 提取JSON内容
            if "```json" in content:
                # 处理有```json标记的情况
                json_content = content.split("```json")[1].split("```")[0].strip()
            elif "[参考编号]" in content:
                # 处理包含参考编号的情况
                json_content = content.split("[参考编号]")[0].strip()
            else:
                # 处理纯JSON或其他情况
                # 处理数组或对象类型
                if content.strip().startswith("["):
                    start = content.find("[")
                    end = content.rfind("]") + 1
                else:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                
                if start != -1 and end != 0:
                    json_content = content[start:end].strip()
                else:
                    json_content = content.strip()
            
            # 清理JSON中的空reference和references字段
            json_content = re.sub(r'"reference"\s*:\s*,', '', json_content)
            json_content = re.sub(r'"reference"\s*:\s*""\s*,', '', json_content)
            json_content = re.sub(r'"references"\s*:\s*\[\s*[\w\s,.":]+\s*\]', '', json_content)
            # 修复可能导致的双逗号问题
            json_content = re.sub(r',\s*,', ',', json_content)
            # 修复最后一个属性后面多余的逗号
            json_content = re.sub(r',\s*}', '}', json_content)
            
            self.logger.info(f"提取的JSON内容：{json_content}")
            return json.loads(json_content)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.logger.error(f"获取Deepseek响应失败: {str(e)}")
            raise

    async def get_inventory_cycle(self) -> Dict[str, Any]:
        """获取库存周期数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供豆粕库存周期分析数据。\n请以如下JSON格式回答："
            prompt += """
{
    "current_inventory": {
        "value": 数值,
        "unit": "万吨",
        "level": "高位/低位/中位",
        "mom_change": 环比变化率,
        "yoy_change": 同比变化率
    },
    "forecast": {
        "arrival": {
            "period": "预计到港时间",
            "volume": "预计到港量",
            "unit": "万吨/月"
        },
        "turning_point": "库存拐点预判分析"
    },
    "impact": "对市场影响分析"
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取库存周期数据失败: {str(e)}")
            raise

    async def get_technical_signals(self) -> Dict[str, Any]:
        """获取技术面信号数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供豆粕期货技术面分析。\n请以如下JSON格式回答："
            prompt += """
{
    "trends": {
        "weekly": {
            "pattern": "周线趋势描述",
            "key_levels": {
                "support": [支撑位列表],
                "resistance": [压力位列表]
            }
        },
        "daily": {
            "pattern": "日线趋势描述",
            "key_levels": {
                "support": [支撑位列表],
                "resistance": [压力位列表]
            }
        }
    },
    "volatility": {
        "current": 当前波动率,
        "strategy": "波动率策略建议"
    },
    "signals": {
        "trend": "多头/空头/震荡",
        "strength": "强/中/弱",
        "recommendation": "技术面操作建议"
    }
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取技术面信号数据失败: {str(e)}")
            raise

    async def get_price_anchors(self) -> Dict[str, Any]:
        """获取历史价格锚定数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供豆粕历史价格锚定分析。\n请以如下JSON格式回答："
            prompt += """
{
    "historical": {
        "low": {
            "value": 最低价,
            "period": "统计周期"
        },
        "high": {
            "value": 最高价,
            "period": "统计周期"
        },
        "average": {
            "value": 均值,
            "period": "统计周期"
        }
    },
    "seasonal": {
        "current_period": "当前季节性特征",
        "probability": 上涨概率,
        "historical_pattern": "历史规律描述"
    },
    "current_price": {
        "value": 当前价格,
        "position": "相对历史位置描述"
    }
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取历史价格锚定数据失败: {str(e)}")
            raise

    async def get_news_policy(self) -> Dict[str, Any]:
        """获取资讯与政策扰动数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供豆粕市场最新资讯与政策扰动分析。\n请以如下JSON格式回答："
            prompt += """
{
    "positive_factors": [
        {
            "event": "利多事件描述",
            "impact": "预计影响幅度",
            "probability": "发生概率"
        }
    ],
    "negative_factors": [
        {
            "event": "利空事件描述",
            "impact": "预计影响幅度",
            "probability": "发生概率"
        }
    ],
    "policy_updates": [
        {
            "policy": "政策名称",
            "content": "政策内容",
            "impact": "市场影响分析"
        }
    ],
    "key_monitoring": "需重点关注的事项"
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取资讯与政策扰动数据失败: {str(e)}")
            raise

    async def get_hog_market(self) -> Dict[str, Any]:
        """获取生猪市场联动数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供生猪市场与豆粕的联动分析。\n请以如下JSON格式回答："
            prompt += """
{
    "hog_market": {
        "inventory": {
            "value": 存栏量,
            "unit": "亿头",
            "yoy_change": 同比变化
        },
        "price": {
            "current": 当前价格,
            "unit": "元/公斤",
            "trend": "价格趋势"
        }
    },
    "feed_demand": {
        "status": "需求状况描述",
        "inventory_cycle": "补库周期分析"
    },
    "substitution": {
        "rapeseed_meal": {
            "price_spread": 豆菜价差,
            "impact": "替代效应分析"
        }
    },
    "outlook": "后市展望"
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取生猪市场联动数据失败: {str(e)}")
            raise

    def get_core_factor_data(self, date: str) -> Optional[CoreFactorAnalysis]:
        """从数据库获取指定日期的核心驱动因子数据"""
        try:
            db = self.SessionLocal()
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
            analysis = db.query(CoreFactorAnalysisDB).filter(CoreFactorAnalysisDB.date == query_date).first()
            if analysis:
                return CoreFactorAnalysis(
                    date=analysis.date,
                    inventory_cycle=analysis.inventory_cycle,
                    technical_signals=analysis.technical_signals,
                    price_anchors=analysis.price_anchors,
                    news_policy=analysis.news_policy,
                    hog_market=analysis.hog_market,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at
                )
            return None
        except Exception as e:
            self.logger.error(f"获取核心驱动因子数据失败: {str(e)}")
            raise
        finally:
            db.close()

    def save_core_factor_data(self, date: str, data: Dict[str, Any]) -> None:
        """保存核心驱动因子数据到数据库"""
        try:
            db = self.SessionLocal()
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
            db_analysis = CoreFactorAnalysisDB(
                date=query_date,
                inventory_cycle=data["inventory_cycle"],
                technical_signals=data["technical_signals"],
                price_anchors=data["price_anchors"],
                news_policy=data["news_policy"],
                hog_market=data["hog_market"]
            )
            db.merge(db_analysis)
            db.commit()
            self.logger.info(f"核心驱动因子数据已保存到数据库 - 日期: {date}")
        except Exception as e:
            self.logger.error(f"保存核心驱动因子数据失败: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()

    async def get_core_factor_analysis(self, date: str) -> Dict[str, Any]:
        """获取完整的核心驱动因子分析数据"""
        try:
            self.logger.info(f"开始获取{date}的核心驱动因子分析数据")
            
            # 首先尝试从数据库获取
            cached_data = self.get_core_factor_data(date)
            if cached_data:
                self.logger.info(f"从数据库获取到核心驱动因子数据 - 日期: {date}")
                return cached_data.dict()

            self.logger.info("数据库中没有找到核心驱动因子分析数据，开始调用Deepseek API")
            
            # 获取各项数据
            inventory = await self.get_inventory_cycle()
            technical = await self.get_technical_signals()
            price_anchors = await self.get_price_anchors()
            news_policy = await self.get_news_policy()
            hog_market = await self.get_hog_market()

            # 构建完整数据
            result = {
                "inventory_cycle": inventory,
                "technical_signals": technical,
                "price_anchors": price_anchors,
                "news_policy": news_policy,
                "hog_market": hog_market
            }

            # 保存到数据库
            self.save_core_factor_data(date, result)
            
            return result
        except Exception as e:
            self.logger.error(f"获取核心驱动因子分析数据失败: {str(e)}")
            raise 