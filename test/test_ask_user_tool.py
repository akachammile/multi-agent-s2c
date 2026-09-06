"""验证正式提问工具的模型 Schema 和多问题 checkpoint 载荷。"""

import json
import runpy
import unittest
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

# 单独加载工具定义，避免导入 LeaderAgent 时加载模型、数据库和其他服务。
ask_user = runpy.run_path(str(Path(__file__).resolve().parents[1] / "src/agents/leaderagent/tools.py"))["ask_user"]


class AskUserToolTest(unittest.IsolatedAsyncioTestCase):
    """检查一个工具调用携带多个问题并分别接收答案。"""

    async def test_question_schema_and_interrupt_resume(self) -> None:
        """模型可见嵌套字段，恢复后保留不同问题各自的答案。"""
        schema = convert_to_openai_tool(ask_user)["function"]["parameters"]
        question_schema = schema["properties"]["questions"]["items"]
        self.assertEqual(set(question_schema["required"]), {"question_id", "question", "options"})
        self.assertEqual(question_schema["properties"]["question"]["description"], "需要用户回答的具体问题")
        option_schema = question_schema["properties"]["options"]["items"]
        self.assertEqual(set(option_schema["required"]), {"label", "value"})
        self.assertEqual(option_schema["properties"]["value"]["description"], "回答时使用的选项值")

        questions = [
            {
                "question_id": "database",
                "question": "请选择数据库",
                "options": [{"label": "PostgreSQL", "value": "postgresql"}],
            },
            {
                "question_id": "environment",
                "question": "请选择部署环境",
                "options": [{"label": "本地部署", "value": "local"}],
            },
        ]
        builder = StateGraph(MessagesState)
        builder.add_node("tools", ToolNode([ask_user]))
        builder.add_edge(START, "tools")
        builder.add_edge("tools", END)
        graph = builder.compile(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "ask-user-multiple-questions"}}
        await graph.ainvoke(
            {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[{"name": "ask_user", "args": {"questions": questions}, "id": "ask-1", "type": "tool_call"}],
                    )
                ]
            },
            config,
        )
        state = await graph.aget_state(config)
        self.assertEqual(len(state.interrupts), 1)
        self.assertEqual(state.interrupts[0].value, {"kind": "ask_user", "questions": questions})
        self.assertFalse(any(isinstance(message, ToolMessage) for message in state.values["messages"]))

        answers = {"database": "postgresql", "environment": "local"}
        await graph.ainvoke(Command(resume={state.interrupts[0].id: answers}), config)
        state = await graph.aget_state(config)
        self.assertEqual(state.interrupts, ())
        self.assertEqual(state.next, ())
        results = [message for message in state.values["messages"] if isinstance(message, ToolMessage)]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].tool_call_id, "ask-1")
        self.assertEqual(json.loads(results[0].content), answers)


if __name__ == "__main__":
    unittest.main()
