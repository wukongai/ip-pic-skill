# IP Pic 仓库文档结构整理设计

## 背景

IP Pic 的公开仓库已经包含完整的中英文用户手册、图片工具接入说明和维护者手册，但六份长文档仍位于仓库根目录。它们与 `README`、`SKILL.md`、许可证、社区治理文件和工程合同混排，削弱了根目录作为“项目入口”的可读性。

本次只整理文档信息架构，不修改 IP 配图行为、用户旅程、模板、风格、渲染后端、隐私边界或发行能力。

## 失败模式与根因

失败模式：根目录同时承担项目入口、用户文档中心和维护者文档中心三种职责，导致文件职责不清，后续新增文档容易继续平铺。

根因层级：工程信息架构与确定性路径约束。修复应落在文件布局、链接和回归测试，不向 `SKILL.md` 增加新的自然语言禁令。

## 目标结构

根目录只保留以下三类文件：

1. 项目与 Skill 入口：`README.zh-CN.md`、`README.en.md`、`SKILL.md`。
2. 开源与社区治理：`LICENSE`、`NOTICE.md`、`UPSTREAM-LICENSE.txt`、`SECURITY.md`、`CONTRIBUTING.md`、`CHANGELOG.md`。
3. 工程配置与合同：`pyproject.toml`、`skill.contract.yaml`、`upstream.lock.json`、`.waza.yaml`。

六份长文档移动到 `docs/`：

| 当前路径 | 目标路径 |
|---|---|
| `USER-GUIDE.zh-CN.md` | `docs/USER-GUIDE.zh-CN.md` |
| `USER-GUIDE.en.md` | `docs/USER-GUIDE.en.md` |
| `IMAGE-TOOL-SETUP.zh-CN.md` | `docs/IMAGE-TOOL-SETUP.zh-CN.md` |
| `IMAGE-TOOL-SETUP.en.md` | `docs/IMAGE-TOOL-SETUP.en.md` |
| `MAINTAINER-GUIDE.zh-CN.md` | `docs/MAINTAINER-GUIDE.zh-CN.md` |
| `MAINTAINER-GUIDE.en.md` | `docs/MAINTAINER-GUIDE.en.md` |

`docs/VERIFICATION.*`、`docs/product.md`、`docs/architecture.md` 及现有 `docs/specs/`、`docs/plans/`、`docs/adr/`、`docs/reports/` 保持原位。

不新增 `docs/user/` 和 `docs/maintainer/` 子层。当前文档数量较少，平铺在 `docs/` 更容易发现，也避免给普通用户暴露过长路径。

## 链接策略

- 根目录 `README.*` 和 `SKILL.md` 使用 `docs/...` 链接进入完整文档。
- `references/README.md` 使用 `../docs/...` 链接。
- 移动到 `docs/` 的文档相互引用时使用同目录相对链接，例如 `IMAGE-TOOL-SETUP.zh-CN.md` 和 `VERIFICATION.zh-CN.md`。
- 历史 Spec、Plan 和 Changelog 中描述旧文件位置的文字保留，不把历史事实机械改写为当前路径。
- 非链接形式的维护命令如果要求 Agent 读取用户手册，应改为当前真实路径，避免未来执行失败。

## 测试设计

先在 `tests/test_documented_user_flows.py` 增加目录结构合同：

- 六份长文档必须全部存在于 `docs/`；
- 六份长文档不得继续残留在仓库根目录；
- README、SKILL、references 和文档内部所有活动链接必须指向存在的文件；
- 用户手册内容合同继续从新路径读取，确保本次迁移不改变小白流程；
- 中英文文档必须同时迁移，不能只整理中文版。

测试应先在旧结构上失败，再移动文件并修复引用使其通过。随后运行完整单元测试、发行门禁、凭证与私人路径扫描。

## 非目标

- 不改写用户手册正文。
- 不添加或删除公开插图。
- 不调整模板、风格、导演、文字层或后端行为。
- 不移动 GitHub 约定保留在根目录的许可证、Security、Contributing、Changelog。
- 不整理历史研发文档内容。
- 不推送远程仓库，除非用户另行确认。

## 验收标准

1. 根目录不再出现六份长文档。
2. 所有当前入口都能打开新路径中的对应文档。
3. 用户手册、图片工具说明和维护者手册的文件内容不因移动发生语义变化。
4. 文档流程测试、完整测试和发行门禁全部通过。
5. 隐私、凭证、私人绝对路径与许可证检查继续通过。
6. `git diff --summary` 明确显示六次 rename，除路径和链接外没有业务代码变化。

## 回退

本次变更在独立分支完成。若任一回归失败，保留失败证据并撤销该分支上的文档迁移提交；不覆盖远程 `main`，不修改 Image Factory 原版工作流。
