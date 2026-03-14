from _curses import meta
from dataclasses import dataclass, field
from src.configs.config import config as sys_config
from src.agents.common.base_context import BaseContext


@dataclass
class DeepAgentContext(BaseContext):

    system_prompt: str = field(
        default="你是一个深度研究智能体", metadata={"description": "系统提示词"}
    )
    sub_model: str = field(
        default="dashscope/qwen3.5-plus", metadata={"description": "子模型"}
    )
    flash_model: str = field(
        default=sys_config.flash_model, metadata={"description": "快速模型"}
    )
