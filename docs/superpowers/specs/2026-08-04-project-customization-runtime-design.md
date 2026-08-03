# IP Pic 项目级角色与风格定制运行时设计

## 状态

Approved for implementation，2026-08-04。

## 问题与根因

普通用户手册已经告诉用户可以让 Agent 保存自己的角色、参考图、风格和导演习惯，但当前 Skill 只有公开内置角色、六种官方渲染风格和单次 brief 覆盖能力，没有项目级持久化、版本、激活或回退运行时。现状属于“文档承诺存在，确定性产品能力缺失”，根因在 Skill 的状态管理和编译解析层，不是图片后端。

继续让 Agent 任意编辑安装目录中的 JSON 会造成四类问题：

- 升级 Skill 时覆盖用户配置；
- 用户隐私进入公开仓库或 Skill 安装包；
- 缺少版本和回退，Agent 修改错误后无法恢复；
- 各宿主 Agent 写出的结构不一致，编译结果不可审计。

## 产品结果

用户只需用自然语言告诉 Agent：

> 把我的角色保存为“小禾”，参考图用 `assets/xiaohe.png`。以后默认使用。  
> 新增一个“温暖蜡笔”风格，继承极简线稿，颜色更温暖、线条略粗。  
> 保存“认真拆解”导演动作：身体前倾、看向流程板、右手移动卡片，表情专注。

Agent 负责把自然语言整理为结构化草稿；Skill 负责校验、生成变更预览，并在用户明确确认后写入当前内容项目的 `.ip-pic/`。之后用户可以按名称使用、更新为新版本、切回旧版本或设为默认。安装目录保持只读，所有私人信息只保存在用户项目。

## 用户旅程

### 首次保存角色

1. Agent 收集角色名称、外貌、性格、至少三个连续性锚点、素材授权依据与参考图用途。
2. Agent 调用 `plan create character`，Skill 返回标准化预览、目标版本和风险提示，不改变项目状态。
3. Agent把预览用自然语言展示给用户。
4. 用户明确说“确认保存”后，Agent 使用同一计划调用 `apply`。
5. Skill 写入不可变版本、更新注册表并生成回执。用户可选择把它设为默认角色。

### 新增或修改个人风格

1. 用户描述希望的视觉感觉。
2. Agent 选择一个官方基础风格，并只提取线条、材质、色彩、形状和表面语气。
3. Skill 拒绝角色身份、参考图、场景、画幅、交付模式、模型、provider 和凭证字段。
4. 修改永远创建新版本；旧版本仍可查看和激活。

### 保存导演预设

导演预设可保存动作、基础表情、个性化表情描述、强度、面部线索、视线目标、头部姿态和身体姿态。个性化表情必须以七种稳定基础表情之一为底座，避免任意描述破坏可控性。

### 在文章配图中使用

用户可以说“用小禾、温暖蜡笔和认真拆解给这篇文章配图”。Agent 在 brief 中放入项目资产选择；编译器从当前项目解析已激活或指定版本，生成与内置能力相同的 director plan、prompt、render handoff 和 manifest。

优先级固定为：

1. 原版导演和模板默认值；
2. 当前项目激活或点名的导演预设；
3. 本次任务的显式 composition / character performance 覆盖。

本次任务显式要求永远优先，项目预设不能覆盖文章内容分析、构图家族、文字策略、画幅或交付模式。

### 更新和回退

“把小禾的外套改成蓝色”创建 `v0002`，不覆盖 `v0001`。  
“切回小禾上一版”通过一份新的激活计划把活动指针切回 `v0001`，不删除任何版本。

## 项目数据模型

```text
<user-project>/.ip-pic/
├── registry.json
├── characters/<asset-id>/v0001.json
├── styles/<asset-id>/v0001.json
├── directors/<asset-id>/v0001.json
├── plans/<plan-id>.json
├── receipts/<change-id>.json
└── .lock
```

`.ip-pic/` 不得是符号链接。资产 ID 只允许小写 ASCII 字母、数字和单个连字符，且必须以字母或数字开头结尾。显示名和中文别名保存在内容中，不用于路径。

### 注册表

`registry.json` 使用 `ip-pic-project-registry/v1`：

