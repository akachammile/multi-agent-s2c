"""验证提问数据的外层结构转换。"""

import runpy
import unittest
from pathlib import Path

# 避免加载 server.utils 包时初始化无关的认证和 Worker 依赖。
parse_interrupt_questions = runpy.run_path(str(Path(__file__).resolve().parents[1] / "server/utils/interrupt_utils.py"))["parse_interrupt_questions"]


class InterruptQuestionsTest(unittest.TestCase):
    """只检查外层转换，不限制问题和选项内容。"""

    def test_list_passthrough(self) -> None:
        """空列表及未经校验的列表都保持原样。"""
        for questions in ([], [{"question_id": "drink"}], [None]):
            with self.subTest(questions=questions):
                self.assertIs(parse_interrupt_questions(questions), questions)

    def test_single_question(self) -> None:
        """单个问题包装后保留原问题及多个选项。"""
        question = {
            "question_id": "drink_type",
            "question": "下午你想喝哪一类饮品？",
            "options": [
                {"label": "咖啡（提神）", "value": "coffee"},
                {"label": "茶（清爽）", "value": "tea"},
                {"label": "无咖啡因／甜饮", "value": "no_caffeine"},
            ],
        }
        result = parse_interrupt_questions(question)
        self.assertEqual(len(result), 1)
        self.assertIs(result[0], question)
        self.assertEqual(parse_interrupt_questions({}), [{}])

    def test_unsupported_type(self) -> None:
        """其他类型明确报错，不猜测或转换内容。"""
        for questions in (None, "问题", 123, ()):
            with self.subTest(questions=questions), self.assertRaisesRegex(ValueError, "questions 必须是列表或单个问题字典"):
                parse_interrupt_questions(questions)


if __name__ == "__main__":
    unittest.main()
