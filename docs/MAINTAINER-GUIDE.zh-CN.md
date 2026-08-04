# IP Pic 维护者技术手册

这份文件保留完整的命令、配置、合同、测试和扩展说明，供 Agent、开发者与维护者使用。普通内容创作者请从 [Agent 用户手册](USER-GUIDE.zh-CN.md) 开始，不需要手动执行本手册中的命令。

以下内容从首次技术安装开始，供需要排查或扩展 Skill 的维护者按顺序执行。

维护者首次验证可完成“第 1 步到第 5 步”；建议先使用 `prompt-only`，它不会调用付费图片 API。

## 先记住三件事

1. `ip-pic` 只做 IP 文章配图和 IP 静态视频关键帧，不做封面、海报、知识卡片或发布平台。
2. 示例里的“学习向导阿拓”是公开原创教程角色。公开包只有文字 profile，不附带任何人物参考图；要固定你自己的 IP 外貌，必须登记你自有或已授权的参考图。
3. 单图重生和整批重建使用新的 `id` 与输出目录；只重做 two-step 文字层时使用新的 final 路径。`retry_failed` 会按合同更新原批次 manifest，但不会重编成功项。图片、后端回执和 QA 回执默认拒绝覆盖。

术语速查：

- brief：你填写的任务单。
- raw：还没加入最终文字的原始图片。
- final：允许进入人工验收的最终图片。
- manifest：程序生成的执行合同。
- handoff / request：交给图片后端的请求。
- receipt：后端或 QA 写回的证据文件。
- backend：真正生成图片的后端。
- finalize：确认真实图片文件存在并写回 receipt。

## 第 1 步：进入正确目录

找到包含 `SKILL.md`、`scripts`、`templates` 的完整 `ip-pic` 文件夹。在终端输入 `cd `，把该文件夹拖进终端窗口，再按回车。

然后执行：

```bash
pwd
test -f SKILL.md && test -f scripts/compile_ip_pic.py && echo "IP Pic 目录正确"
```

成功标志：最后一行显示 `IP Pic 目录正确`。

如果没有显示，说明你不在完整 Skill 根目录。不要只复制 `SKILL.md`。

## 第 2 步：创建独立 Python 环境

依次执行：

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

参数说明：

- `python3 -m venv .venv`：在当前目录创建隔离环境。
- `source .venv/bin/activate`：启用这个环境。
- `pip install -e .`：安装当前完整 Skill，修改代码后不必重复复制。

成功标志：

- Python 版本不低于 3.10。
- 命令行开头通常出现 `(.venv)`。
- 安装最后没有红色错误。

必须停止的情况：

- `python3 --version` 低于 3.10 或找不到命令；
- `python3 -m venv .venv` 返回非 0；
- 安装结束出现 `ERROR`。

先安装或切换到 Python 3.10+，再从本步骤重来。不要用管理员权限强行把依赖装进系统 Python。

如果 Skill 目录只读，请在可写工作目录创建虚拟环境，并用 Skill 的完整路径安装：

```bash
python3 -m venv ip-pic-venv
source ip-pic-venv/bin/activate
python3 -m pip install -e "/完整路径/ip-pic"
```

后续仍从完整 Skill 根目录运行脚本，但把 `--output-dir` 指向可写的绝对路径。

以后重新打开终端时，先进入 Skill 根目录，再执行：

```bash
source .venv/bin/activate
```

## 第 3 步：先做安装自检

执行：

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

参数说明：

- `-B`：不生成 `__pycache__`。
- `discover -s tests -v`：发现并详细运行 `tests` 中的全部测试。
- `verify_release.py`：检查模板数量、六风格、隐私、路径、凭证和发行 allowlist。

成功标志：

- 单元测试最后显示 `OK`。
- 发行检查显示通过，没有 `error`。

如果失败，先停止真实生图，把完整错误交给 Agent；不要修改原始候选来“绕过测试”。

## 第 4 步：完成第一次无付费编译

执行：

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/article-brief.json \
  --output-dir outputs/manual-direct-01 \
  --print-prompt
