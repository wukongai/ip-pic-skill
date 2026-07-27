# Backend Selection

首次运行必须让用户选择；“宿主有工具”不等于用户已经同意使用。编译器始终保持 provider-neutral，图片调用由选定 renderer 或宿主工具执行。

## 固定的四种选择

| id | 用户看到的名称 | 配置与结果 |
|---|---|---|
| `codex-image-tool` | Codex Image Tool / 内置 imagegen | GPT Image 2；宿主提供，不需要用户 Key |
| `openai-direct` | 直接 OpenAI API | 本 Skill 自带 GPT Image 2 renderer；需要用户自己的安全配置，可能收费；平台检查失败时不可用 |
| `ai-router` | 已有 ai-router | 仅限已经安装并注册 `ai_router.generate_image` 的宿主；凭证和路由留在 Router |
| `prompt-only` | 只生成 Prompt | 不生成图片，返回 `compile_only` |

若 `requested: auto` 且没有可用的已保存偏好，`scripts/resolve_backend.py` 必须返回 `needs_user_choice / first_run_choice`，并按表中顺序给出四项及当前可用状态。不可静默选择原生工具、唯一第三方工具或付费方式。

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

`kind` 只允许 `native` 或 `third_party`。`prompt-only` 无需写入 inventory，解析器始终把它作为可选的非生图路径。

## 解析规则

1. 用户本次明确选择 `prompt-only`：立即返回 `compile_only`。
2. 用户本次明确选择其他后端：已就绪则 `selected`，未就绪则 `needs_setup`，不可 fallback。
3. 用户明确保存的偏好已就绪：使用该偏好。
4. 保存偏好失效：重新返回四项选择，不可 fallback。
5. 没有本次选择或保存偏好：返回 `first_run_choice`。

只有用户明确要求“以后默认用这个”时才写入 `EXTEND.md`。本次选择默认只作用于本次任务。

## 各后端边界

### Codex Image Tool

调用宿主提供的 Image Tool / `imagegen`。用户不配置 Key；Agent 不询问 provider 或底层模型参数。只有工具当前真实可用时才显示为可用。

### 直接 OpenAI API

这是与编译器分离的 renderer，不改变 render request：

1. Agent 运行 `python3 <skill-root>/scripts/openai_backend.py doctor`。
2. `unsupported_platform` 时说明这一后端当前不可用，让用户重新选择；Windows 仍可安装 Skill 并使用其他后端。
3. `missing_credentials` 时，说明费用和凭证位置；用户确认后运行 `configure`。
4. `configure` 使用隐藏输入，只写用户级 `~/.custom-ip-illustration/.env`，权限为当前用户可读；也可读取进程 `OPENAI_API_KEY`。
5. Agent 不在聊天、命令参数、日志、profile 或 `EXTEND.md` 中接收或回显 Key。
6. 建立真人卡通母版时，保持用户项目为工作目录，运行 `python3 <skill-root>/scripts/openai_backend.py master --reference <project-photo-path> --output <project-character-master.png>`；输入和输出不得位于 Skill 安装目录。
   输出必须使用 `.png` 后缀。如果输出文件已存在，命令会在付费请求前停止；让用户改用新的输出文件名，不会覆盖已有母版。
7. 已有合法 profile 且编译完成后才运行 `render`。直接 renderer 只接受编译器的三组精确尺寸：`16:9 = 1536x864`、`1:1 = 1024x1024`、`9:16 = 1152x2048`；宽高必须是 16 的倍数，并满足 GPT Image 2 的边长、宽高比与总像素限制。每次使用全新的输出文件名；任一目标已存在时在 API 调用前停止并保留原文件。每张远端失败单独报告。

`doctor` 返回 `unsupported_platform` 时停止该路径，不运行 `configure`、`master` 或 `render`，不发送付费请求，也不静默 fallback。

### 已有 ai-router

只在宿主已经安装并注册 `ai_router.generate_image` 时可选。本 Skill 不引导下载任何私有 Router，不读取 Router 的 `.env`，也不接收 provider、model、base URL、重试或 fallback。上述能力和凭证都由 Router 自己管理。

### prompt-only

只保存 prompt、`render-request.json` 和 manifest，不生成图片。最终回复必须明确这是 `compile_only`，不能使用“已生成图片”“出图完成”等说法。
