# Backend Selection

Skill 不探测凭证，不配置服务，也不决定模型。宿主只需提供当前可调用图片工具的结构化 inventory。

## Inventory

```json
{
  "backends": [
    {
      "id": "host-image-tool",
      "kind": "native",
      "available": true,
      "default": true
    }
  ]
}
```

`kind` 只允许 `native` 或 `third_party`。Inventory 不得包含 API key、服务地址、模型、余额、重试或 fallback。

## 解析顺序

1. 本次请求明确指定且可用。
2. 保存偏好且可用。
3. 宿主原生工具。
4. 唯一第三方工具。
5. 多个第三方工具时返回 `needs_user_choice`。
6. 没有工具时返回 `compile_only`。

可用 `scripts/resolve_backend.py` 对 inventory 做确定性验证。用户的自然语言请求仍由宿主 Agent 转换为 inventory。

## 保存偏好

只有用户明确要求“以后默认用这个”时才写入 `EXTEND.md`。本次选择默认只作用于本次任务。
