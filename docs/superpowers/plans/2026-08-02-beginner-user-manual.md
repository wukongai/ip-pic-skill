# IP Pic 傻瓜式用户手册实施计划

日期：2026-08-02
依据：`docs/superpowers/specs/2026-08-02-beginner-user-manual-design.md`

## Task 1：先建立文档与用户路径回归测试

涉及文件：

- 新增 `tests/test_documented_user_flows.py`
- 更新 `tests/test_identity_and_license.py`

步骤：

1. 写失败测试，要求中英文主手册、定制说明、两步文字合成 CLI 和完整示例存在。
2. 写失败测试，验证文档引用的仓库内相对路径都存在。
3. 写失败测试，验证合同不引用不存在的脚本或伪造输出文件。
4. 写失败测试，验证显式字体覆盖不会继承内置 TTC face 索引。
5. 写失败测试，拦截已发现的私人外貌/服装残留措辞。
6. 运行新增测试并记录 RED。

## Task 2：补齐手册所需的最小真实接口

涉及文件：

- 新增 `scripts/compose_publish_layout.py`
- 更新 `src/ip_pic/publish.py`
- 更新 `src/ip_pic/compiler.py`
- 更新 `skill.contract.yaml`

步骤：

1. 为 `run-manifest.json` 中的 `publish_layout` 提供薄命令行包装。
2. 默认写入独立 `publish-layout.json`，并保持非覆盖输出策略。
3. 显式 `--font-path` 时把各文字角色的 font index 归零。
4. 对用户显式提供的角色 profile 调用公开 profile 校验器。
5. 修正合同中的实际脚本名称和 selection receipt 位置。
6. 运行 Task 1 测试直至 GREEN。

## Task 3：重写中英文傻瓜式手册与定制教程

涉及文件：

- 新增 `USER-GUIDE.zh-CN.md`
- 新增 `USER-GUIDE.en.md`
- 新增 `references/customization.md`
- 更新 `README.md`
- 更新 `README.zh-CN.md`
- 更新 `SKILL.md`
- 更新 `references/README.md`
- 更新 `references/delivery-modes.md`
- 更新 `references/qa-checklist.md`
- 更新 `references/style-variants.md`
- 更新 `references/user-choice-flow.md`
- 更新 `examples/article-brief.json`
- 更新 `examples/video-square-brief.json`
- 新增必要的 two-step 示例

步骤：

1. 以“准备 → 验证 → 选择模式 → 编译 → 渲染 → 合成 → QA → 重做”为固定顺序。
2. 每一步给出命令、参数含义、成功标志、预期文件和常见失败。
3. 给出自有/授权角色素材和 `ip_profile` 的安全替换流程。
4. 给出六种内置风格的选择表。
5. 准确区分文章 selection receipt 与视频 template。
6. 准确区分 direct-integrated 与 two-step-publish 的字体能力。
7. 给出个人 fork 修改风格、新增风格、测试和回退教程。
8. 删除或修正所有与实际实现矛盾的旧描述。

## Task 4：独立 Agent 用户模拟与技术复核

涉及文件：

- 项目测试输出目录中的模拟记录和评分

步骤：

1. 将候选 Skill 复制到一次性目录。
2. 让全新 Agent 只能依据公开手册完成 prompt-only 流程。
3. 让 Agent 用普通用户语言记录每个卡点并按 100 分制评分。
4. 让独立技术复核者核对全部命令、路径、输入和输出合同。
5. 对阻断项返回 Task 1–3 修正，直到评分不低于 90。

## Task 5：同步项目级测试副本并完成发布前验证

步骤：

1. 运行全部单元、合同、parity、release 和隐私扫描。
2. 运行 Skill Engineering、Skill Up 与 Microsoft Waza 检查。
3. 只在全部自动化验证通过后更新项目级测试副本。
4. 在项目测试输出目录生成绑定绝对路径的 `START-HERE-USER-MANUAL-TEST.md`。
5. 明确列出仍需用户人工执行的真实后端与视觉验收，不把结构测试冒充视觉通过。

## 停止条件

- 任一公开 IP 能力未映射。
- 任一手册命令不存在或无法按文档执行。
- 发现个人身份、凭证、私有路径或未授权素材残留。
- 自动化验证失败。
- 用户模拟仍存在阻断步骤。

满足停止条件时，不更新 Global Skill，不 push，不 tag，不发布 Release。
