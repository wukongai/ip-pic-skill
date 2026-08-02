---
name: ip-pic
description: 为已授权角色制作中文文章 IP 配图和静态视频关键帧。用户说“IP 配图”“自定义角色配图”“文章人物插画”时使用；包含完整导演、两种文字交付、13 个结构、六种风格、批量连续性、重做和逐图 QA。先确认角色权利和用户选择，再生成并逐图检查，最终必须由用户真实看图。不用于知识卡片、封面、海报或发布平台。
license: MIT
metadata:
  short-description: 完整 IP 配图导演、编译、渲染交接与 QA
  version: 0.3.0-rc.2
---

# IP 配图

**USE FOR:** IP 配图、自定义角色配图、文章人物插画、IP 静态关键帧。

**DO NOT USE FOR:** 知识卡片、封面、海报或发布平台。

## 流程

1. 按[用户选择](references/user-choice-flow.md)确认模式、画布、风格和角色权利。
2. 按[工作流内核](references/workflow-kernel.md)导演、编译和渲染；后端不得改写计划。
3. direct 一次融合中文；two-step 先做无字图再确定性加字。
4. 逐图执行[质量检查](references/qa-checklist.md)，最后由用户看图。

## Examples

普通用户可直接说“给下面这段文字配 1 张图”或“给这篇文章配图”。首次按[用户手册](USER-GUIDE.zh-CN.md)确认阿拓参考图，其余步骤由 Agent 完成。

技术见[维护者手册](MAINTAINER-GUIDE.zh-CN.md)，样式见[定制](references/customization.md)，完整索引见[能力与资源](references/README.md)，许可见[NOTICE](NOTICE.md)。

## Error handling

缺少选择、权利或参考图时停止；拒绝覆盖；批量只重试失败项；人工验收前不声明视觉通过。