```

参数说明：

- `--brief`：输入任务 JSON。
- `--output-dir`：本次全新输出目录。
- `--print-prompt`：同时在终端显示最终 prompt，方便人工检查。

成功标志：终端出现下面四类路径，并显示 `mode: compile-only`：

- `image_brief.json`
- `ip-director-plan.json`
- `*.prompt.md`
- `run-manifest.json`

编译不会调用图片 API。查看最终合同：

```bash
python3 -m json.tool outputs/manual-direct-01/run-manifest.json
```

你应该看到：

- `delivery.mode` 为 `direct-integrated`。
- `size` 为示例模板的 `1536x864`。
- `render_handoff.schema_version` 为 `image-render-handoff/v1`。
- `expected_outputs` 给出应该写入的图片路径。

如果提示输出目录已经存在，不要删除旧结果。把 `manual-direct-01` 改成 `manual-direct-02`，同时把 brief 中的 `id` 改成新的任务 id。

## 第 5 步：先走 prompt-only

执行：

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --backend prompt-only \
  --request outputs/manual-direct-01/prompt-only.json
```

成功标志：

- 生成 `outputs/manual-direct-01/prompt-only.json`。
- 状态是 `prompt_ready`。
- `rendered` 是 `false`。

这一步只证明渲染交接正确，不代表已经生成图片，更不代表视觉通过。

## 第 6 步：选择真实渲染后端

四条路径的上游导演、模板、prompt 和 QA 完全相同。只选一条。

### A. Codex Image Tool

先准备请求：

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/manual-direct-01/codex-request.json
```

然后对宿主 Agent 说：

```text
请读取 outputs/manual-direct-01/codex-request.json，
不要改写 prompt、size 或参考图选择；
用 Codex Image Tool 生成图片并写到 expected_output，
完成后执行请求中的 finalize 流程。
```

宿主生成真实文件后，回填回执：

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/manual-direct-01/codex-request.json \
  --output outputs/manual-direct-01/image/ato-intelligence-value.png \
  --receipt-id your-host-run-id
```

`--output` 必须与 request 中的 `expected_output` 完全一致。文件不存在、是符号链接或路径不一致都会失败。

prepare 成功时 request 中应是 `status: awaiting_host`、`rendered: false`。finalize 成功后会生成 `codex-request.receipt.json`，其中必须是 `status: ok`、`rendered: true`，并含 `output_sha256`；然后进入第 11 步 QA。

### B. OpenAI Direct

只在你明确选择 BYOK 时使用。先把 key 放在安全 shell 或 secret manager，不要写入仓库：

```bash
python3 -m pip install -e '.[openai]'
export OPENAI_API_KEY='你的 OpenAI API Key'
python3 scripts/render_ip_pic.py openai-direct \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --request outputs/manual-direct-01/openai-request.json \
  --model gpt-image-2 \
  --quality high
```

OpenAI Direct 会按 handoff 自动选择端点：没有 `assets` 时调用 Images Generate；有 `assets` 时调用 Images Edit，并把所有已选择参考图作为输入。任一参考图路径缺失或文件不存在都会失败关闭，不能静默丢掉角色素材。

Images Edit 最多接收 16 张参考图；每张必须是小于 50MB 的 PNG、JPEG 或 WebP 普通文件，不能是符号链接。后端在付费调用前会再次校验路径、ownership、purpose、required、真实图片格式和文件大小。request 身份同时绑定 model、quality、operation 和每张输入图的 SHA-256；只有这些内容完全不变时，API 失败后才能用同一路径重试。修改 prompt、参考图、model 或 quality 时必须新建 request。已存在 receipt 时会在调用前停止。返回内容还必须是与 request 尺寸完全一致的 PNG，才能写图片和成功回执。

对本手册的 direct 示例，真实图片必须写到：

```text
outputs/manual-direct-01/image/ato-intelligence-value.png
```

成功时生成 `openai-request.receipt.json`，其中必须是 `status: ok`、`rendered: true`，`output_image` 必须等于上面的路径，并含 `output_sha256`；然后进入第 11 步 QA。

### C. 宿主已安装的 ai-router

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --backend host-ai-router \
  --request outputs/manual-direct-01/ai-router-request.json
```

然后把下面这段原样发给已经安装 ai-router 的宿主 Agent：

```text
请读取 outputs/manual-direct-01/ai-router-request.json。
调用你已经安装的 ai-router 图片生成工具；必须原样使用 request 中的
prompt、size、assets 和 expected_output，不要自行选择或删除参考图。
把图片写到 expected_output。成功后不要替我伪造回执，直接告诉我真实工具结果。
```

公开 Skill 不实现也不公开宿主 ai-router 的 provider、adapter、凭证、余额、重试或 fallback。宿主真实生成文件后，在 Skill 根目录执行：

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/manual-direct-01/ai-router-request.json \
  --output outputs/manual-direct-01/image/ato-intelligence-value.png \
  --receipt-id your-ai-router-run-id
```

