# IP 配图 Preferences

```yaml
preferred_image_backend: auto
default_output_dir: imgs
default_style: editorial-handdrawn
default_canvas: 16:9
generation_batch_size: 4
language: zh
```

`preferred_image_backend` 可选值：

- `auto`：首次运行仍展示四项，让用户选择；
- `codex-image-tool`；
- `openai-direct`；
- `ai-router`；
- `prompt-only`。

只有用户明确要求“以后默认用这个”时才修改。只保存偏好，不要在此文件写入 API key、token、cookie、secret、服务地址或模型路由。直接 OpenAI API 的 Key 只允许位于进程环境或用户级 `~/.ip-pic/.env`。
