from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from src.agents import agent_manager

router = APIRouter(prefix="/chat", tags=["chat"])




@router.post("/agent/{agent_id}/run")
async def chat(agent_id: str):
    """对话接口，支持流式/非流式"""
    agent = agent_manager.get_agent("DeepAgent")
    response = await agent.stream({"messages": "你好"})
    return {"content": response["messages"][1].content}
