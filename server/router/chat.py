from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from src.agents import agent_manager

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    messages: list[dict] = Field(..., description="对话消息列表")
    model: str | None = Field(default=None, description="指定模型")


class ChatResponse(BaseModel):
    content: str = Field(..., description="回复内容")
    model: str = Field(..., description="使用的模型")


@router.post("agent/{agent_id}/run")
async def chat(agent_id: str, request: ChatRequest):
    """对话接口，支持流式/非流式"""
    agent = agent_manager.get_agent("deepagents")
    print(type(agent))
    agent.stream({"messages": "xxxxx"})

    return response


async def _stream_chat(request: ChatRequest):
    """流式输出生成器"""
    # TODO: 接入 agent 的 stream 方法
    yield "data: [DONE]\n\n"
