# IP Onboarding

首次使用只收集身份一致性和授权所需信息。不要要求用户理解 schema，也不要把教程角色保存成用户身份。

## 进入条件

按顺序寻找：

1. 用户本次明确提供的角色资料、附件或路径；
2. 当前项目 `.ip-pic/ip-profile.json`。

两处都没有时才进入 onboarding。不要搜索其他私人目录，不要自动复制仓库示例。

## 先选角色来源

一次只问一个选择：

- **我的角色**：用本人或已获授权的真人照片生成原创卡通母版，再建立 profile。
- **悟空知识工匠**：本次读取 `examples/characters/wukong/profile.json`，预览 `examples/characters/wukong/preview.png`。
- **月兔地图师**：本次读取 `examples/characters/moon-rabbit/profile.json`，预览 `examples/characters/moon-rabbit/preview.png`。
- **学习向导阿拓**：本次读取 `examples/characters/ato/profile.json`，预览 `examples/characters/ato/preview.png`；`examples/characters/ato/source-synthetic-photo.png` 用来演示“合成照片到原创角色母版”，不是真人照片。

三个教程角色都必须由用户明确选择，不默认，也不把示例 profile 写入用户项目。教程结束后，仍没有用户 profile。

真正编译时，Agent 在本次输出目录建立临时运行 profile：复制所选教程 profile 的内容，并临时加入对应 `preview.png`，标记为 `purpose: appearance` 与 `authorized: true`。该文件只服务本次任务；不修改 Skill 内随附 profile，不写入 `.ip-pic/ip-profile.json`，也不把教程角色冒充成用户身份。这样三个真实出图方式都能自动获得一致性参考图，用户不需要补充 prompt。

## 先用教程角色验证出图

首次上手建议先选一个教程角色：

1. 用一段短文字生成 1 张图；
2. 成功后，再用一篇长文测试自动分析和多图输出；
3. 两次都跑通后，再建立自己的角色。

用户指令保持一句话。配图点、数量建议、`content_points`、`image_count`、brief、prompt 和 QA 都由 Agent 自动处理。

## 从真人照片建立卡通母版

确认照片属于用户本人，或用户已获得其中人物的授权。按已经配置的出图方式执行：

- **Codex Image Tool 或已有 `ai-router`**：在对话中附加真人照片和母版提示词，让已选图片工具生成母版。
- **直接 OpenAI API**：先运行 `doctor`；就绪后保持用户项目目录为工作目录：

```bash
python3 <skill-root>/scripts/openai_backend.py master --reference <project-photo-path> --output <project-character-master.png>
```

输入和输出都留在用户项目，不得写入 Skill 安装目录。若 `doctor` 返回 `unsupported_platform`，让用户改选其他方式。如果输出文件已存在，命令会在付费请求前停止；请改用新的输出文件名，不会覆盖已有母版。

- **`prompt-only`**：只输出母版 prompt。用户需使用外部图片工具生成并上传母版，或改选教程角色。

母版提示词使用以下约束：

```text
把这张本人或已获授权的真人照片转成原创卡通 IP 角色母版。保留可识别的发型、脸型、眼镜等非敏感外观锚点，但不要推断敏感属性；设计为全身角色，使用干净中性背景，同时展示正面、侧面、背面等多视角和 4 个常用表情。造型简洁，适合文章系列配图并能跨图保持一致。无文字、水印或 logo，不模仿任何第三方角色特征。
```

图片工具完成母版并由用户确认视觉效果后，再从母版提取 profile。未经用户确认，不写文件。不得把 `prompt-only` 的 prompt 文本误报成已经生成的母版图片。

## 建立自己的 profile

严格一次问一个问题；用户已经提供的信息不要重复询问。

1. `ownership.status`：`user_owned`、`licensed` 或 `authorized`。
2. `ownership.basis`：一句话说明权利来源，不需要上传合同。
3. `identity`：角色名称和一句身份描述。
4. `appearance`：整体外观和至少一个签名特征。
5. `personality.traits`：影响动作和表情的 2～4 个性格词。
6. `continuity_anchors`：跨图不可漂移的轮廓、配色、服装或道具。
7. 可选授权参考图：每张注明 `purpose` 与 `authorized: true`。

普通用户不手写 JSON。Agent 收集完成后生成 `.ip-pic/ip-profile.json`。参考图路径只进入 render request，不进入 prompt 正文；授权素材库存不等于每张图都要发送，只选当前图片确实需要的参考素材。

## 增加动作与表情

- `.ip-pic/assets/poses/`：站立讲解、指向、思考、操作设备等动作；
- `.ip-pic/assets/expressions/`：开心、疑惑、专注、惊讶等表情；
- 新参考图不覆盖 `character-master.png`；
- profile 的 `references` 为每张图标明 `purpose` 与 `authorized: true`；
- 每次出图只选当前画面需要的少量参考图。

## 预览与保存

字段齐全后，展示权利来源、身份、外观、连续性锚点、性格、参考图数量和拟保存位置。

提醒用户 `.ip-pic/ip-profile.json` 是明文 JSON，可能被 Git 或云盘同步；不希望同步时，把 `.ip-pic/` 加入项目 `.gitignore`。

只有用户明确确认后才保存。若文件已存在，先说明将覆盖并再次确认。角色资料不得包含凭证、provider、model、服务地址或与角色无关的私人知识库。

## 停止

- 用户不知道角色权利来源；
- 用户要求模仿一个不属于自己的受保护角色；
- 身份一致性依赖的参考图不可访问；
- 用户尚未确认 profile 摘要或覆盖已有文件。
