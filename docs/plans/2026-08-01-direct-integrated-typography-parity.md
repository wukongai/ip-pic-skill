# Direct-integrated Typography Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让公开版 direct-integrated 一次直出恢复原版粗字、单条手绘强调线和蓝色辅助层级。

**Architecture:** 将原版宿主层 typography 规则提取为独立的公开 prompt recipe，由编译器在 direct-integrated 模式确定性注入；后端继续只消费统一 handoff。two-step 与视频确定性文字层保持不变。

**Tech Stack:** Python 3、`unittest`、JSON prompt/manifest 合同。

## Global Constraints

- 不修改调用方通过 `IMAGE_FACTORY_SOURCE` 提供的原版只读事实源。
- 不把 direct-integrated 改成 two-step-publish。
- 不公开私人身份、参考图片、品牌或私有路径。
- 不增加字体配置界面。
- 不 push、tag、发布 Release 或修改 Global Skill。

---

### Task 1: 锁定原版 direct-integrated 文字 recipe

**Files:**
- Create: `src/ip_pic/typography.py`
- Modify: `src/ip_pic/compiler.py`
- Modify: `tests/test_selection_and_compiler.py`
- Modify: `tests/test_compiler_dual_end.py`

**Interfaces:**
- Consumes: `delivery_mode` 与原版 `references/typography-system.md` 的公开视觉规则。
- Produces: `direct_integrated_prompt_lines() -> tuple[str, ...]`。

- [ ] **Step 1: Write the failing tests**

在 `tests/test_selection_and_compiler.py` 断言 direct prompt 包含“直出中文字样式”、粗黑体、禁止楷体、55%–82% 单条手绘线、`#4B79A6` 和 `#6E93B7`；断言 two-step prompt 不含该块。

在 `tests/test_compiler_dual_end.py` 读取原版 typography reference，断言公开 recipe 的每项语义都有原版事实证据。

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
IMAGE_FACTORY_SOURCE="$IMAGE_FACTORY_SOURCE" \
python3 -m unittest \
  tests.test_selection_and_compiler \
  tests.test_compiler_dual_end -v
```

Expected: FAIL，因为当前 direct prompt 没有“直出中文字样式”结构块。

- [ ] **Step 3: Implement the minimal recipe**

在 `src/ip_pic/typography.py` 返回固定 prompt 行；在 `src/ip_pic/compiler.py` 的 direct 分支追加：

```python
lines.extend(["", "【直出中文字样式】", *typography.direct_integrated_prompt_lines()])
```

- [ ] **Step 4: Run focused tests to verify GREEN**

执行 Step 2 同一命令，预期全部 PASS。

- [ ] **Step 5: Commit**

```bash
git add \
  src/ip_pic/typography.py \
  src/ip_pic/compiler.py \
  tests/test_selection_and_compiler.py \
  tests/test_compiler_dual_end.py
git commit -m "fix: restore direct typography parity"
```

### Task 2: 文档、发行门禁与真实视觉复验

**Files:**
- Modify: `references/typography-system.md`
- Modify: `README.zh-CN.md`
- Modify: `README.en.md`
- Modify: `parity/ip-parity-manifest.json`
- Test: `tests/test_release_gate.py`

**Interfaces:**
- Consumes: Task 1 的固定 recipe。
- Produces: 对外默认行为说明、事实源映射和真实 E2E 证据。

- [ ] **Step 1: Add regression assertions**

断言发行物明确说明 direct-integrated 使用原版公开 recipe，同时没有声称字形像素级固定或要求私人字体文件。

- [ ] **Step 2: Run release test to verify RED**

Run:

```bash
python3 -m unittest tests.test_release_gate -v
```

Expected: FAIL，因为文档尚未声明该 recipe。

- [ ] **Step 3: Update public documentation and mapping**

补充 direct-integrated 的粗字、单线和蓝色层级说明；记录其来源为原版 typography reference 的 `sanitize + compile`，不增加字体配置。

- [ ] **Step 4: Run all automated gates**

```bash
IMAGE_FACTORY_SOURCE="$IMAGE_FACTORY_SOURCE" \
IP_PIC_PRIVATE_SOURCE_ID="$IP_PIC_PRIVATE_SOURCE_ID" \
python3 -m unittest discover -s tests -v

IP_PIC_PRIVATE_SOURCE_ID="$IP_PIC_PRIVATE_SOURCE_ID" \
python3 scripts/verify_parity.py \
  --source-root "$IMAGE_FACTORY_SOURCE"

python3 scripts/verify_release.py
```

Expected: all tests PASS，64/64 mapped，release errors 为空。

- [ ] **Step 5: Run real Codex Image Tool E2E**

用上一轮阿拓 `direct-integrated + 16:9 + minimal-lineart` 内容编译新目录并真实生成。不得覆盖旧图。

Expected: 标题较粗、端正，标题下仅一条手绘强调线；QA receipt 仍保持 `visual_acceptance=pending_human`。

- [ ] **Step 6: Commit and sync project E2E copy**

显式暂存文档、映射和测试后提交；从提交快照生成干净 archive，备份并替换调用方通过 `IP_PIC_E2E_TARGET` 提供的项目级测试副本：

```text
$IP_PIC_E2E_TARGET
```

在项目级副本重新运行全部自动化门禁。
