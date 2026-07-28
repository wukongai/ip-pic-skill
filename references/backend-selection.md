# Backend Selection

出图方式在首次使用时配置一次，之后普通“配图”请求复用当前项目的已保存选择。编译器始终 provider-neutral；图片调用由选定 renderer 或宿主工具执行。

## 三种真实出图方式

| id | 用户看到的名称 | 配置与结果 |
|---|---|---|
| `codex-image-tool` | Codex Image Tool / 内置 imagegen | GPT Image 2；宿主提供，不需要用户 Key |
| `openai-direct` | 直接 OpenAI API | 本 Skill 自带 GPT Image 2 renderer；需要用户自己的安全配置，可能收费；平台检查失败时不可用 |
| `ai-router` | 已有 ai-router | 仅限已经安装并注册 `ai_router.generate_image` 的宿主；凭证和路由留在 Router |

`prompt-only` 是 compile-only fallback / 非出图兜底，不是独立的真实出图方式。它只生成 prompt、`render-request.json` 和 manifest，不生成图片，状态为 `compile_only`。

## 首次配置与复用

1. 若已有就绪的项目偏好，普通配图直接复用，不再询问。
2. 若用户本次明确指定后端，检查其可用状态；已就绪则使用，未就绪则进入配置，绝不 fallback。
3. 若没有偏好也没有本次选择，`scripts/resolve_backend.py` 返回 `needs_user_choice / first_run_choice`。Agent 展示三种真实出图方式的可用状态，并把 `prompt-only` 单独列为不出图兜底。
4. 首次选择后询问是否保存为当前项目默认。只有用户明确要求“以后默认用这个”时，才写入 `.ip-pic/EXTEND.md`。
5. 保存偏好失效时重新选择；不得静默改用宿主原生工具、唯一第三方工具或可能收费的 API。
6. 用户明确选择 `prompt-only` 时立即返回 `compile_only`。

底层解析器仍会把 `prompt-only` 放入可选结果列表，以保持确定性的 `first_run_choice` 合同；用户文档必须把它与三种真实出图方式分开解释。

## Inventory

宿主传入结构化 inventory，不得包含 API key、服务地址、模型、余额、重试或 fallback：

```json
{
  "backends": [
    {
      "id": "codex-image-tool",
      "kind": "native",
      "available": true,
      "configured": true
    },
    {
      "id": "openai-direct",
      "kind": "third_party",
      "available": true,
      "configured": false,
      "requires_setup": true
    }
  ]
}
```

`kind` 只允许 `native` 或 `third_party`。`prompt-only` 无需写入 inventory。

## 各后端边界

### Codex Image Tool

调用宿主提供的 Image Tool / `imagegen`。用户不配置 Key；Agent 不询问 provider 或底层模型参数。只有工具当前真实可用时才显示为可用。

### 直接 OpenAI API

这是与编译器分离的 renderer，不改变 render request：

1. Agent 运行 `python3 <skill-root>/scripts/openai_backend.py doctor`。
2. `unsupported_platform` 时说明当前不可用，让用户重新选择；Windows 仍可安装 Skill 并使用其他后端。
3. `missing_credentials` 时说明费用和凭证位置；用户确认后运行 `configure`。
4. `configure` 使用隐藏输入，只写用户级 `~/.ip-pic/.env`，权限为当前用户可读；也可读取进程 `OPENAI_API_KEY`。
5. Agent 不在聊天、命令参数、日志、profile 或 `EXTEND.md` 中接收或回显 Key。
6. 建立真人卡通母版时，保持用户项目为工作目录：

```bash
python3 <skill-root>/scripts/openai_backend.py master --reference <project-photo-path> --output <project-character-master.png>
```

输入和输出不得位于 Skill 安装目录。输出必须使用 `.png`。如果输出文件已存在，命令在付费请求前停止；让用户改用新的输出文件名，不会覆盖已有母版。

7. 已有合法 profile 且编译完成后才运行 `render`。只接受三组精确尺寸：`16:9 = 1536x864`、`1:1 = 1024x1024`、`9:16 = 1152x2048`；宽高必须是 16 的倍数，并满足 GPT Image 2 的边长、宽高比与总像素限制。
8. 每次使用全新的输出文件名；任一目标已存在时在 API 调用前停止并保留原文件。每张远端失败单独报告。

`doctor` 返回 `unsupported_platform` 时停止该路径，不运行 `configure`、`master` 或 `render`，不发送付费请求，也不静默 fallback。

### 已有 ai-router

只在宿主已经安装并注册 `ai_router.generate_image` 时可选。本 Skill 不引导下载任何私有 Router，不读取 Router 的 `.env`，也不接收 provider、model、base URL、重试或 fallback。凭证、模型选择和容错都由 Router 自己管理。

### prompt-only

只保存 prompt、`render-request.json` 和 manifest，不生成图片。最终回复必须明确这是 `compile_only`，不能使用“已生成图片”“出图完成”等说法。
