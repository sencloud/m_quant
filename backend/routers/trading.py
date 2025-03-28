from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.trading import OptionsStrategy
from utils.logger import logger
import httpx
from config import settings
import json
from openai import OpenAI
from fastapi.responses import StreamingResponse
import asyncio
from starlette.background import BackgroundTask

router = APIRouter()

# 初始化OpenAI客户端
client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

async def stream_response(response, request: Request):
    reasoning_content = ""
    content = ""
    
    try:
        for chunk in response:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                logger.info("客户端断开连接")
                break
                
            try:
                if chunk.choices[0].delta.reasoning_content:
                    reasoning_content += chunk.choices[0].delta.reasoning_content
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_content})}\n\n"
                elif chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            except Exception as e:
                logger.error(f"处理chunk时出错: {str(e)}")
                continue
        
        # 发送完成标记
        yield f"data: {json.dumps({'type': 'done', 'reasoning': reasoning_content, 'content': content})}\n\n"
    except Exception as e:
        logger.error(f"流式响应出错: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        logger.info("流式响应结束")

@router.get("/options")
async def get_options_strategies(request: Request):
    """获取期权策略分析"""
    try:
        prompt = """基于今天的豆粕市场环境，我做出如下交易选择，你评估下是否合适
开空：豆粕2509合约期货
买多2509 3200的期权
买跌2505 2750的期权"""
        
        logger.info(f"开始调用Deepseek API，prompt: {prompt}")
        
        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            return StreamingResponse(
                stream_response(response, request),
                media_type="text/event-stream",
                background=BackgroundTask(logger.info, "请求处理完成")
            )
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API调用失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"获取期权策略分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-strategy")
async def generate_strategy(prompt: str, request: Request):
    """根据提示生成交易策略"""
    try:
        logger.info(f"开始生成策略，prompt: {prompt}")
        
        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            return StreamingResponse(
                stream_response(response, request),
                media_type="text/event-stream",
                background=BackgroundTask(logger.info, "请求处理完成")
            )
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API调用失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"生成策略失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 