# IP Pic Release-Grade Real E2E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在全新隔离用户项目中按普通用户手册完成 `ip-pic` 发布级真实图片 E2E，形成可复验的图片、回执、截图、视觉 QA、手册插图和公开验证说明。

**Architecture:** 公开候选保持独立；专用测试项目创建一次性 `runs/2026-08-03-release-grade/` 证据包。机器可读矩阵和验证器负责确定性覆盖，Codex Image Tool 负责真实渲染，独立 Agent 负责新手流程、视觉 QA 和发布审计，Computer Use 负责用户可见截图。

**Tech Stack:** Python 3 标准库、现有 `ip-pic` 编译/渲染/QA CLI、Pillow、Codex Image Tool、Computer Use、Markdown、JSON。

## Global Constraints

- 原版 Image Factory 只读，不修改、不切换。
- 只修改隔离候选和专用测试项目；不修改 Global Skill。
- 不 push、不 tag、不创建 GitHub Release。
- 准备好的阿拓参考图必须存放在 Skill 外部，并实际进入所有身份连续性样本的 render handoff。
- 最终有效样本覆盖 13 / 13 正式结构、6 / 6 风格、16:9 / 1:1 / 3:4 / 9:16、direct-integrated、two-step-publish、长文五图和静态视频关键帧。
- 真实图片调用最多 24 次；不降低 QA 门禁来迁就调用上限。
- 后端不得改写 director plan、模板、文字策略、prompt、参考图选择、尺寸或 QA 合同。
- 所有公开文档和发行目录不得包含本机绝对路径、私人身份、凭证、provider、adapter、余额、fallback 或内部路由。
- 视觉 QA 必须区分 Agent 评审与作者本人签字，不得伪造人工确认。

---

### Task 1: 建立机器可读发布矩阵与失败基线

**Files:**
- Create: `$E2E_ROOT/tests/test_release_run_validator.py`
- Create: `$E2E_ROOT/tools/validate_release_run.py`
- Create: `$E2E_ROOT/fixtures/release-grade-matrix.json`

**Interfaces:**
- Consumes: 公开候选的 `templates/registry.json`、`profiles/render-styles.json` 和运行目录。
- Produces: `validate_run(run_root: Path) -> list[str]`；空列表代表确定性证据完整，非空列表逐项说明缺口。

- [ ] **Step 1: 写验证器失败测试**

```python
def test_empty_run_reports_all_release_grade_gaps(tmp_path):
    errors = validate_run(tmp_path)
    assert any("formal templates: 0/13" in item for item in errors)
    assert any("render styles: 0/6" in item for item in errors)
    assert any("authorized reference handoff missing" in item for item in errors)
    assert any("direct-integrated real image missing" in item for item in errors)
    assert any("two-step raw/final evidence missing" in item for item in errors)
    assert any("long batch: 0/5" in item for item in errors)
    assert any("visual qa missing" in item for item in errors)
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python3 -m unittest tests/test_release_run_validator.py -v`

Expected: FAIL，因为 `validate_release_run` 尚不存在。

- [ ] **Step 3: 实现最小验证器**

验证器读取 `matrix.json` 和每个 case 的 `case.json`、`run-manifest.json`、backend request、receipt、图片与 `qa/*.json`。必须计算：

```python
REQUIRED_TEMPLATES = {
    "custom-ip-handdrawn-article-v1",
    "custom-ip-handdrawn-video-content-first-v2",
    "custom-ip-handdrawn-video-portrait-v1",
    "ip-art-print-video-square-v1",
    "ip-editorial-video-square-v1",
    "ip-editorial-video-subtitle-safe-v4",
    "ip-editorial-video-v3",
    "ip-expressive-handdrawn-video-square-v1",
    "ip-minimal-lineart-video-square-v1",
    "ip-playful-craft-video-playback-v1",
    "ip-playful-craft-video-square-v1",
    "ip-pop-impact-video-square-v1",
    "ip-sticker-collage-video-square-v1",
}
REQUIRED_STYLES = {
    "minimal-lineart",
    "playful-craft",
    "sticker-collage",
    "expressive-handdrawn",
    "pop-impact",
    "art-print",
}
REQUIRED_CANVASES = {"16:9", "1:1", "3:4", "9:16"}
```

