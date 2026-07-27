# IP Onboarding

首次使用只收集身份一致性和授权所需信息。不要要求用户理解 schema，也不要把教程角色保存成用户身份。

## 进入条件

按顺序寻找：

1. 用户在本次请求中明确提供的角色资料、附件或路径；
2. 当前项目 `.custom-ip-illustration/ip-profile.json`。

都不存在时才进入 onboarding。不要搜索其他私人目录，不要自动复制仓库示例。

## 先选角色来源

一次只问一个选择：

- **我的角色**：用本人或已获授权的真人照片生成原创卡通母版，再建立 profile。
- **悟空知识工匠**：本次读取 `examples/characters/wukong/profile.json`，预览 `examples/characters/wukong/preview.png`。
- **月兔地图师**：本次读取 `examples/characters/moon-rabbit/profile.json`，预览 `examples/characters/moon-rabbit/preview.png`。

两个教程角色必须由用户明确二选一，不默认，也不把示例 profile 写入用户项目。教程结束后，仍没有用户 profile。

## 从真人照片建立卡通母版

确认照片属于用户本人，或用户已获得其中人物的授权。按第 2 步已经选择的出图方式执行：

- Codex Image Tool 或已有 `ai-router`：在对话中附加真人照片和母版提示词，让已选图片工具生成母版。
- 直接 OpenAI API：先运行 `doctor`；就绪后保持用户项目为工作目录，运行 `python3 <skill-root>/scripts/openai_backend.py master --reference <project-photo-path> --output <project-character-master.png>`。输入和输出都留在用户项目，不得写入 Skill 安装目录；若 `doctor` 返回 `unsupported_platform`，让用户改选其他方式。
  如果输出文件已存在，命令会在付费请求前停止；请改用新的输出文件名，不会覆盖已有母版。
- `prompt-only`：只输出母版 prompt。用户需使用外部图片工具生成并上传母版，或改选悟空知识工匠/月兔地图师教程角色。

母版 prompt 使用以下约束：

- 生成原创卡通表达，不模仿第三方受保护角色；
- 保留发型、脸型、眼镜等非敏感、可识别外观锚点；
- 不推断种族、健康、宗教等敏感属性；
- 生成全身、干净中性背景的角色母版；
- 包含正面、侧面、背面和常用表情；
- 不生成文字、水印或 logo。

图片工具完成母版并由用户确认视觉效果后，再从母版提取 profile。未经用户确认，不写文件。不得把 `prompt-only` 的 prompt 文本误报成已经生成的母版图片。

## 建立自己的 profile

严格一次问一个问题；用户已回答的字段不要重复问。

1. `ownership.status`：`user_owned`、`licensed` 或 `authorized`。
2. `ownership.basis`：一句话说明权利来源，不需要上传合同。
3. `identity`：角色名称和一句身份描述。
4. `appearance`：整体外观和至少一个签名特征。
5. `personality.traits`：影响动作和表情的 2～4 个性格词。
6. `continuity_anchors`：跨图不可漂移的轮廓、配色、服装或道具。
7. 可选授权参考图：每张注明 `purpose` 与 `authorized: true`。

参考图路径只进入 render request，不进入 prompt 正文。授权素材库存不等于每张图都要发送；只选当前图片确实需要的参考素材。

## 预览与保存

字段齐全后，展示：

- 权利状态与来源；
- 名称与身份；
- 外观、签名特征和连续性锚点；
- 性格；
- 已授权参考图数量；
- 拟保存位置 `.custom-ip-illustration/ip-profile.json`。

提醒用户该文件是明文 JSON，可能被 Git 或云盘同步；不希望同步时，把 `.custom-ip-illustration/` 加入项目 `.gitignore`，或本次只保留在对话中。

只有用户明确确认后才保存。若文件已存在，先说明将覆盖并再次确认。角色资料不得包含凭证、provider、model、服务地址或与角色无关的私人知识库。

## 停止

- 用户不知道角色权利来源。
- 用户要求模仿一个不属于自己的受保护角色。
- 身份一致性依赖的参考图不可访问。
- 用户尚未确认 profile 摘要或覆盖已有文件。
