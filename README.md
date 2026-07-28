# IP 配图 Skill

[简体中文](README.md) | [English](README.en.md)

这是 IP 配图 Skill 的安装与使用指南。照着下面的顺序安装、配好一种出图方式，再用教程角色完成两次测试。跑通以后，再换成你自己的角色。

正常使用很简单：你只需要说“给这段文字配图”或“给这篇文章配图”。文章分析、配图点选择、图片数量建议、brief、prompt、出图和检查都由 Agent 自动完成。

## 1. 安装 Skill

在你准备写文章的项目目录运行：

```bash
npx skills add wukongai/ip-pic-skill
```

安装器会询问目标 Agent 和安装范围。安装完成后，重新打开任务并说：

```text
使用 ip-pic，检查安装并带我完成第一次使用。
```

Agent 会自行定位 Skill 和脚本。正常使用不需要你研究 JSON、脚本路径或安装依赖。

## 2. 配好一种出图方式

IP 配图有三种真实出图方式，首次配置一次，之后直接说“配图”即可。

1. **Codex Image Tool / 内置 `imagegen`（推荐）**：使用 GPT Image 2；由 Codex 提供，不需要你配置 API Key。
2. **直接 OpenAI API**：使用 Skill 自带的 GPT Image 2 renderer；需要你自己的 `OPENAI_API_KEY`，费用进入你的 OpenAI API 账户。
3. **已有 `ai-router`**：适合已经安装并注册 `ai_router.generate_image` 的用户；Key、provider、model、重试和 fallback 都留在 Router 内。

首次选择后，可以让 Agent 设为当前项目默认。以后它会复用这个方式；只有后端失效或你要求更换时才重新选择。

`prompt-only` 是非出图兜底，不是独立的真实出图方式。它只生成 prompt、`render-request.json` 和 manifest，不会生成图片，结果为 `compile_only`。

### 直接 OpenAI API 的安全配置

如果选择直接 OpenAI API，让 Agent 依次运行：

```bash
python3 <skill-root>/scripts/openai_backend.py doctor
python3 <skill-root>/scripts/openai_backend.py configure
```

只有 `doctor` 返回 `missing_credentials` 时才需要 `configure`。它使用隐藏输入，把 Key 写入用户级 `~/.ip-pic/.env`；也可以在当前进程提供 `OPENAI_API_KEY`。