每个成功 case 必须满足：真实文件存在且不是 symlink、receipt 指向同一文件、参考图选择回执存在、QA 状态不是结构错误、图片尺寸与声明一致。`prompt-only` 不进入真实图片计数。

- [ ] **Step 4: 写完整运行通过测试**

使用 13 个最小假图片/manifest fixture，证明覆盖集合、5 图批次、two-step raw/final、失败重试和四后端状态均被识别。再删除任意一项，测试必须精确报告该项。

- [ ] **Step 5: 运行验证器测试并确认 GREEN**

Run: `python3 -m unittest tests/test_release_run_validator.py -v`

Expected: PASS，0 failures。

- [ ] **Step 6: 提交测试项目 harness**

显式提交三个文件，不提交运行输出。

---

### Task 2: 创建全新用户项目并由新手 Agent按手册建立第一次配图

**Files:**
- Create: `$RUN_ROOT/clean-user-project/article/first-example.md`
- Create: `$RUN_ROOT/clean-user-project/character-assets/ato-reference-01.png`
- Create: `$RUN_ROOT/clean-user-project/character-assets/ato-reference-01.sha256`
- Create: `$RUN_ROOT/clean-user-project/character-assets/ato-profile.json`
- Create: `$RUN_ROOT/inputs/first-example.txt`
- Create: `$RUN_ROOT/logs/novice-user-agent.md`

**Interfaces:**
- Consumes: 候选 Skill、普通用户手册、准备好的阿拓参考图。
- Produces: 干净项目、项目级 Skill、外部授权角色资产和新手操作记录。

- [ ] **Step 1: 复制公开 Skill 到项目级目录**

复制后运行 `diff -qr`，候选与 `.agents/skills/ip-pic` 必须零差异。历史输出和 Image Factory 源码不得进入 `clean-user-project`。

- [ ] **Step 2: 登记外部阿拓参考图**

项目角色资料必须与实际参考图一致，至少记录：

```json
{
  "path": "character-assets/ato-reference-01.png",
  "purpose": "identity-primary",
  "ownership": "user-owned-or-authorized",
  "required": true
}
```

记录 SHA-256，后续每个连续性 case 都引用同一文件；不得把图片复制进 `.agents/skills/ip-pic`。

- [ ] **Step 3: 派发无历史上下文的新手用户 Agent**

Agent 只读取 `USER-GUIDE.zh-CN.md`，执行手册中的安装/第一次示例提示词，记录它是否能自行发现项目、图片工具、保存位置、角色参考图和逐图确认流程。

- [ ] **Step 4: 保存 RED 基线**

如果新手 Agent跳过参考图、只生成 prompt、要求普通用户运行内部命令、覆盖旧图或宣称未生成图片为完成，记录原话和失败层级；在改手册前保留这份基线。

---

### Task 3: 编译 13 结构 / 6 风格真实矩阵

**Files:**
- Create: `$RUN_ROOT/matrix.json`
- Create: `$RUN_ROOT/cases/$CASE_ID/brief.json`
- Create: `$RUN_ROOT/cases/$CASE_ID/case.json`
- Create: `$RUN_ROOT/cases/$CASE_ID/compiled/`

**Interfaces:**
- Consumes: Task 2 的项目角色资料和参考图。
- Produces: 13 个互不覆盖的 director plan、prompt、render handoff 和 case 合同。

- [ ] **Step 1: 固定 13 个 case 的交叉覆盖**

