# ip-pic · IP 配图

`ip-pic` 是一个可独立安装的 Codex Skill，用固定原创或已授权角色制作中文文章配图和静态视频关键帧。它保留完整 IP 导演、13 个正式结构、1 个兼容结构、6 种渲染风格、两种文字交付、参考图策略、批量连续性、失败重做和逐图 QA。

它不包含知识卡片、封面、海报、笔记系统、课程项目或内容发布平台，也不包含任何私有图片路由、凭证、余额和供应商容错实现。

第一次使用请从[傻瓜式用户手册](USER-GUIDE.zh-CN.md)开始；修改样式、新增风格和回退见[定制与个人 fork](references/customization.md)。

## 能力

- 文章：16:9、1:1、3:4、9:16 或自定义尺寸。
- 静态视频关键帧：16:9、1:1、9:16 独立构图。
- `direct-integrated`：一次生成少量可读中文，文字与人物、物件和动作融合；纯插画失败。
- `two-step-publish`：无字 raw + 确定性中文标题层；raw 与 final 分离。
- 方屏/竖屏关键帧：确定性栏目名、核心观点、红色强调线和补充文字。
- 人物导演：尺度、裁切、动作、表情、视线、头部姿态、身体重心和朝向。
- 批量：连续性轮换、部分失败、只重试失败项、整批新目录重建。
- 参考图：主参考、多参考、reference board、候选 handoff 与 selection receipt。
- 后端：Codex Image Tool、OpenAI Direct、宿主 ai-router、prompt-only。

## 安装

需要 Python 3.10+。

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

`pip install -e .` 应在完整 Skill clone 中执行。若从其他工作目录调用 console entry，请设置 `IP_PIC_HOME` 为该完整目录；模板和 profiles 不会被一个孤立的 Python 模块替代。

使用 OpenAI Direct 时再安装可选依赖：

```bash
python3 -m pip install -e '.[openai]'
export OPENAI_API_KEY='your-key-from-a-secure-shell-or-secret-manager'
```

不要把 key 写入 brief、JSON、Markdown、`.env*` 或仓库。

作为 Codex Skill 安装时，把整个目录复制或链接到个人/项目 Skill 目录，并确保目录名为 `ip-pic`。不要只复制 `SKILL.md`，因为模板、profiles、参考手册和脚本都是运行时依赖。

## 第一次运行

示例已使用公开原创教程角色“学习向导阿拓”：

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/article-brief.json \
  --output-dir outputs/ato-article \
  --print-prompt
```

编译器输出：

- `image_brief.json`
- `ip-director-plan.json`
- `*.prompt.md`
- `run-manifest.json`
- `image-render-handoff/v1`

编译不会调用图片 API。

## 四种渲染路径

### 1. Codex Image Tool

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/ato-article/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/ato-article/codex-request.json
```

宿主 Agent 读取 request 中未经改写的 prompt、size 和授权素材，调用 Codex Image Tool，把真实文件写到 `expected_output`。完成后：

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/ato-article/codex-request.json \
  --output outputs/ato-article/image/ato-intelligence-value.png \
  --receipt-id host-run-id
```

文件不存在、是符号链接或路径与请求不一致时，finalize 失败。

### 2. OpenAI Direct

```bash
python3 scripts/render_ip_pic.py openai-direct \
  --manifest outputs/ato-article/run-manifest.json \
  --request outputs/ato-article/openai-request.json \
  --model gpt-image-2 \
  --quality high
```

实现使用 OpenAI Image API 的 `images.generate`。当前 direct adapter 对带参考图的 handoff 失败关闭；这类任务请用 Codex Image Tool 或宿主 ai-router，以免静默丢失人物参考。

官方接口说明：[OpenAI Image generation](https://developers.openai.com/api/docs/guides/image-generation)。

### 3. 宿主 ai-router

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/ato-article/run-manifest.json \
  --backend host-ai-router \
  --request outputs/ato-article/ai-router-request.json
```

仓库不包含 ai-router 的 provider、adapter、凭证、余额、重试或 fallback。宿主调用完成后仍必须使用 `finalize` 回填真实文件回执。

