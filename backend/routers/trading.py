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
                    print(chunk.references)
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
        
        prompt = f"""请基于{date}的豆粕及豆粕强相关联的品种市场数据，对豆粕ETF、豆粕期货和豆粕期权市场进行全面分析，必须从数据出发，不能做任何假设，只能从互联网上获取最新数据，同时结合你已有的金融知识，对下一个交易日给出交易策略建议，包含以下维度：

1、盘中分析：
- 豆粕ETF、豆粕期货和豆粕期权市场分析
2、交易策略建议：
- 给出交易策略建议
3、组合策略建议：
- 给出组合策略建议
4、风险管理：
- 给出风险管理建议
5、关联品种分析：
- 给出关联品种分析

请提供详细的数据支持和具体的价格区间。"""
        
        try:
            response = client.chat.completions.create(
                model="bot-20250329163710-8zcqm",
                messages=[{"role": "system", "content": "你是DeepSeek，是一个金融领域专家"}, {"role": "user", "content": prompt}],
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
