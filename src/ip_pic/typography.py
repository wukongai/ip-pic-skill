"""Public direct-integrated typography recipe extracted from the original workflow."""

from __future__ import annotations


DIRECT_INTEGRATED_PROMPT_LINES = (
    "- 核心观点只保留 1 句，建议 8–18 个汉字，最多三行。",
    "- 主标题使用大号、厚重、端正的黑色中文展示字，视觉接近现代粗黑体或稳重的编辑型宋黑混合；笔画清楚、有分量，手机端也能一眼读清。",
    "- 禁止楷体、书法体、儿童体、细宋体、细字重和空心描边字；不要把主标题画成随意手写批注。",
    "- 全图最多一组强调线：只在核心观点下方画一条不规则手绘线，长度约为标题字块宽度的 55%–82%，不要每行都加线。",
    "- 栏目名使用正式、端正、中等偏粗的说明蓝字，参考 #4B79A6；不用手写体、儿童体或装饰体。",
    "- 补充判断使用更小的 medium 或 semibold 浅蓝字，参考 #6E93B7；与栏目名至少在字号、明度、字距三项中有两项不同。",
    "- 文字必须与人物动作、物件和信息路径形成一个整体，不得退化为独立海报标题卡或白色气泡框。",
    "- 不得同时使用整词红字、多条红线和红色框；黑色主标题、单条强调线和两级蓝字共同建立层级。",
)


def direct_integrated_prompt_lines() -> tuple[str, ...]:
    """Return the immutable original-style typography recipe."""

    return DIRECT_INTEGRATED_PROMPT_LINES
