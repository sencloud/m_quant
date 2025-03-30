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
        
        prompt = f"""请基于{date}的市场数据，对豆粕期货和期权市场进行全面分析，必须从数据出发，不能做任何假设，只能从互联网上获取数据，或根据你已有的知识，包含以下维度：

1. 库存周期验证
- 当前库存水平及其对价格的影响
- 库存拐点预判，重点关注巴西大豆到港量
- 提供环比和同比变化数据

2. 技术面分析
- 周线趋势研判，包括波浪理论分析
- 日线和小时线关键支撑压力位
- 波动率分析及相应期权策略建议

3. 历史价格分析
- 十年历史价格区间分析
- 季节性规律研究

4. 资讯与政策影响
- 短期可能的利多因素分析
- 潜在风险事件评估

5. 生猪市场联动分析
- 从需求端验证市场状况
- 替代品（如菜粕）对市场的影响

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
