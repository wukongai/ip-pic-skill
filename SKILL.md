---
name: ip-pic
description: 为已授权角色规划、编译并验收中文文章 IP 配图和静态视频关键帧。用户说“IP 配图”“自定义角色配图”“文章人物插画”“IP 静态关键帧”时使用；支持两种交付模式、四种画布、13 个结构、六种风格、批量连续性与失败重做。先确认用户选择与角色权利，再编译并逐图 QA。不用于知识卡片、封面、海报或发布平台。
license: MIT
metadata:
  short-description: 完整 IP 配图导演、编译、渲染交接与 QA
  version: 0.3.0-rc.2
---

# IP 配图

**ORCHESTRATOR SKILL**

**INVOKES:** compiler + render backend.

**USE FOR:** IP 配图、自定义角色配图、文章人物插画、IP 静态关键帧。

**DO NOT USE FOR:** 知识卡片、封面、海报或发布平台。

## 必须流程

1. 读[用户选择](references/user-choice-flow.md)，确认业务、交付模式、画布和风格；校验角色 ownership 与授权素材。
2. 按[工作流内核](references/workflow-kernel.md)运行内容导演并编译；后端不得改写导演计划。
3. `direct-integrated` 一次生成融合中文；`two-step-publish` 先生成无字 raw，再叠加确定性文字 final。
4. 后端只消费同一 handoff。逐图执行[质量检查](references/qa-checklist.md)，再由用户真实看图。

新手/E2E：[用户手册](USER-GUIDE.zh-CN.md)。样式/字体：[定制](references/customization.md)。完整索引：[能力与资源](references/README.md)。许可：[NOTICE](NOTICE.md)。

## Examples

```bash
python3 scripts/compile_ip_pic.py --brief examples/article-brief.json --output-dir outputs/example
python3 scripts/verify_release.py
```

## Error handling

缺少选择、权利或参考图时停止；拒绝覆盖；批量只重试失败项；人工验收前不声明视觉通过。