prepare 成功时 request 中应是 `status: awaiting_host`、`rendered: false`。finalize 成功后生成 `outputs/manual-direct-01/ai-router-request.receipt.json`，其中必须是 `status: ok`、`rendered: true`，`output_image` 必须等于上面的路径，并含 `output_sha256`；然后进入第 11 步 QA。

### D. prompt-only

只导出 prompt 和交接请求，不生成图片。它适合免费自检或交给其他已授权宿主，不可当成真实 E2E。

## 第 7 步：理解两种文章文字模式

### direct-integrated：一次直出图文融合

示例 [examples/article-brief.json](../examples/article-brief.json) 使用此模式。

必须达到：

- 最终图有少量、短、可读的中文。
- 文字与人物、物件、动作共同表达一个判断。
- 主标题是较粗、端正的黑色中文展示字。
- 标题下只有一条不规则手绘强调线。
- 栏目名和补充判断使用两级说明蓝。

失败信号：纯插画、无画面文字、楷体、书法体、儿童体、细宋体、空心描边、乱码或文字墙。

重要限制：这是图像模型一次生成。`--font-path` 不能控制此模式的字形；要精确指定本机字体，请选择 `two-step-publish`。

### two-step-publish：先无字底图，再确定性加字

编译示例：

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/article-two-step-brief.json \
  --output-dir outputs/manual-two-step-01 \
  --print-prompt
```

确认 prompt 的图片规格是 `2048x2048`、`当前 raw 画布: 1:1`，明确要求“无字原始主视觉图片”，且不再出现“必须是 16:9 横版”。若仍出现冲突，停止真实生图并把 prompt 交给维护者。

下面给出 Codex Image Tool 的完整 two-step 路径；若改用 OpenAI Direct 或宿主 ai-router，只替换第 6 步所示的后端动作，不改变 manifest 和 raw 路径。

先 prepare：

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-two-step-01/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/manual-two-step-01/codex-request.json
```

把下面这段原样发给宿主 Agent：

```text
请读取 outputs/manual-two-step-01/codex-request.json，
不要改写 prompt、size 或参考图选择；
用 Codex Image Tool 生成无字 raw，并写到 expected_output。
```

真实 raw 必须写到：

```text
outputs/manual-two-step-01/image/ato-two-step-judgement.png
```

raw 存在后先回填后端回执：

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/manual-two-step-01/codex-request.json \
  --output outputs/manual-two-step-01/image/ato-two-step-judgement.png \
  --receipt-id your-two-step-host-run-id
```

确认 `codex-request.receipt.json` 是 `status: ok`、`rendered: true`，并含 `output_sha256`。然后在以下两种合成方式中只选一种。

方式一，不指定字体，使用原版默认的较粗中文展示字与手绘强调线：

```bash
python3 scripts/compose_publish_layout.py \
  --run-manifest outputs/manual-two-step-01/run-manifest.json
```

成功标志：

- 生成 `publish-layout.json`。
- 生成 `publish/final/ato-two-step-judgement.png`。
- 生成同名 `.layout-result.json`。
- raw 仍保留且未被覆盖。

默认 `editorial-ink-v2` 是原版较粗中文字重和墨线层级；`editorial-warm-v1` 是兼容暖纸层级。选择值写在 `selection_receipt.publish_extension_id`。

#### 使用你自己的字体

仅对 `two-step-publish` 使用。下面的命令始终写到独立的 `custom-font-01` 路径，因此无论你是否已经运行默认合成，都不会覆盖旧 final：

```bash
python3 scripts/compose_publish_layout.py \
  --run-manifest outputs/manual-two-step-01/run-manifest.json \
  --layout-manifest outputs/manual-two-step-01/publish-layout-custom-font-01.json \
  --output-image outputs/manual-two-step-01/publish/custom-font-01/ato-two-step-judgement.png \
  --font-path "/你的字体文件完整路径/YourChineseFont.ttf"