不要把 Key 粘贴到聊天、文章、仓库、角色资料或 `EXTEND.md`。可以从 [OpenAI API Keys](https://platform.openai.com/api-keys) 创建 Key；API 使用可能需要账户额度或组织验证。若返回 `unsupported_platform`，改选 Codex Image Tool 或已有 `ai-router`。

直接 renderer 使用精确尺寸：`16:9 = 1536x864`、`1:1 = 1024x1024`、`9:16 = 1152x2048`。宽高必须是 16 的倍数。若输出文件已存在，调用会在付费请求前停止；请使用新的输出文件名，不会覆盖原文件。

### 已有 ai-router

AI Router 是宿主中已经安装并通过 MCP 暴露图片能力的统一入口。`ip-pic` 只调用现成的 `ai_router.generate_image`，不读取 Router 的 `.env`，也不接管它的凭证、模型和容错配置。本项目不引导下载任何私有 Router 仓库。

## 3. 先用教程角色跑通

第一次不要急着建立自己的角色。先从三个原创教程角色中选一个：

| 悟空知识工匠 | 月兔地图师 | 学习向导阿拓 |
|---|---|---|
| ![悟空知识工匠](examples/characters/wukong/preview.png) | ![月兔地图师](examples/characters/moon-rabbit/preview.png) | ![学习向导阿拓](examples/characters/ato/preview.png) |
| [角色资料](examples/characters/wukong/profile.json) | [角色资料](examples/characters/moon-rabbit/profile.json) | [角色资料](examples/characters/ato/profile.json) |

阿拓还提供一张 [合成源照片](examples/characters/ato/source-synthetic-photo.png)，用于演示“真人风格照片 → 原创卡通母版”。它是项目生成的教程素材，不是真人照片。

例如：

```text
这次教程使用学习向导阿拓。
```

三个角色都不会自动保存成你的 `.ip-pic/ip-profile.json`。

## 4. 用一段短文字测试

先复制下面这段文字：

> 很多人以为效率来自把计划写得更细，但真正让项目变快的是缩短反馈周期。先交付一个可以检查的小结果，再根据反馈继续调整，比长时间闭门完成一个大版本更可靠。

然后只说：

```text
用学习向导阿拓给下面这段文字配 1 张图：
<粘贴上面的文字>
```

Agent 会自动提炼核心判断、选择画面、生成图片并检查角色一致性。成功标准是：真正得到图片，角色没有明显漂移，画面能表达文字含义，并且没有乱码、水印或无意义文字。

## 5. 给一篇长文自动配图

短文字成功以后，把完整文章交给 Agent：

```text
用学习向导阿拓给下面这篇文章配图：
<粘贴文章>
```

就这一句。Agent 会自动分析标题、章节和语义转折，选择值得视觉化的内容，决定合理数量，再完成编译、出图和逐张检查。它不会机械地每段配一张，也不会要求你先写配图点或 prompt。

如果你想覆盖默认值，可以额外指定，例如“做 3 张 16:9 配图”。不指定时，让 Skill 自己判断。

真实后端成功时，结果包括图片、prompt、`render-request.json` 和运行清单。选择 `prompt-only` 时只有编译产物，必须明确显示 `compile_only`，不能声称已经出图。

## 6. 换成你自己的角色

前两次测试跑通后，再准备一张本人或已获授权的真人照片。建议单人、清晰、光线均匀，发型、脸型、眼镜和服装锚点清楚可见。

使用 Codex Image Tool 或已有 `ai-router` 时，附加真人照片，并使用这段母版提示词：

```text
把这张本人或已获授权的真人照片转成原创卡通 IP 角色母版。保留可识别的发型、脸型、眼镜等非敏感外观锚点，但不要推断敏感属性；设计为全身角色，使用干净中性背景，同时展示正面、侧面、背面等多视角和 4 个常用表情。造型简洁，适合文章系列配图并能跨图保持一致。无文字、水印或 logo，不模仿任何第三方角色特征。
```

如果使用直接 OpenAI API，让 Agent 保持在你的用户项目目录运行：

```bash
python3 <skill-root>/scripts/openai_backend.py master --reference <project-photo-path> --output <project-character-master.png>
```

输入和输出都应位于你的项目，不能写入 Skill 安装目录。如果输出文件已存在，请换一个新的输出文件名；调用不会覆盖已有母版。

如果使用 `prompt-only`，Skill 只能提供母版提示词。你需要把照片和 prompt 交给外部图片工具，生成后再把母版上传给 Agent；也可以继续使用教程角色。

母版满意后说：

```text
用这张卡通母版建立我的 ip-profile；一次只问一个问题，保存前先让我确认。
```

Agent 会确认权利来源，整理名称、身份、外观、性格和连续性锚点，再保存到 `.ip-pic/ip-profile.json`。你不需要手写 JSON。

之后正常配图只要说：

```text
用我的角色给这篇文章配图：
<粘贴文章>
```

### 增加动作和表情

需要更稳定的动作或表情时，把新参考图分别放进：

```text
.ip-pic/assets/poses/
.ip-pic/assets/expressions/
```

不要覆盖角色母版。让 Agent 把每张参考图的用途和授权状态写入 profile；每次出图只选择当前画面需要的少量参考图。

`.ip-pic/ip-profile.json` 可能包含本地路径。若不希望被 Git 或云盘同步，把 `.ip-pic/` 加入项目 `.gitignore`。

## 安装或首次运行失败时

- 安装命令失败：检查 Node.js 和 `npx`，确认安装范围。
- 安装完成但编译器启动失败：再检查 Python 3.10+ 和实际可执行文件。
- 只有 prompt、没有图片：确认是否选择了 `prompt-only`，或真实后端尚未配置成功。
- 直接 OpenAI API 返回 `unsupported_platform`：改选其他真实出图方式。Windows 仍可安装 Skill 并使用其他方式。

Windows PowerShell 使用同一条单行命令：

```powershell
npx skills add wukongai/ip-pic-skill
```

## 可选偏好

需要长期保存画幅、风格或后端时，把 `EXTEND.example.md` 复制为项目 `.ip-pic/EXTEND.md`。偏好文件不能保存 Key、token、cookie、服务地址或模型路由。

## 从旧名称迁移

如果安装过旧版 `custom-ip-illustration`：

1. 用 Skill 管理器移除旧 Skill；
2. 重新运行 `npx skills add wukongai/ip-pic-skill`；
3. 如需保留角色与偏好，把项目 `.custom-ip-illustration/` 中的文件移动到 `.ip-pic/`。

## 开发者验证

```bash
git clone https://github.com/wukongai/ip-pic-skill.git
cd ip-pic-skill
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_release.py --root . --manifest public-release-manifest.json
```

安全问题见 [SECURITY.md](SECURITY.md)，贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。
