# 凭证生命周期

`ip-pic` 不保存、打印或写入任何 API 凭证。公开 Skill 只在用户明确选择 `openai-direct` 且授权真实渲染时，从进程环境读取 `OPENAI_API_KEY`，并固定访问 `api.openai.com`。Codex Image Tool 与宿主 ai-router 的凭证归宿主运行时管理，本 Skill 不读取。

## 配置

1. 在操作系统密钥管理器、受控 shell 会话或宿主 secret manager 中设置 `OPENAI_API_KEY`。
2. 不要把凭证写进 brief、manifest、JSON、Markdown、命令历史、仓库文件或 Skill 目录。
3. 先用 `prompt-only` 完成无网络编译；只有用户明确要求真实渲染时才调用有副作用的后端。

## 轮换、吊销与删除

- 轮换：在 OpenAI 控制台创建替代密钥，更新外部 secret source，验证新密钥后吊销旧密钥。
- 吊销：发现凭证可能被未授权使用时，立即在 OpenAI 控制台移除对应密钥，并停止仍持有旧值的运行进程。
- 删除：从 shell 会话、密钥管理器或 secret manager 删除本地副本；检查生成目录，确认请求与回执中没有凭证值。
- 宿主 ai-router：按宿主产品自己的凭证生命周期文档处理；本 Skill 不提供导出、显示或迁移功能。

错误输出只说明缺少哪个环境变量，不回显变量值。任何日志、请求或回执出现 `api_key`、`authorization` 或 provider token 都是发行阻断项。
