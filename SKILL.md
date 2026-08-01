---
name: ip-pic
description: 为中文文章和静态视频关键帧规划、编译并验收固定原创或已授权 IP 配图。支持 16:9、1:1、3:4、9:16，direct-integrated 图文融合、two-step-publish 确定性中文层、六种渲染风格、批量连续性、参考图选择与失败重做。用户说“IP 配图”“自定义角色配图”“文章人物插画”“IP 静态关键帧”时使用；不用于知识卡片、封面、海报、笔记库或发布平台业务。
metadata:
  short-description: 完整 IP 配图导演、编译、渲染交接与 QA
---

# IP 配图

把文章中的判断、转折、事实或流程转成带固定角色的正文解释图或静态视频关键帧。角色必须原创或已获授权。不要生成 Ian Xiaohei 的角色，也不要复刻其示例图；本 Skill 只继承经 MIT 许可的工作流方法，署名见 `NOTICE.md`。

## 输入、输出与停止条件

- 输入：文章正文或视频关键帧文案、角色 profile 与权利依据、用户确认的业务类型、交付模式、画布和风格。
- 输出：selection receipt、内容导演计划、结构模板、prompt、参考图计划、render handoff、逐图 manifest、后端回执和 QA receipt；`two-step-publish` 另输出不覆盖 raw 的确定性文字 final。
- 停止/禁止：缺少用户选择、角色权利依据或必要参考素材时停止；禁止接管知识卡片、封面、海报、OB、布丁、训练营或发布平台工作流，禁止覆盖既有输出。

## 开始前必须确认

按 `references/user-choice-flow.md` 获取 `selection_receipt/v1`，分别确认：

1. `business_type`：`ip_article_illustration` 或 `ip_video_keyframe`；
2. `delivery_mode`：`direct-integrated` 或 `two-step-publish`；
3. `canvas`：16:9、1:1、3:4、9:16 或合法自定义尺寸；
4. `style_variant_id`：六种原版渲染风格之一；
5. 选择 `two-step-publish` 时，另确认 `publish_extension_id`：
   `editorial-ink-v2`（原版粗体墨线）或 `editorial-warm-v1`（兼容暖纸）。

用户未明确选择或接受推荐时停止编译。角色 profile 必须含 ownership、identity、appearance、personality、continuity_anchors；没有权利依据时停止。

## 工作流

1. 短文选一个认知锚点；长文从标题、段落转折和结论规划 4–8 张，不平均切字数。见 `references/workflow-kernel.md`。
2. 为每张图运行内容导演，确定 structure、composition family、人物尺度、裁切、朝向、动作、表情、视线和姿态。显式专家覆盖优先。
3. 从 13 个正式结构与 1 个兼容结构中选择场景兼容模板；渲染风格只覆盖线条、材质、色彩和表面语气。
4. 按 `references/prompt-template.md` 编译 prompt、director plan、reference plan、render handoff 和 manifest。
5. `direct-integrated` 必须一次生成少量可读中文并与人物动作、物件关系融合；纯插画判定失败。
6. `two-step-publish` 先生成无字 raw，再用确定性发布层生成 final；raw 不得冒充 final，也不得覆盖。
7. 视频关键帧先生成无字 raw，再运行 `scripts/compose_video_keyframe_text.py`；方屏和竖屏独立构图。
8. 四条后端只消费同一个 handoff：Codex Image Tool、OpenAI Direct、宿主 ai-router 或 prompt-only。后端不得改写导演、模板、prompt 或 QA。
9. 逐张执行 `references/qa-checklist.md`。自动结构检查不能替代真实看图；只有用户完成人工视觉验收后才能声称视觉通过。

## 批量与重建

- 相邻镜头不得重复 `composition_family + crop + orientation + action`。
- 最近六张至少覆盖四种方屏构图家族，并包含坐姿、俯视局部、双手近景和装置主导。
- 单项失败不终止整批；成功项保持不动，失败重试只消费失败项。
- “全部重做”必须新建输出目录与 shot plan，不得把旧 raw、旧 prompt 或否决图片放入参考集合。

完整规约见 `references/full-rebuild-playbook.md`。

## 命令入口

```bash
python3 scripts/compile_ip_pic.py --brief examples/article-brief.json --output-dir outputs/example
python3 -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

渲染配置、安装方式和真实 E2E 见 `README.zh-CN.md`。所有输出默认新建；已有目录、raw、final、回执或符号链接均拒绝覆盖。