```

要求：

- 字体文件真实存在。
- 支持手册中要显示的中文。
- 你拥有相应使用权。
- 成功后检查 `outputs/manual-two-step-01/publish/custom-font-01/ato-two-step-judgement.png`，不要误看默认 final。

显式字体覆盖使用字体文件的第 0 个 face。更换字体后必须人工检查缺字、方框、行数、裁切和气质。

macOS 可直接使用原版默认字体层级。文章 two-step 在 Windows 或 Linux 上第一次合成就必须显式传 `--font-path`，即使系统里另装了中文字体也不要依赖自动发现；当前默认标题带引用的是 macOS 字体路径。不要等默认命令失败后再覆盖同一 final。

## 项目级定制运行时：让 Agent 保存角色、风格和导演预设

普通用户不执行这一节。Agent 或维护者使用下面的确定性入口，把私人配置写到用户写作项目的 `.ip-pic/`，而不是 Skill 安装目录。

三类资产分别是：

- `character`：角色 profile、权利依据、连续性锚点和项目内参考图；
- `style`：继承一个内置风格，只覆盖线条、材质、配色、形状和表面语气；
- `director`：动作、基础表情、个性化表情描述、强度、面部线索、视线、头部与身体姿态。

先把公开草稿复制到用户项目再修改。角色草稿中的参考图路径必须相对用户项目，真实存在且不是符号链接：

```bash
mkdir -p "/你的写作项目/customization-drafts"
cp examples/project-customization/character-draft.json "/你的写作项目/customization-drafts/"
cp examples/project-customization/style-draft.json "/你的写作项目/customization-drafts/"
cp examples/project-customization/director-draft.json "/你的写作项目/customization-drafts/"
```

先生成角色保存预览，不改变 registry 或活动角色：

```bash
python3 scripts/manage_ip_pic_project.py plan-create \
  --project-root "/你的写作项目" \
  --kind character \
  --draft "/你的写作项目/customization-drafts/character-draft.json" \
  --activate
```

命令输出 `status: preview`、目标 `version`、`content_hash` 和 `plan_path`。Agent 必须先把草稿内容和目标版本用自然语言展示给用户。用户没有明确确认时，不运行 apply。

确认后使用刚才返回的计划路径：

```bash
python3 scripts/manage_ip_pic_project.py apply \
  --project-root "/你的写作项目" \
  --plan "/你的写作项目/.ip-pic/plans/计划编号.json" \
  --confirm
```

`apply --confirm` 会创建不可变版本、更新活动指针并生成不含角色正文的回执。风格和导演使用同一流程，只把 `--kind` 分别改成 `style`、`director`，并传入对应草稿。

只读列出项目配置：

```bash
python3 scripts/manage_ip_pic_project.py list \
  --project-root "/你的写作项目"
```

查看一个具体版本：

```bash
python3 scripts/manage_ip_pic_project.py show \
  --project-root "/你的写作项目" \
  --kind character \
  --id ato-guide \
  --version v0001
```

修改角色、风格或导演时重新执行 `plan-create`，系统会分配下一个 `vNNNN`，绝不覆盖旧版。切回旧版也先生成预览：

```bash
python3 scripts/manage_ip_pic_project.py plan-activate \
  --project-root "/你的写作项目" \
  --kind character \
  --id ato-guide \
  --version v0001
```

用户确认后，再对返回的计划执行 `apply --confirm`。回退只改变活动指针，旧版和新版文件都保留。

使用项目配置编译时必须带 `--project-root`，brief 的 `project_customization` 点名角色、风格和导演 ID；也可以指定 `active`：

```bash
python3 scripts/compile_ip_pic.py \
  --brief "/你的写作项目/article-brief.json" \
  --project-root "/你的写作项目" \
  --output-dir "/你的写作项目/outputs/article-01" \
  --print-prompt
