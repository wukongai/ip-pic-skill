# IP Pic Agent-first 用户手册恢复计划

日期：2026-08-02
依据：`docs/superpowers/specs/2026-08-02-beginner-user-manual-design.md`

## Task 1：固定旧流程与当前错误基线

1. 从历史备份读取旧版安装和首次使用流程。
2. 保留当前命令密集型手册，并以独立 Git 提交固定。
3. 先写失败测试，锁定 Agent 安装、阿拓参考图、短段落、Obsidian 文章和自然语言定制。

## Task 2：按受众拆分手册

1. 将完整命令资料迁移为 `MAINTAINER-GUIDE.*`。
2. 将 `USER-GUIDE.*` 恢复为完全 Agent-first 的小白流程。
3. 重写 `README.*` 为公开地址和一句话安装入口。
4. 更新 `SKILL.md`，让普通用户直接描述配图任务，其余步骤由 Agent 内部完成。
5. 保留原版 direct-integrated、two-step-publish、字体和手绘强调线语义。
6. 从普通用户入口删除版本号、安装位置、内部检查门禁和“用户不需要懂某技术”的解释性文案。

## Task 3：文档和行为验证

1. 运行文档合同测试，检查所有链接和禁用技术词。
2. 运行全量单元、parity、release、隐私与凭证门禁。
3. 运行 Skill Engineering、Skill Up 与 Microsoft Waza 检查。
4. 让全新 Agent 仅阅读普通用户手册，模拟完整上手并评分。
5. 对任何真实阻断返回 Task 1–3 修正。

## Task 4：保留版本并同步测试副本

1. 将 Agent-first 手册作为新 Git 提交，保留此前技术手册基线提交。
2. 备份项目级测试副本。
3. 仅在自动化验证全部通过后，同步到 `test-table/ip-pic-e2e/.agents/skills/ip-pic`。
4. 不 push、不 tag、不发布 Release、不修改 Global Skill。

## 人工验收

自动化结束后仍需用户执行：

- 公开地址发布后的全新安装；
- 阿拓参考图真实看图；
- direct-integrated 粗手写中文与手绘强调线；
- two-step-publish 字体效果；
- 一小段和整篇 Obsidian 文章的连续性与整体观感。