| Case | Template | Style | Canvas | Mode | 业务 |
|---:|---|---|---|---|---|
| 01 | custom-ip-handdrawn-article-v1 | minimal-lineart | 16:9 | direct-integrated | 首次短文 |
| 02 | custom-ip-handdrawn-video-content-first-v2 | expressive-handdrawn | 9:16 | two-step-publish | 竖屏关键帧 |
| 03 | custom-ip-handdrawn-video-portrait-v1 | sticker-collage | 9:16 | direct-integrated | 竖屏人物 |
| 04 | ip-art-print-video-square-v1 | art-print | 1:1 | two-step-publish | 方屏 |
| 05 | ip-editorial-video-square-v1 | minimal-lineart | 1:1 | two-step-publish | 方屏关键帧 |
| 06 | ip-editorial-video-subtitle-safe-v4 | expressive-handdrawn | 9:16 | two-step-publish | 字幕安全 |
| 07 | ip-editorial-video-v3 | sticker-collage | 9:16 | direct-integrated | 竖屏编辑 |
| 08 | ip-expressive-handdrawn-video-square-v1 | expressive-handdrawn | 1:1 | direct-integrated | 长文第 1 图 |
| 09 | ip-minimal-lineart-video-square-v1 | minimal-lineart | 1:1 | direct-integrated | 长文第 2 图 |
| 10 | ip-playful-craft-video-playback-v1 | playful-craft | 3:4 | two-step-publish | 长文第 3 图 |
| 11 | ip-playful-craft-video-square-v1 | playful-craft | 1:1 | direct-integrated | 长文第 4 图 |
| 12 | ip-pop-impact-video-square-v1 | pop-impact | 1:1 | direct-integrated | 长文第 5 图 |
| 13 | ip-sticker-collage-video-square-v1 | sticker-collage | 1:1 | direct-integrated | 失败重做 |

- [ ] **Step 2: 为每个 brief 写入一致的授权参考图**

`visual.authorized_assets` 必须包含 Task 2 的参考图；编译后检查 `reference_plan`、backend request 和 selection receipt，参考图必须存在于 handoff，但本机绝对路径不得进入 prompt 正文。

- [ ] **Step 3: 编译每个 case**

每个 case 使用新的输出目录。编译后运行确定性断言：

```text
template_id == matrix.template
style_variant_id == matrix.style
delivery_mode == matrix.mode
authorized_assets count >= 1
selected identity-primary reference exists
prompt contains no local absolute path
```

- [ ] **Step 4: 保存编译矩阵摘要**

`matrix.json` 必须列出 case id、模板、风格、画幅、交付模式、业务、prompt 路径、request 路径、预期图片路径和 QA 路径。

---

### Task 4: 使用 Codex Image Tool 完成最多 24 次真实渲染

**Files:**
- Create: `$RUN_ROOT/outputs/$CASE_ID/raw.png`
- Create: `$RUN_ROOT/outputs/$CASE_ID/final.png`
- Create: `$RUN_ROOT/receipts/$CASE_ID.json`
- Create: `$RUN_ROOT/logs/image-calls.ndjson`

**Interfaces:**
- Consumes: Task 3 的完整 prompt、尺寸和同一张授权参考图。
- Produces: 13 个有效结构样本及最多 11 次定向重试。

- [ ] **Step 1: 逐 case 调用 Codex Image Tool**

每次调用必须传入完整 prompt 和准备好的参考图。`direct-integrated` 明确要求少量可读中文、粗重端正黑色主标题和单条手绘强调线；`two-step-publish` 明确要求 raw 无文字。

- [ ] **Step 2: 每次调用后立即保存原始结果**

不得覆盖已有图片。日志记录 case、attempt、调用方式、输入 prompt hash、参考图 hash、输出路径和结果状态，不记录任何凭证或私有路由。

- [ ] **Step 3: finalize 真实回执**

使用现有 `render_ip_pic.py finalize` 绑定 request、真实文件和 receipt id。hash、尺寸、路径和 symlink 检查必须通过。

- [ ] **Step 4: 对 two-step 样本运行确定性文字合成**

先验证 raw 无字且 hash 已记录，再运行 publish/video overlay。final 写新路径，合成后重新验证 raw hash 不变。

- [ ] **Step 5: 定向重做失败项**

纯插画、中文不可读、人物未使用参考图、构图冲突、字幕区侵入或水印等失败，只重做当前 case；成功项和 receipt 不变。累计调用达到 24 次仍有失败时停止并保持整体未完成。

---

### Task 5: 独立视觉 QA、批量连续性与故障恢复

**Files:**
- Create: `$RUN_ROOT/qa/$CASE_ID.json`
- Create: `$RUN_ROOT/qa/continuity-review.json`
- Create: `$RUN_ROOT/qa/reviewer-report.md`
- Create: `$RUN_ROOT/logs/failure-recovery.md`