```

项目导演预设只填补本次任务没有明确写出的动作和人物表演；文章自己的显式要求优先。个人风格必须来自 `user-explicit` 的选择，不能冒充官方推荐。项目绝对路径不会进入 prompt；已授权参考图绝对路径只进入本地受控 handoff。

必须失败关闭的情况：

- 用户未确认就 apply；
- `.ip-pic`、计划或参考图是符号链接；
- 参考图位于项目外或不存在；
- 计划 hash 被修改，或生成计划后 registry revision 已改变；
- 版本目标已存在；
- 个人风格出现角色身份、参考图、场景、画幅、交付模式、模型、provider 或凭证字段。

## 第 8 步：使用自己的 IP 形象素材

公开示例默认只有阿拓文字 profile，不带人物图片。正式测试自己的 IP 时，请同时准备：

- 一份有权使用的角色说明。
- 1–5 张你自有或已授权的清晰参考图。
- 每张图的用途和权利来源。

复制示例为新文件，文件名不要与旧文件重复：

```bash
mkdir -p work
cp examples/article-brief.json work/my-character-article-01.json
```

用文本编辑器修改 `visual.ip_profile`。必须保留以下结构：

```json
{
  "schema_version": "ip-character-profile/v1",
  "id": "my-character-v1",
  "ownership": {
    "status": "user-owned",
    "basis": "由我原创并拥有使用权"
  },
  "identity": {
    "name": "角色公开名称",
    "description": "角色身份和内容职责"
  },
  "appearance": {
    "description": "只写公开、非敏感、确实需要保持的外观"
  },
  "personality": ["冷静", "好奇"],
  "continuity_anchors": [
    "锚点一",
    "锚点二",
    "锚点三"
  ],
  "references": [
    {
      "path": "/你有权使用的参考图完整路径/character-front.png",
      "purpose": "角色正面与配色一致性",
      "authorized": true
    }
  ]
}
```

保存后先验证 JSON。成功时会把格式化 JSON 打印到终端，不出现错误：

```bash
python3 -m json.tool work/my-character-article-01.json
```

`ownership.status` 只接受：

- `user-owned`
- `licensed`
- `project-original-tutorial`

再把真实素材登记到 `visual.authorized_assets`：

```json
[
  {
    "id": "character-main",
    "path": "/你有权使用的参考图完整路径/character-front.png",
    "purpose": "主角色身份与配色",
    "ownership": "user-owned",
    "required": true
  }
]
```

同时修改任务 `id`、标题和内容，然后编译到新目录：

```bash
python3 scripts/compile_ip_pic.py \
  --brief work/my-character-article-01.json \
  --output-dir outputs/my-character-article-01 \
  --print-prompt
```

编译器会校验 profile 的权利状态、依据、身份、外观、性格、至少三个连续性锚点，以及 profile 内参考图的 `authorized: true`。每个 `authorized_assets` 项也必须使用真实存在的绝对路径，并明确填写允许的 ownership 和 purpose；缺字段或文件不存在会在生成 handoff 前停止。素材文件不会被打包进公开 Skill，也不会写入 prompt 正文；它只进入受控 render handoff。

### prepared reference 到底是什么，如何确认后端真的用了

prepared reference 就是你在本步骤事先挑好、裁好、确认有权使用，并登记进 brief 的本地人物参考图。`ip-pic` 不替你偷偷下载、猜测或生成角色素材。

一张图可以同时出现在：

- `visual.ip_profile.references`：说明它用于哪项角色连续性；
- `visual.authorized_assets`：把它作为已授权渲染素材交给后端。

编译后检查真实交接，不要只看 prompt：

```bash
python3 -m json.tool outputs/my-character-article-01/run-manifest.json
```

在 `render_handoff.assets` 中应看到你登记的素材路径、用途、权利状态和是否必需。绝对路径只存在于受控 handoff，不会进入公开 prompt。多张图时，每张图使用不同的 `id` 和清楚的 `purpose`，例如“正面五官”“侧面轮廓”“服装配色”；编译前的 reference selection 已决定进入这份 handoff 的集合，宿主不能随意换图。

先 prepare：

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/my-character-article-01/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/my-character-article-01/codex-request.json
```

再检查 request：

```bash
python3 -m json.tool outputs/my-character-article-01/codex-request.json
```

确认 request 顶层的 `assets` 与 manifest 的 `render_handoff.assets` 一致，再让宿主生成。宿主 Agent 的指令必须包含：

```text
必须读取并附加 request.assets 中所有 required=true 的参考图；
不得只复制文字 prompt 后丢掉参考图；不得用失败输出反向充当参考图。
```

最后只能通过真实看图核对角色脸型、发型、配色和连续性锚点。receipt 的哈希只能证明生成了哪一个文件，不能自动证明人物长得正确。

不要使用未获授权的第三方角色、名人照片或来源不明的图片。

## 第 9 步：选择六种文章风格

修改 brief 的：

```text
selection_receipt.style_variant_id
```

可选值：

| 用户名称 | 值 |
|---|---|
| 简约线稿 | `minimal-lineart` |
| 毛毡手作 | `playful-craft` |
| 贴画拼贴 | `sticker-collage` |
| 松弛手绘 | `expressive-handdrawn` |
| 高冲击 | `pop-impact` |
| 艺术版画 | `art-print` |