```json
{
  "schema_version": "ip-pic-project-registry/v1",
  "revision": 3,
  "active": {
    "character": {"id": "xiao-he", "version": "v0002"},
    "style": {"id": "warm-crayon", "version": "v0001"},
    "director": {"id": "serious-breakdown", "version": "v0001"}
  },
  "assets": {
    "character": {
      "xiao-he": {
        "display_name": "小禾",
        "aliases": ["小禾老师"],
        "versions": ["v0001", "v0002"]
      }
    },
    "style": {},
    "director": {}
  }
}
```

注册表只保存索引和活动指针，不复制角色隐私正文。`revision` 每次成功 apply 加一，用于发现计划生成后发生的并发漂移。

### 角色版本

角色版本使用 `ip-pic-project-character/v1` 外壳，核心 `profile` 必须通过已有 `ip-character-profile/v1` 校验。参考图路径必须：

- 是相对项目根目录的普通文件路径；
- 解析后仍位于项目根目录；
- 文件真实存在且不是符号链接；
- 明确标记 `authorized: true` 并说明用途。

Skill 保存相对路径，编译时才解析绝对路径用于受控 render handoff；公开 prompt 和 manifest 不包含项目绝对路径。

### 个人风格版本

个人风格使用 `ip-pic-project-style/v1`：

```json
{
  "schema_version": "ip-pic-project-style/v1",
  "id": "warm-crayon",
  "version": "v0001",
  "display_name": "温暖蜡笔",
  "base_style_id": "minimal-lineart",
  "scope": "render-style-only",
  "overrides": {
    "line": "略粗、自然、有轻微手绘抖动",
    "palette": ["暖黄", "砖红", "低饱和青绿"],
    "material": "干燥蜡笔与纸张颗粒"
  }
}
```

`overrides` 只允许 `line`、`palette`、`material`、`shape_language`、`surface_tone`、`background_treatment` 和 `typography_tone`。每个值有长度和数组数量上限。所有嵌套位置都拒绝身份、参考素材、角色 bible、场景、画幅、文字交付策略、provider、model、endpoint、token、authorization 和 `api_key`。

项目风格在官方基础风格的深拷贝上合并为渲染风格提示，不修改官方注册表，也不冒充官方风格 ID。

### 导演预设版本

导演预设使用 `ip-pic-project-director/v1`，可包含：

- `action`：最多 160 个字符；
- `character_performance.expression_preset`：七种稳定基础表情；
- `expression_description`：最多 120 个字符；
- `intensity`；
- 最多两个 `facial_cues`；
- `gaze_target`；
- `head_pose`；
- `body_pose`：最多 120 个字符。

导演预设不得写入构图家族、画幅、文字策略、交付模式、角色身份、参考图或后端字段。

## 变更计划与 API

公开入口为 Agent 使用的确定性命令：

```text
python3 scripts/manage_ip_pic_project.py plan-create \
  --project-root <project> --kind <character|style|director> \
  --draft <draft.json> [--activate]

python3 scripts/manage_ip_pic_project.py plan-activate \
  --project-root <project> --kind <kind> --id <id> --version <version>

python3 scripts/manage_ip_pic_project.py apply \
  --project-root <project> --plan <plan.json> --confirm

python3 scripts/manage_ip_pic_project.py list \
  --project-root <project> [--kind <kind>]

python3 scripts/manage_ip_pic_project.py show \
  --project-root <project> --kind <kind> --id <id> [--version <version>]
```

普通用户手册不要求用户输入这些命令；Agent 按 Skill 工作流调用。

计划文件使用 `ip-pic-project-change-plan/v1`，至少包含唯一 `plan_id`、操作、标准化内容、目标版本、计划时的 registry revision、内容 SHA-256 和目标路径。`apply` 重新计算 hash、重新校验内容和目标路径，并确认当前 revision 未变化。计划内容、hash 或注册表发生变化时失败关闭。

## 原子性与不覆盖

- 使用项目内 `.lock` 独占创建锁；已有锁时停止并提示稍后重试。
- 版本文件从不覆盖；目标存在立即失败。
- 新版本先写同目录临时文件，`fsync` 后 `os.replace` 到不可变目标。
- 注册表写入临时文件并用 `os.replace` 替换。
- 如果版本写入后注册表更新失败，只清理本次创建且 hash 匹配的新版本，不触碰已有文件。
- 回执最后写入；回执失败不撤销已经成功的注册表事务，但命令必须明确报告 `applied_without_receipt`，下次可根据 registry 和版本 hash 重建回执。
- 变更计划不等于用户确认。没有 `--confirm` 不执行。