**Interfaces:**
- Consumes: Task 4 的原始图片、final 图片、director plan、参考图和回执。
- Produces: 独立逐图 verdict、跨图连续性 verdict 和重试证据。

- [ ] **Step 1: 派发独立视觉 QA Agent**

Reviewer 不读取实现历史，只读图片与验收合同。每张报告必须包含：

```json
{
  "status": "pass|fail|needs_retry",
  "identity_continuity": {},
  "composition": {},
  "action_expression_gaze_pose": {},
  "typography": {},
  "safe_zone": {},
  "privacy_and_rights": {},
  "findings": []
}
```

- [ ] **Step 2: 检查长文五图**

Case 08–12 必须属于同一篇文章五个不同认知锚点；相邻图片不得重复 family、orientation 和 action，五张至少出现四种构图家族，身份锚点一致。

- [ ] **Step 3: 注入一次可恢复失败**

将 Case 13 的一次渲染标记为失败，运行“只重试失败项”。记录其余成功图片前后 hash 相同，并验证整批重建使用新目录。

- [ ] **Step 4: 主 Agent复核 reviewer**

主 Agent逐张查看真实图片，检查 reviewer 是否漏报明显错误；Critical / Important finding 必须修复并重新评审。

---

### Task 6: 验证四后端边界

**Files:**
- Create: `$RUN_ROOT/backend/codex-image-tool.json`
- Create: `$RUN_ROOT/backend/openai-direct.json`
- Create: `$RUN_ROOT/backend/host-ai-router.json`
- Create: `$RUN_ROOT/backend/prompt-only.json`
- Create: `$RUN_ROOT/backend/REPORT.md`

**Interfaces:**
- Consumes: 同一个已编译的中性 case。
- Produces: 四条路径的真实或安全失败关闭证据。

- [ ] **Step 1: Codex Image Tool**

复用一个真实 case 的 request、图片和 receipt，状态必须为真实 rendered。

- [ ] **Step 2: OpenAI Direct**

先只检查进程是否已安全配置 `OPENAI_API_KEY`，不显示值。存在时真实运行一次带参考图的编辑调用；不存在时运行缺凭证失败关闭、官方 endpoint allowlist、脱敏错误和引用文件校验，不声称真实出图。

- [ ] **Step 3: 宿主 ai-router**

仅通过 `providers_doctor` 预检，不读取任何 env。可用时真实调用并保存公开回执；不可用时保存结构化状态和 handoff 合同。

- [ ] **Step 4: prompt-only**

必须得到 `prompt_ready`、`rendered=false`，且没有伪造图片或 receipt。

- [ ] **Step 5: 对比上游 fingerprint**

四个 backend artifact 的 director plan、模板、prompt、尺寸、文字策略和参考图选择归一化后必须一致。

---

### Task 7: 用 TDD 改进普通用户手册和公开验证说明

**Files:**
- Modify: `tests/test_documented_user_flows.py`
- Modify: `USER-GUIDE.zh-CN.md`
- Modify: `USER-GUIDE.en.md`
- Modify: `README.zh-CN.md`
- Modify: `README.en.md`
- Create: `docs/VERIFICATION.zh-CN.md`
- Create: `docs/VERIFICATION.en.md`
- Create: `docs/assets/ip-pic-user-flow.png`

**Interfaces:**
- Consumes: Task 2 新手失败基线、Task 4–6 的真实证据。
- Produces: Agent-first 手册、流程插图、可替换插图锚点和准确的验证说明。

- [ ] **Step 1: 写失败测试**

新增断言：

```python
def test_public_guide_has_visual_and_honest_verification_scope(self):
    guide = (ROOT / "USER-GUIDE.zh-CN.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    verification = (ROOT / "docs/VERIFICATION.zh-CN.md").read_text(encoding="utf-8")
    self.assertIn("docs/assets/ip-pic-user-flow.png", guide)
    self.assertIn("IP-PIC-ILLUSTRATION:", guide)
    self.assertIn("大型内容图像工作流", verification)
    self.assertIn("真实图片 E2E", verification)
    self.assertIn("不同 Agent", verification)
    self.assertIn("Issues", verification)
    self.assertNotIn("作者没有时间测试", guide + readme + verification)
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python3 -m unittest tests.test_documented_user_flows.DocumentedUserFlowTests.test_public_guide_has_visual_and_honest_verification_scope -v`