### 4. prompt-only

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/ato-article/run-manifest.json \
  --backend prompt-only \
  --request outputs/ato-article/prompt-only.json
```

状态为 `prompt_ready`、`rendered=false`；它不会伪装成渲染成功。

## 交付模式

### direct-integrated

prompt 首、中、尾三处都要求图文融合。最终图必须含少量、短、可读的中文标题或标签，并与当前判断和角色动作有直接关系。QA 中 `integrated_text_present` 或 `integrated_text_legible` 为 false 时，只重做渲染层。

默认直出文字沿用原版宿主的中文字体系：主标题使用较粗、端正的黑色中文展示字，接近现代粗黑体或稳重的编辑型宋黑混合；标题下只画单条不规则手绘强调线，栏目名和补充判断分别使用两级说明蓝。该模式仍由模型一次完成图文融合，不切换为 `two-step-publish`，也不做二次文字叠加；不同图片允许存在少量字形波动，但楷体、书法体、儿童体、细宋体和空心描边字均视为失败信号。

### two-step-publish

raw prompt 禁止文字。取得 raw 后运行 `python3 scripts/compose_publish_layout.py --run-manifest <run-manifest.json>`，生成独立 final 和 `.layout-result.json`。发布层从 raw 边缘采样背景色，确定性排版，不覆盖 raw。

选择该模式时必须同时确认标题带：`editorial-ink-v2` 保留原版较粗的
中文字重和墨线层级，`editorial-warm-v1` 保留兼容暖纸层级。把选择写入
`selection_receipt.publish_extension_id`；编译器会将它写入
`publish_layout.extension_id`，不存在的标题带会在生图前失败关闭。

### 静态视频关键帧

先编译 `examples/video-square-brief.json`，编译器会同时输出
`video-text-overlay.json`。渲染无字 raw 后运行：

```bash
python3 scripts/compose_video_keyframe_text.py --manifest path/to/overlay.json
```

方屏支持 `square-left` / `square-right`，竖屏支持 full-frame、subtitle-safe 等原版布局；安全区违规会失败。

## 角色与参考图

内置教程角色：

- `profiles/characters/ato/profile.json`
- `profiles/characters/wukong/profile.json`
- `profiles/characters/moon-rabbit/profile.json`

自定义角色 profile 必须写明权利依据并含 3–5 个 continuity anchors。参考图只在 `visual.authorized_assets` 登记，每项含 `path / purpose / ownership / required`。用户图片不会嵌入 prompt 正文。

## 批量、重试和整批重建

Python API：

```python
from ip_pic.batch import build_shot_plan, run_batch, retry_failed, rebuild_batch
```

方屏批次轮换六种构图家族。相邻镜头不重复 family、crop、orientation 与 action；最近六张至少四种 family。`retry_failed` 不重新编译成功项。`rebuild_batch` 强制新目录并过滤旧输出树中的参考素材。

## QA

```python
from ip_pic.qa import evaluate_image
```

传入由真实看图流程得到的观察值。全项通过只生成 `checks_passed / pending_human`，不会自动批准发布。最终仍需人工观察：

- 同一角色跨风格是否稳定；
- 文字是否真实可读并与画面融合；
- 构图是否体现不同结构，而不是换模板名；
- 长批次动作、表情、视线、尺度与姿态是否轮换；
- two-step 和视频文字层是否符合层级与安全区。

## 验证

```bash
python3 -m unittest discover -s tests -v
IMAGE_FACTORY_SOURCE=/path/to/read-only/source \
IP_PIC_PRIVATE_SOURCE_ID=private-source-id \
python3 scripts/verify_parity.py \
  --manifest parity/ip-parity-manifest.json \
  --source-root "$IMAGE_FACTORY_SOURCE"
python3 scripts/verify_release.py
```

双端 parity 使用私有事实源时才运行；公开发行不包含该源。结构测试、真实文件 E2E 和人工视觉验收是三个不同层级。

## 许可证

本项目代码使用 MIT License。工作流方法派生自 MIT 许可的 Ian Xiaohei Illustrations，保留原许可证和署名于 `UPSTREAM-LICENSE.txt`、`NOTICE.md`、`upstream.lock.json`。本项目不分发上游角色或示例图片。