## 编译解析

`compile_ip_pic.py` 新增可选 `--project-root`。brief 可包含：

```json
{
  "project_customization": {
    "character": {"id": "xiao-he", "version": "active"},
    "style": {"id": "warm-crayon", "version": "v0001"},
    "director": {"id": "serious-breakdown", "version": "active"}
  }
}
```

缺少某类选择时使用该类活动资产；没有活动项目资产时维持现有阿拓、官方风格和原版导演行为。点名不存在、没有授权或校验失败的项目资产必须失败，不静默回落。

项目解析在 selection 校验和导演合并之前完成：

- 角色 profile 和授权素材注入 `visual`；
- 个人风格通过专用解析器返回官方基础风格加安全覆盖；
- 导演预设作为中间默认值合并；
- 任务显式值最后覆盖。

selection receipt 对项目风格只接受 `source=user-explicit`；`user-accepted-recommendation` 必须继续严格等于已发布的官方推荐。

公共 manifest 记录资产 ID、版本和内容 hash，不记录用户项目根目录或参考图绝对路径。受控 handoff 可以携带参考图本地路径供宿主工具调用，但不得回写公开仓库。

## 安全边界

- 不读取 `.env*`、凭证目录或项目外文件。
- 所有路径在打开前执行 `resolve` 和项目根包含关系检查。
- 拒绝 `.ip-pic`、版本文件、参考图或计划文件符号链接。
- 拒绝未知字段，避免 Agent 把业务内容或秘密顺手写入。
- 错误信息不回显完整角色资料、参考图绝对路径或敏感值。
- 不联网，不调用图片 API，不改变任何 provider 行为。
- 不写 Skill 安装目录、全局 Skill、原版 Image Factory 或公开仓库外的用户项目。

## 兼容性与迁移

- 没有 `.ip-pic/` 或没有 `--project-root` 的旧调用，输出保持不变。
- 六种官方风格、13 个结构模板、direct-integrated、two-step-publish 和后端 handoff 合同保持不变。
- 现有内联 `visual.ip_profile` 与 `composition` 仍受支持，并作为本次任务显式覆盖。
- 不自动导入历史私人资料。用户通过 Agent 明确创建项目资产。
- 当前为向后兼容的候选增量，版本提升为 `0.3.0-rc.3`。

## 验收

自动化必须覆盖：

- 角色、个人风格、导演三类草稿的正常与非法输入；
- 计划阶段无状态变化；
- 未确认 apply 失败；
- 不可变 `v0001` / `v0002`；
- list、show、按名称/别名/版本解析、激活旧版本；
- 计划篡改、registry 漂移、路径穿越、符号链接、锁、覆盖和秘密字段失败关闭；
- 活动和点名资产进入编译；
- 明确任务覆盖优先于导演预设；
- 项目绝对路径不进入 prompt 和公共 manifest；
- handoff 只包含已授权参考图；
- 原有无项目配置 brief 输出不回归；
- 官方风格与推荐逻辑不回归。

最后由主 Agent 在全新的临时用户项目中只按普通用户手册模拟：

1. 保存角色和参考图；
2. 保存个人风格；
3. 保存表情、动作、视线和身体姿态预设；
4. 用短文完成 direct-integrated prompt-only 编译；
5. 更新角色和风格得到新版本；
6. 切回旧版本并再次编译；
7. 验证拒绝计划和未确认计划不改变项目。

这次用户模拟证明配置持久化和编译集成，不冒充真实图片视觉 E2E。真实角色一致性、文字美观和风格效果仍需图片工具出图及人工看图验收。

## 文档要求

普通用户手册新增“把 IP Pic 调成你的专属工作流”，只给自然语言示例：保存角色、增加参考图版本、修改风格、保存动作/表情、查看版本和切回旧版。命令、JSON 字段和内部存储结构只放维护者文档。

SKILL.md 必须明确：

- Agent 在写入前展示预览并等待确认；
- 用户未确认时不得 apply；
- 所有私人配置只写当前项目 `.ip-pic/`；
- 不修改安装目录；
- 编译时自动解析项目默认或用户点名版本。

