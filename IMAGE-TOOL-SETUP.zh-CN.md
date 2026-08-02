# IP Pic 图片工具接入说明

这份说明只在 Agent 明确告诉你“当前没有可用图片工具”时使用。普通配图请回到[用户手册](USER-GUIDE.zh-CN.md)，直接运行阿拓示例。

IP Pic 默认推荐使用 GPT Image 2。它有三种真实出图方式；选一种即可：

| 你的情况 | 选择 | 配置放在哪里 |
|---|---|---|
| 正在使用 Codex | Codex Image Tool（推荐） | Codex 自己管理，不需要配置 API Key |
| 没有 Codex | OpenAI 官方 API，或宿主已接好的中转站 | Key、服务地址和模型放在宿主的安全配置中 |
| 已经有 ai-router | 宿主 `ai_router.generate_image` | 凭证和路由继续由你自己的 ai-router 管理 |

## Codex Image Tool（推荐）

Codex 内置图片生成使用 GPT Image 2，用量计入 Codex 使用额度。把下面的话发给 Codex：

```text
这次使用 Codex Image Tool 和 GPT Image 2 出图。
请显式调用 `$imagegen`，完整使用 ip-pic 生成的提示词、画面尺寸和角色参考图。
出图后继续完成 IP Pic 的逐图检查，并把真实图片给我看。
```

你不需要配置 API Key。当前任务内不必反复发送这段话。

## 没有 Codex：OpenAI 官方 API

```text
我没有 Codex。请为 ip-pic 使用 OpenAI 官方图片 API 和 GPT Image 2。
请引导我把 `OPENAI_API_KEY` 保存到当前 Agent 的安全凭证存储，
或当前运行进程的环境变量中；不要让我把 Key 粘贴到聊天或写进项目文件。
官方 API 地址使用 `https://api.openai.com/v1`。
配置完成后先检查连接，再继续第一次配图。
```

Key 只能由你本人输入到宿主的安全凭证入口、系统密码存储或安全环境中。它不能写进 IP Pic、文章、Obsidian 笔记、角色资料或 Git 仓库。Agent 只能报告“已配置”或“未配置”，不能显示完整 Key。

IP Pic 的官方直连会自动区分两种调用：没有参考图时使用图片生成；带有角色参考图时使用图片编辑，并提交全部已选择的授权参考图。它不能为了继续运行而丢掉参考图。

配置 Key 后，Agent 还要确认账户可使用 GPT Image 2、组织验证状态和可用额度。Key 存在不等于已经具备出图权限。

## 没有 Codex：已有图片中转站

中转站不是 OpenAI 官方直连。把中转站的地址、Key 和模型写入宿主工具或 ai-router 的用户级配置，不要写入 IP Pic。

```text
请把我已有的图片中转站接成当前宿主的图片工具，或接入我自己的 ai-router。
地址、Key 和模型只保存到宿主或 Router 的用户级安全配置，
不要写进 ip-pic、文章、角色资料或项目仓库。
接好后先确认它能接收提示词、画面尺寸和角色参考图，再继续配图。
```

中转站 Key 也必须由你本人在安全入口输入，不能粘贴到聊天。IP Pic 没有一个通用于所有宿主的“中转站配置文件”；具体位置由当前宿主或 Router 决定。

## 已经有 ai-router

如果宿主已经注册了 `ai_router.generate_image`：

```text
请检查当前宿主是否已有 `ai_router.generate_image`。
如果有，就用它完成 ip-pic 的真实出图，
完整传入提示词、画面尺寸、角色参考图和预期输出位置。
不要读取、显示或修改 ai-router 的凭证、provider、路由、重试或 fallback 配置。
```

ai-router 的地址、Key、模型和路由仍保存在它自己的用户级配置中，不写入 IP Pic。

## 第一次检查结果

让 Agent 只报告状态，不显示凭证：

```text
图片工具检查结果：
连接来源：
出图方式：
实际模型：
是否支持角色参考图：
是否会产生单独 API 费用：
```

“是否支持角色参考图”必须为“是”，才能继续固定角色流程。使用官方 API 或中转站时，Agent 还应说明是“OpenAI 官方”还是“第三方中转”。单独产生 API 费用前必须先告诉你并得到确认。

## 仍然无法出图

`prompt-only` 不会生成图片，只会准备提示词和出图合同。Agent 必须明确说“尚未真实出图”，不能把它当成完成。

默认选择顺序是：Codex Image Tool → 已验证支持参考图的宿主图片工具 → 已注册的 ai-router → OpenAI 官方 API → `prompt-only`。
