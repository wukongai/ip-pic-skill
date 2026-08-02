---
name: ip-pic
description: 为已授权角色规划和制作中文文章 IP 配图与静态视频关键帧。用户要求“IP 配图”“自定义角色配图”“文章人物插画”“文章连续多图”“中文图文融合”“静态视频关键帧”，或需要固定角色连续性、失败重做和逐图验收时使用。适合短文单图、长文批量以及方屏、横屏或竖屏静态画面。不用于知识卡片、封面、海报、视频剪辑或发布平台。
license: MIT
metadata:
  short-description: 完整 IP 配图导演、编译、渲染交接与 QA
  version: 0.3.0-rc.2
---

# IP 配图

**ORCHESTRATOR SKILL**

**INVOKES:** 本地编译器与一个图片后端。

**USE FOR:** IP 配图、自定义角色配图、文章人物插画、IP 静态关键帧。

**DO NOT USE FOR:** 知识卡片、封面、海报或发布平台。

## 流程

1. 按[用户选择](references/user-choice-flow.md)确认模式、画布、风格和角色权利。
2. 按[工作流内核](references/workflow-kernel.md)导演、编译和渲染；后端不得改写计划。
3. direct 融合中文；two-step 先做无字图再加字。
4. 执行[质量检查](references/qa-checklist.md)，最后由用户看图。

## Examples

普通用户可直接说“使用阿拓示例给这段文字配 1 张图”或“给这篇文章配图”。Agent 自动完成其余步骤，详见[用户手册](USER-GUIDE.zh-CN.md)。

技术见[维护者手册](MAINTAINER-GUIDE.zh-CN.md)，完整规则见[能力与资源](references/README.md)，许可见[NOTICE](NOTICE.md)。

## Error handling

缺少选择、权利或参考图时停止；拒绝覆盖；批量只重试失败项；人工验收前不声明视觉通过。