六风格只改变材质、线条、色彩、形状和表面语气，不改变角色身份、业务场景、画布、交付模式或构图导演。

## 第 10 步：编译静态视频关键帧

先运行 1:1 示例：

```bash
python3 scripts/compile_ip_pic.py \
  --brief examples/video-square-brief.json \
  --template ip-editorial-video-square-v1 \
  --output-dir outputs/manual-video-square-01 \
  --print-prompt
```

成功时会多出：

```text
outputs/manual-video-square-01/video-text-overlay.json
```

先检查 prompt：开头必须写“无字原始视觉素材”，结尾必须写“无字视频关键帧 raw”，不能再出现“直接生成成品图片”。

用 Codex Image Tool 的完整路径如下：

```bash
python3 scripts/render_ip_pic.py prepare \
  --manifest outputs/manual-video-square-01/run-manifest.json \
  --backend codex-image-tool \
  --request outputs/manual-video-square-01/codex-request.json
```

让宿主把无字 raw 写到：

```text
outputs/manual-video-square-01/image/ato-video-square-01.png
```

然后回填：

```bash
python3 scripts/render_ip_pic.py finalize \
  --request outputs/manual-video-square-01/codex-request.json \
  --output outputs/manual-video-square-01/image/ato-video-square-01.png \
  --receipt-id your-video-host-run-id
```

receipt 必须是 `status: ok`、`rendered: true`。再执行确定性文字层：

```bash
python3 scripts/compose_video_keyframe_text.py \
  --manifest outputs/manual-video-square-01/video-text-overlay.json
```

成功标志：

- 生成 `outputs/manual-video-square-01/final/ato-video-square-01.png`，尺寸为 2048x2048。
- 生成 `outputs/manual-video-square-01/final/video-text-overlay-result.json`。
- 标题、蓝色栏目名、单条强调线和补充说明可见。
- 底部字幕安全区保持干净。

文章与视频的风格入口不同：

- 文章使用 `selection_receipt.style_variant_id`。
- 视频使用 `--template` 选择既有视频结构/风格模板。
- 当前视频编译器不会读取文章 selection receipt 来切换风格。

常用方屏模板：

| 风格 | 视频模板 |
|---|---|
| 编辑默认 | `ip-editorial-video-square-v1` |
| 简约线稿 | `ip-minimal-lineart-video-square-v1` |
| 毛毡手作 | `ip-playful-craft-video-square-v1` |
| 贴画拼贴 | `ip-sticker-collage-video-square-v1` |
| 松弛手绘 | `ip-expressive-handdrawn-video-square-v1` |
| 高冲击 | `ip-pop-impact-video-square-v1` |
| 艺术版画 | `ip-art-print-video-square-v1` |

竖屏可使用 `custom-ip-handdrawn-video-portrait-v1`、`ip-editorial-video-v3` 或 `ip-editorial-video-subtitle-safe-v4`。必须相应修改 brief 的 `composition.size` 和构图字段，不要把方屏机械裁成竖屏。

视频自定义字体写在 `video-text-overlay.json` 顶层：

```json
{
  "font_path": "/你的中文字体完整路径/YourChineseFont.ttc",
  "headline_font_path": "/你的标题字体完整路径/YourHeadlineFont.ttc"
}
```

保存后立即验证 JSON：

```bash
python3 -m json.tool outputs/manual-video-square-01/video-text-overlay.json
```

注意：

- 9:16 标题使用 `font_path`。
- 1:1 方屏标题可使用 `headline_font_path`。
- Windows 必须显式配置中文 `font_path`；1:1 如需不同标题字体，再配 `headline_font_path`。
- Linux 只有系统存在脚本列出的 Noto CJK 字体路径时才可自动回退；为了可复现，正式交付仍建议显式配置。
- 不同系统的字体 fallback 可能不同，必须在目标系统人工看图。

如果已经生成默认视频 final，修改字体后不要覆盖它。复制 overlay 为新文件，并把顶层 `output_dir` 改到新目录：

```bash
cp outputs/manual-video-square-01/video-text-overlay.json \
  outputs/manual-video-square-01/video-text-overlay-font-retry-01.json
```

把新 JSON 顶层的 `output_dir` 改成：

```text
outputs/manual-video-square-01/final/font-retry-01
```