Expected: FAIL，因为插图和验证说明尚不存在。

- [ ] **Step 3: 生成流程说明插图**

使用 Codex Image Tool 生成一张无私人身份、无品牌锁定的教程插图，表达“文章 → Agent → IP Pic → 逐图确认 → 保存到项目”。图片内不依赖小号中文，主要文字仍由 Markdown 提供。保存到 `docs/assets/ip-pic-user-flow.png`。

- [ ] **Step 4: 更新手册版式与插图锚点**

手册顶部展示流程图；每个主要模块加入类似：

```html
<!-- IP-PIC-ILLUSTRATION:first-run -->
```

锚点不显示占位文案，维护者以后可以在其下方加入自己的 IP 配图。

- [ ] **Step 5: 添加验证范围与反馈入口**

公开说明必须区分：自动化合同、真实 Codex E2E、其他后端真实/合同状态、Agent视觉 QA、未覆盖宿主差异。链接项目 Issues，不写本机路径和内部版本竞争信息。

- [ ] **Step 6: 运行测试并确认 GREEN**

Run: `python3 -m unittest tests.test_documented_user_flows -v`

Expected: PASS，0 failures。

- [ ] **Step 7: 提交候选文档和插图**

提交测试、中文/英文手册、README、验证说明和图片；不提交测试项目中的个人/外部参考图。

---

### Task 8: Computer Use 截图、视觉画廊与最终报告

**Files:**
- Create: `$RUN_ROOT/screenshots/01-clean-project.png` 至 `09-report-summary.png`
- Create: `$RUN_ROOT/VISUAL-GALLERY.md`
- Create: `$RUN_ROOT/REPORT.zh-CN.md`
- Create: `$RUN_ROOT/REPORT.json`

**Interfaces:**
- Consumes: 所有测试图片、QA、后端证据、手册和测试输出。
- Produces: 用户可直接检查的截图证据包和机器可读结论。

- [ ] **Step 1: 用 Computer Use 打开并截图关键页面**

截图覆盖：干净项目、手册首页、参考图登记、direct-integrated、two-step raw/final、1:1/9:16、长文五图、13 结构/6 风格、最终报告。

- [ ] **Step 2: 生成视觉画廊**

每张缩略图旁列出 case、模板、风格、画幅、交付模式、attempt、QA verdict，并链接原始图片、prompt、request 和 receipt。

- [ ] **Step 3: 运行机器验证器**

Run: `python3 tools/validate_release_run.py "$RUN_ROOT"`

Expected: `OK: release-grade evidence complete`，exit 0。

- [ ] **Step 4: 运行全部自动化验证**

Run:

```text
python3 -m unittest discover -s tests -v
python3 scripts/verify_release.py
skill-engineering doctor . --profile production --json
skill-engineering validate-eval-suite --suite tests/evaluation/suite.yaml --production
skill-engineering evaluate --suite tests/evaluation/suite.yaml --baseline-results tests/evaluation/baseline-results.json --candidate-results tests/evaluation/candidate-results.json --production
```

Alibaba Skill Up 和 Microsoft Waza 使用当前测试副本重跑；报告记录真实输出，不沿用旧结果。

- [ ] **Step 5: 独立发布审计**

Reviewer 检查公开候选、测试副本和证据包的一致性，重点审计私人信息、凭证、绝对路径、夸大声明、无真实图片的“通过”状态和未解决视觉 finding。

- [ ] **Step 6: 生成最终报告**

报告首屏只回答：结果、影响、仍未覆盖的环境、用户下一步。技术附录再列命令、case、hash 和回执。

- [ ] **Step 7: 最终非发布停止点**

测试完成后保持本地分支，不 push、不 tag、不发布 Release、不修改 Global Skill，等待用户查看截图和报告后单独确认发布。
