from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
from models.trading import OptionsStrategy, DailyStrategyAnalysis
from services.trading import TradingService
from utils.logger import logger
import httpx
from config import settings
import json
from openai import OpenAI
from fastapi.responses import StreamingResponse
import asyncio
from starlette.background import BackgroundTask
from datetime import datetime

router = APIRouter()

# 初始化OpenAI客户端
client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots"
)

def get_trading_service() -> TradingService:
    return TradingService()

async def stream_response(response, request: Request, date: str):
    reasoning_content = ""
    content = ""
    
    try:
        for chunk in response:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                logger.info("客户端断开连接")
                break
                
            try:
                if hasattr(chunk, "references"):
                    pass
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                elif hasattr(chunk.choices[0].delta, "reasoning_content"):
                    reasoning_content += chunk.choices[0].delta.reasoning_content
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_content})}\n\n"
                    
            except Exception as e:
                logger.error(f"处理chunk时出错: {str(e)}")
                continue
        
        # 发送完成标记
        yield f"data: {json.dumps({'type': 'done', 'reasoning': reasoning_content, 'content': content})}\n\n"
        
        # 保存到数据库
        try:
            trading_service = TradingService()
            analysis = DailyStrategyAnalysis(
                date=date,  # 使用用户选择的日期
                content=content,
                reasoning_content=reasoning_content
            )
            trading_service.save_strategy_analysis(analysis)
            logger.info(f"策略分析已保存到数据库 - 日期: {date}")
        except Exception as e:
            logger.error(f"保存策略分析到数据库失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"流式响应出错: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        logger.info("流式响应结束")

@router.get("/options")
async def get_options_strategies(
    date: str,
    request: Request,
    trading_service: TradingService = Depends(get_trading_service)
):
    """获取期权策略分析"""
    try:
        # 首先尝试从数据库获取
        analysis = trading_service.get_strategy_analysis(date)
        if analysis:
            logger.info(f"从数据库获取到策略分析 - 日期: {date}")
            return {
                "content": analysis.content,
                "reasoning_content": analysis.reasoning_content
            }

        # 如果数据库中没有，则调用Deepseek API
        logger.info("数据库中没有找到策略分析，开始调用Deepseek API")

        # 获取交易数据
        trading_data = trading_service.get_trading_data()
        if not trading_data or 'raw_data' not in trading_data:
            raise HTTPException(status_code=500, detail="获取交易数据失败")

        raw_data = trading_data['raw_data']
        prompt = f"""我需要生成一份提示词，其核心目标是：基于多维度数据生成豆粕主力合约（{raw_data['main_contract']}）下一个交易日的交易操作策略。 目前我已经有如下框架，请帮我把【】内的数据说明用最新的互联网资讯补充完成（最好是今天的），并将补完后的这份提示词完整返回给我。
                请直接返回提示词，不需要其他任何额外的文字，特别是引用参考和来源，不要出现任何的引用和来源，还有markdown语法字符也不能出现。

``` 目标：基于多维度数据生成豆粕主力合约（{raw_data['main_contract']}）下一个交易日（{raw_data['next_day']}）的量化策略，不要出现任何的引用和来源。
一、实时价格与技术指标
{trading_data['price_analysis']}
{trading_data['technical_analysis']}
{trading_data['volume_analysis']}
二、基本面与市场情绪 【请补充供应端数据（进口大豆到港量、油厂开机率、豆粕库存）、需求端数据（饲料企业采购量、替代品价格）】
三、国际市场联动
1、【请补充隔夜CBOT美豆走势情况】
2、【请补充USDA出口销售数据和巴西贴水情况】
3、人民币汇率：{raw_data['usd_cny']}。
四、资金与政策风险
1、【请补充机构行为，包括净空、净多头寸、机构仓位变化情况】。
2、政策风险 中美关税：美豆进口关税138%，远月成本支撑，但5月前到港压力主导。
3、【请补充天气炒作情况】
4、【请补充基差变化】
5、【请补充突发事件】 ```
"""
        logger.info(f"生成提示词：{prompt}")
        try:
            response = client.chat.completions.create(
                model="bot-20250329163710-8zcqm",
                messages=[{"role": "system", "content": "你是DeepSeek，是一个提示词工程专家"}, {"role": "user", "content": prompt}],
                stream=False
            )
            content = response.choices[0].message.content
            logger.info(f"生成提示词：{content}")

            response = client.chat.completions.create(
                model="bot-20250329163710-8zcqm",
                messages=[{"role": "system", "content": "现在你是一个豆粕期货量化策略专家，请根据我给你的提示词，生成一份豆粕期货交易操作策略。"}, {"role": "user", "content": content}],
                stream=True
            )

            return StreamingResponse(
                stream_response(response, request, date),
                media_type="text/event-stream",
                background=BackgroundTask(logger.info, "请求处理完成")
            )
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API调用失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"获取期权策略分析失败: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