保留 `items[0].output_file`：

```text
ato-video-square-01.png
```

不要添加 `output` 或 `result_receipt`；合成器会在新 `output_dir` 自动生成新图片和 `video-text-overlay-result.json`。

再次验证并执行：

```bash
python3 -m json.tool outputs/manual-video-square-01/video-text-overlay-font-retry-01.json
python3 scripts/compose_video_keyframe_text.py \
  --manifest outputs/manual-video-square-01/video-text-overlay-font-retry-01.json
```

对新 final 重新做第 11 步人工看图和 QA，旧 final 与旧 receipt 保留作审计。

## 第 11 步：逐图 QA

先打开 `run-manifest.json`，查看：

```text
visual_qa.required_checks
```

逐项真实看图。只有你实际看见通过的项目才传 `--pass-check`。

direct-integrated 示例：

```bash
python3 scripts/qa_ip_pic.py \
  --manifest outputs/manual-direct-01/run-manifest.json \
  --image outputs/manual-direct-01/image/ato-intelligence-value.png \
  --pass-check ip_identity \
  --pass-check semantic_action \
  --pass-check integrated_text_present \
  --pass-check integrated_text_legible \
  --pass-check text_does_not_overlap_subject
```

成功标志：

- 生成同名 `.qa.json`。
- `status` 是 `checks_passed`。
- `visual_acceptance` 仍是 `pending_human`。
- `approved_for_release` 仍是 `false`。

这表示机器合同检查完成，不代表用户已经批准视觉发布。人工最终验收见 [references/qa-checklist.md](../references/qa-checklist.md)。

two-step 必须检查 final，不是 raw：

```bash
python3 scripts/qa_ip_pic.py \
  --manifest outputs/manual-two-step-01/run-manifest.json \
  --image outputs/manual-two-step-01/publish/final/ato-two-step-judgement.png \
  --pass-check raw_has_no_text \
  --pass-check final_title_band_present \
  --pass-check final_title_legible \
  --pass-check final_text_does_not_overlap_visual \
  --pass-check raw_not_published_as_final
```

视频也检查 final：

```bash
python3 scripts/qa_ip_pic.py \
  --manifest outputs/manual-video-square-01/run-manifest.json \
  --image outputs/manual-video-square-01/final/ato-video-square-01.png \
  --pass-check ip_identity \
  --pass-check semantic_action \
  --pass-check raw_has_no_text \
  --pass-check final_title_present \
  --pass-check final_title_legible \
  --pass-check final_text_does_not_overlap_visual \
  --pass-check subtitle_safe_zone_clear \
  --pass-check raw_not_published_as_final
```

如果某项失败，用 `--fail-check 检查名` 记录。回执会告诉你：

- `retry_scope: render`：重新生图。
- `retry_scope: publish-layout`：two-step 的底图可保留，只重做确定性文字层。

## 第 12 步：失败重做与整批重建

### 单图只重做渲染

如果编译结果正确、图片生成失败，而且预期图片路径还不存在：

1. 保留原 `run-manifest.json`。
2. 创建新的 request 文件名，例如 `codex-request-retry-01.json`。
3. 再调用同一个后端。
4. 不把失败图加入参考图。

### QA 否决且旧图已经存在

不要覆盖旧图：

1. 复制原 brief 为 `work/<原名>-retry-01.json`。
2. 把 brief 内 `id` 改成 `<原 id>-retry-01`。
3. 验证 JSON：`python3 -m json.tool work/<原名>-retry-01.json`。
4. 编译到全新 `outputs/<原 id>-retry-01`。
5. 重新 prepare、真实生图、finalize 和 QA。
6. 保留旧失败图作为审计，但不得把它登记为下一轮参考图。

### 只重做 two-step 文字层

raw 合格、只有字体或排版不合格时，不重生人物。指定全新的 layout manifest 和 final：

```bash
python3 scripts/compose_publish_layout.py \
  --run-manifest outputs/manual-two-step-01/run-manifest.json \
  --layout-manifest outputs/manual-two-step-01/publish-layout-retry-01.json \
  --output-image outputs/manual-two-step-01/publish/retry-01/ato-two-step-judgement.png \
  --font-path "/你的中文字体完整路径/YourChineseFont.ttf"
```

对新的 final 重新真实看图。QA receipt 也使用新的图片路径，因此不会覆盖旧回执。

### 内容、导演或选择错误

