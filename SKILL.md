---
name: custom-ip-illustration
description: 为文章、脚本和关键帧规划并生成用户自有或获授权的固定 IP 角色配图，负责角色 onboarding、动作构图、prompt 编译、图片后端自动选择和视觉 QA。Use when users ask for custom IP illustrations, consistent character art for articles or keyframes, or images based on owned or authorized character references. Do not use for generic non-character art, knowledge cards, covers, video or audio work, or unlicensed character imitation.
---

# Custom IP Illustration

把内容编译成角色一致、可审计的配图请求，并把真实生图交给宿主已经拥有的图片工具。

## 核心边界

- 只使用用户自有、已授权或有明确许可证的角色资料。
- 不内置默认人物，不在缺少合法 `ip-profile/v1` 时猜测角色。
- 不收集 API key、token、cookie、base URL、provider 或模型参数。
- 编译器只生成 prompt、参考素材清单和 provider-neutral render request，不联网、不调用图片 API。
- 用户只要求方案或没有可用图片后端时，诚实交付 `compile_only`，不得声称已经出图。
- 不把用户授权素材库存全部传给图片模型；每张图只选择本次需要的参考素材。

## 工作流

1. 判断请求是否命中本 Skill；普通无角色配图、知识卡片、封面海报、视频剪辑和音频任务交给对应能力。
2. 按顺序发现角色资料：用户本次明确提供的资料或路径、当前项目 `.custom-ip-illustration/ip-profile.json`。两处都没有时进入下方“首次使用引导”，不得猜测角色。
3. 验证 `ownership.status`。缺失、未知或明确无授权时立即停止，不编译、不调用图片工具。
4. 读取第一份存在的偏好文件：项目级 `.custom-ip-illustration/EXTEND.md`、XDG 配置、用户级配置。没有时使用 `auto` 默认值。
5. 按 [内容导演工作流](references/workflow.md) 选择认知锚点、物理隐喻、角色动作、表情、镜头和画幅模板。一张图只解释一个判断或转折。
6. 以用户项目为工作目录，先从当前 `SKILL.md` 定位已安装 Skill 根目录，再运行 `python3 <skill-root>/scripts/compile_ip_illustration.py`。不得假设脚本位于用户项目。每张图必须先落盘 `prompts/NN-*.md`，再考虑生图。
7. 按下方唯一一份后端规则解析图片工具。
8. 用户已经明确要求“生成、制作、出图”时，该请求即授权本次图片生成；只要求规划、prompt 或 dry-run 时不得调用后端。
9. 每张图片独立调用选定后端，传递 prompt、画幅、输出路径和本次选中的参考图。不得传递 provider 路由字段。
10. 按 [QA playbook](references/qa-playbook.md) 分开执行技术检查、Agent 视觉检查和用户最终确认。部分失败必须逐张报告。

## 首次使用引导

缺少角色资料时读取 [IP onboarding](references/ip-onboarding.md)，按以下状态推进：

1. 用一句话说明需要先建立获授权的角色资料，然后一次只问一个选择：使用仓库虚构人物跑教程，还是建立用户自己的角色。
2. 用户选择教程时，明确说明 Mira 是本仓库原创的虚构示例、只用于本次教程，不是默认角色；读取 `examples/ip-profile.example.json` 和 `examples/brief.example.json`。不得把示例资料保存为用户资料。
3. 用户选择自己的角色时，一次只问一个关键问题，依次收集 ownership、identity、appearance、personality、continuity anchors 和可选参考图。
4. 收集完成后先展示人类可读摘要和拟保存位置。只有用户明确确认后，才把资料保存到项目 `.custom-ip-illustration/ip-profile.json`；覆盖既有资料也必须再次确认。
5. 再确认内容、图片数量、画幅、输出目录，以及本次是只编译还是生成图片。不要询问 Router、provider、模型、服务地址或 API 凭证。

## Image Generation Tools

每次请求按以下顺序选择：

1. 当前请求明确指定且当前可用的 backend；
2. `EXTEND.md` 保存且当前可用的 `preferred_image_backend`；
3. 宿主原生图片生成工具；
4. 当前唯一可用的非原生图片 backend；
5. 存在多个非原生 backend 时询问用户一次；
6. 没有可用图片工具时返回 `compile_only`，保留完整 prompt 和 render request。

`preferred_image_backend: auto` 是默认值。偏好失效时继续向后解析，不调用不存在的 backend。不要向普通用户询问 Router、provider、模型或 API 参数。详细判定和结构化 inventory 见 [backend selection](references/backend-selection.md)。

## 输入

- 内容：文章、段落、脚本或结构化要点。
- `ip-profile/v1`：ownership、identity、appearance、personality、continuity anchors 和可选授权参考图。
- `ip-illustration-brief/v1`：标题、内容、画幅、风格和图片数量。
- 输出目录：独立的 CLI / Agent 运行参数，不写进 brief。
- 可选偏好：风格、画幅、输出目录、批量数、语言和 backend id。

示例位于 `examples/`。示例人物只可在用户明确选择教程时使用，不得误认为默认角色。

## 输出

- `prompts/NN-*.md`
- `render-request.json`
- `run-manifest.json`
- 后端可用且本次已授权时的图片文件
- `qa-report.json` 或逐图 QA 结论

所有运行产物写入用户指定目录，不写入 Skill 根目录。

## 停止点

- 缺少角色 ownership 或角色明确未获授权。
- 用户要求复刻受保护角色，但不能证明拥有权利。
- 输出目录位于 Skill 根目录。
- 多个第三方 backend 可用而用户尚未选择。
- 请求的 backend 不存在且没有可用 fallback。
- 参考图路径失效且身份一致性依赖该图。
- 图片生成需要额外付费或外部动作，但当前请求只授权规划。

## 资源路由

- 首次建立角色资料：`references/ip-onboarding.md`
- 内容、动作、构图和画幅：`references/workflow.md`
- 后端选择：`references/backend-selection.md`
- 逐图审查：`references/qa-playbook.md`
- 扩展模板、profile 和 renderer：`references/extensions.md`

## 验证

从 Skill 根目录运行：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_release.py --root . --manifest public-release-manifest.json
```
