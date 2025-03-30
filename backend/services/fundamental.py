from datetime import datetime
import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional
from utils.logger import logger
from openai import OpenAI
from config import settings
import json
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.fundamental import Base, FundamentalAnalysisDB, FundamentalAnalysis

class FundamentalAnalyzer:
    def __init__(self):
        self.logger = logger
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://ark.cn-beijing.volces.com/api/v3/bots"
        )
        self.engine = create_engine(settings.DATABASE_URL or "sqlite:///./trading.db")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_fundamental_data(self, date: str) -> Optional[FundamentalAnalysis]:
        """从数据库获取指定日期的基本面数据"""
        try:
            db = self.SessionLocal()
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
            analysis = db.query(FundamentalAnalysisDB).filter(FundamentalAnalysisDB.date == query_date).first()
            if analysis:
                return FundamentalAnalysis(
                    date=analysis.date,
                    supply_demand=analysis.supply_demand,
                    seasonal={"data": analysis.seasonal},
                    weather=analysis.weather,
                    crush_profit=analysis.crush_profit,
                    overall=analysis.overall,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at
                )
            return None
        except Exception as e:
            self.logger.error(f"获取基本面数据失败: {str(e)}")
            raise
        finally:
            db.close()

    def save_fundamental_data(self, date: str, data: Dict[str, Any]) -> None:
        """保存基本面数据到数据库"""
        try:
            db = self.SessionLocal()
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
            db_analysis = FundamentalAnalysisDB(
                date=query_date,
                supply_demand=data["supply_demand"],
                seasonal=data["seasonal"]["data"],
                weather=data["weather"],
                crush_profit=data["crush_profit"],
                overall=data["overall"]
            )
            db.merge(db_analysis)
            db.commit()
            self.logger.info(f"基本面数据已保存到数据库 - 日期: {date}")
        except Exception as e:
            self.logger.error(f"保存基本面数据失败: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()

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

    async def get_supply_demand_data(self) -> Dict[str, Any]:
        """获取供需平衡数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供最新的全球大豆和豆粕供需平衡数据，包括：\n1. 全球大豆产量及同比\n2. 全球豆粕产量及同比\n3. 中国豆粕消费量及同比\n4. 全球大豆库存及库存消费比\n\n请以如下JSON格式回答："
            prompt += """
{
    "global_soybean_production": {
        "value": 数值,
        "unit": "百万吨",
        "yoy": 同比增长率
    },
    "global_soymeal_production": {
        "value": 数值,
        "unit": "百万吨",
        "yoy": 同比增长率
    },
    "china_soymeal_consumption": {
        "value": 数值,
        "unit": "百万吨",
        "yoy": 同比增长率
    },
    "global_soybean_inventory": {
        "value": 数值,
        "unit": "百万吨",
        "inventory_ratio": 库存消费比
    }
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取供需平衡数据失败: {str(e)}")
            raise

    async def get_seasonal_pattern(self) -> list:
        """获取季节性规律数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请分析大豆和豆粕市场的季节性规律，包括不同时期的特点和影响因素。\n请以如下JSON格式回答，其中status需要根据当前月份动态判断："
            prompt += """
[
    {
        "period": "时间段",
        "pattern": "价格走势特点",
        "factors": "影响因素",
        "status": "符合规律/未到时间/即将进入",
        "status_type": "positive/negative/neutral"
    }
]"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取季节性规律数据失败: {str(e)}")
            raise

    async def get_weather_data(self) -> Dict[str, Any]:
        """获取天气数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供南美主要大豆产区的最新天气状况，包括巴西、阿根廷、巴拉圭/乌拉圭的主要产区。\n请以如下JSON格式回答："
            prompt += """
{
    "brazil": {
        "regions": [
            {
                "name": "产区名称",
                "condition": "天气状况描述"
            }
        ],
        "overall": "总体评价",
        "status_type": "success/warning/danger"
    },
    "argentina": {
        "regions": [
            {
                "name": "产区名称",
                "condition": "天气状况描述"
            }
        ],
        "overall": "总体评价",
        "status_type": "success/warning/danger"
    },
    "others": {
        "regions": [
            {
                "name": "国家名称",
                "condition": "天气状况描述"
            }
        ],
        "overall": "总体评价",
        "status_type": "success/warning/danger"
    },
    "summary": "天气对市场的整体影响分析"
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取天气数据失败: {str(e)}")
            raise

    async def get_crush_profit(self) -> Dict[str, Any]:
        """获取压榨利润数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请提供中国主要地区的大豆压榨利润数据。\n请以如下JSON格式回答："
            prompt += """
{
    "regions": [
        {
            "name": "地区名称",
            "soybean_cost": 大豆成本,
            "soymeal_price": 豆粕价格,
            "soyoil_price": 豆油价格,
            "profit": 利润,
            "weekly_change": 周环比变化
        }
    ],
    "summary": "压榨利润情况分析及对市场的影响"
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取压榨利润数据失败: {str(e)}")
            raise

    async def get_overall_assessment(self) -> Dict[str, Any]:
        """获取综合评估数据"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            prompt = f"今天是{current_date}，请对豆粕市场进行综合评估，包括短期、中期和长期展望。\n请以如下JSON格式回答："
            prompt += """
{
    "rating": {
        "score": 评分(0-100),
        "level": "看多/看空/中性/中性偏多/中性偏空"
    },
    "analysis": {
        "short_term": "短期分析",
        "medium_term": "中期分析",
        "long_term": "长期分析"
    }
}"""
            return await self._get_deepseek_response(prompt)
        except Exception as e:
            self.logger.error(f"获取综合评估数据失败: {str(e)}")
            raise

    async def get_fundamental_analysis(self, date: str) -> Dict[str, Any]:
        """获取完整的基本面分析数据"""
        try:
            self.logger.info(f"开始获取{date}的基本面分析数据")
            
            # 首先尝试从数据库获取
            cached_data = self.get_fundamental_data(date)
            if cached_data:
                self.logger.info(f"从数据库获取到基本面数据 - 日期: {date}")
                return cached_data.dict()

            self.logger.info("数据库中没有找到基本面分析数据，开始调用Deepseek API")
            # 获取各项数据
            supply_demand = await self.get_supply_demand_data()
            seasonal = await self.get_seasonal_pattern()
            weather = await self.get_weather_data()
            crush_profit = await self.get_crush_profit()
            overall = await self.get_overall_assessment()

            # 构建完整数据
            result = {
                "supply_demand": supply_demand,
                "seasonal": {"data": seasonal},
                "weather": weather,
                "crush_profit": crush_profit,
                "overall": overall
            }

            # 保存到数据库
            self.save_fundamental_data(date, result)
            
            # 转换为Pydantic模型并返回
            return FundamentalAnalysis(
                date=datetime.strptime(date, "%Y-%m-%d").date(),
                **result
            ).dict()
        except Exception as e:
            self.logger.error(f"获取基本面分析数据失败: {str(e)}")
            raise 