修改 brief 的 `id`，并使用新输出目录重新编译。不要覆盖旧目录。

### 批量

Agent 编排入口使用 `ip_pic.batch`：

- `build_shot_plan`：先生成构图轮换计划。
- `run_batch`：逐项编译并保留部分失败。
- `retry_failed`：只重试失败项，不重编成功项。
- `rebuild_batch`：使用全新目录整批重建，并排除旧输出树中的图片。

对 Agent 说：

```text
请按 ip-pic 的 docs/USER-GUIDE.zh-CN.md 和 references/full-rebuild-playbook.md
处理这组 IP 配图。先展示 shot plan；使用全新输出目录；
保留成功项，只重试失败项；任何被否决图片不得进入下一轮参考图；
结构测试不能代替我的逐图视觉验收。
```

批量完整合同见 [references/full-rebuild-playbook.md](../references/full-rebuild-playbook.md)。

## 第 13 步：用户能否修改样式或新增风格

可以，但要先区分两种情况：

### 不修改 Skill 本体

你可以安全地：

- 在六种内置文章风格中切换。
- 更换自己有权使用的角色 profile 和参考图。
- 调整文章内容、画布、构图与交付模式。
- 为 two-step 输出指定本机字体。

这些仍属于官方等价能力。

### 修改 Skill 本体

你也可以复制成个人 fork 后：

- 修改已有风格 profile。
- 新增第七种风格。
- 新增标题带。
- 修改视频文字样式。

修改后的 fork 不再是官方固定六风格的原版等价发行物。必须保留许可证、备份、运行测试并自行承担视觉回归。完整步骤见 [references/customization.md](../references/customization.md)。

新增第七种文章风格的最小步骤：

1. 复制 `profiles/render-styles/minimal-lineart-v1.json` 为一个新文件。
2. 把新 profile 的 `id` 改为唯一值；保留 `schema_version: render-style-profile/v1` 和 `scope: render-style-only`。
3. 在 `profiles/render-styles.json` 的 `styles` 数组登记同一个 id 和准确文件名。
4. 不得加入角色身份、参考图、scene、canvas、delivery mode、provider、model 或 key。
5. 运行：

```bash
python3 -c "from pathlib import Path; from ip_pic.styles import list_styles; print([item['id'] for item in list_styles(Path.cwd())])"
python3 -B -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

运行时 loader 应能列出新 id；但官方“恰好六风格”测试和 `verify_release.py` 应按设计失败。这正是个人 fork 边界，不要删除门禁或宣称官方等价。视频风格不是在文章 registry 加一行；视频仍需独立模板开发与真实安全区回归。

## 常见错误速查

| 错误或现象 | 原因 | 处理 |
|---|---|---|
| `output directory already exists` | 输出目录已存在 | 换新的任务 id 和目录 |
| `selection_receipt` / 选择确认错误 | 文章没有确认业务、文字、画布或风格 | 对照示例补齐 receipt |
| `publish_extension_id` 错误 | two-step 未选标题带 | 使用 `editorial-ink-v2` 或 `editorial-warm-v1` |
| `profile ownership` 错误 | 角色权利状态或依据不完整 | 使用允许的 status，并写清 basis |
| `字体不存在` | 字体路径错误 | 使用字体文件的完整路径 |
| 标题是方框或缺字 | 字体不支持中文 | 换有中文字符集的合法字体 |
| direct-integrated 没文字 | 模型未遵守融合文字合同 | 只重做渲染；不要用结构测试冒充通过 |
| two-step raw 有文字 | raw 生图失败 | 重做 raw，不能直接发布 |
| 视频底部被遮挡 | raw 没留安全区或文字布局不合格 | 重做对应阶段 |
| `prompt_ready` | 只是 prompt-only | 选择真实后端才会生成图片 |
| QA 显示 `pending_human` | 自动检查完成但未人工批准 | 打开最终图逐项验收 |

## 发布前最后检查

- 角色素材全部有权使用。
- 没有个人敏感信息、凭证、私有路径或私有业务资料进入 Skill。
- direct-integrated 真实包含融合中文和单条手绘强调线。
- two-step 的 raw 与 final 分离，final 字体可读。
- 视频关键帧安全区无人物、物件或文字冲突。
- 每张图都有独立 QA 回执。
- 自动测试通过。
- 用户本人已真实看图并明确接受。

更多原理与合同从 [references/README.md](../references/README.md) 进入。
