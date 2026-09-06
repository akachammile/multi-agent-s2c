"""统一中断提问数据的外层结构。"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AskHumanPayload:
    """服务端提问载荷，关联会话和产生中断的 Run。"""

    thread_id: str
    run_id: str
    questions: list[Any]
    kind: str = "ask_user"


def parse_interrupt_questions(questions: Any) -> list[Any]:
    """列表原样返回，单个问题字典包装为列表，其他类型报错。"""
    if isinstance(questions, list):
        return questions
    if not isinstance(questions, dict):
        return []
    raise ValueError("questions 必须是列表或单个问题字典")
