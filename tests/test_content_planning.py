from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ip_pic.content import plan_article_slots  # noqa: E402


class ContentPlanningTests(unittest.TestCase):
    def test_short_article_produces_one_cognitive_anchor(self) -> None:
        slots = plan_article_slots(
            "情报不等于价值。真正的价值来自过滤噪声、形成判断并推动行动。"
        )
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]["id"], "article-slot-01")
        self.assertTrue(slots[0]["content_outline"]["headline"])

    def test_long_article_produces_four_to_eight_semantic_slots(self) -> None:
        article = """
# 为什么工具越多，工作反而越慢

团队先把问题误判成工具不足，于是不断新增入口。

## 入口不是能力

一个入口只有在连接清晰流程时才有价值，否则只是新的记忆负担。

## 先判断任务

先判断任务是一次性动作、稳定流程还是需要长期维护的系统。

## 再选择结构

不同任务应落到不同结构，不能用同一模板覆盖全部场景。

## 给失败留回路

失败项应单独重试，已经通过的结果必须保留。

## 用验收结束

结构测试不能代替真实视觉验收，最终还要观察文字、人物和构图。
"""
        slots = plan_article_slots(article)
        self.assertGreaterEqual(len(slots), 4)
        self.assertLessEqual(len(slots), 8)
        headlines = [slot["content_outline"]["headline"] for slot in slots]
        self.assertIn("入口不是能力", headlines)
        self.assertIn("给失败留回路", headlines)
        self.assertEqual(len(headlines), len(set(headlines)))
        self.assertTrue(
            all(slot["source"]["selection_basis"] == "cognitive-anchor" for slot in slots)
        )


if __name__ == "__main__":
    unittest.main()
