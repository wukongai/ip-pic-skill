# IP 角色表演参数

角色表演回答“角色如何对正在发生的事作出反应”。它与身份、动作、渲染风格和版式分别管理：

- `visual.ip_profile` 定义“是谁”以及跨图不可漂移的身份锚点；
- `composition.action` 定义身体正在做什么；
- `composition.character_performance` 定义表情、视线和头部姿态；
- `render_style_profile` 只决定同一表演如何被线稿、毛毡、贴画或版画呈现；
- `layout_profile` 决定图文如何占位，不改变角色态度。

不要把某个表情硬编码进单个风格模板。否则换风格就会丢失角色态度，并形成“风格 × 表情 × 画幅”的模板组合爆炸。

## 输入合同

每张 IP 图可在 `composition` 中提供：

```json
{
  "character_performance": {
    "expression_preset": "skeptical-check",
    "intensity": "balanced",
    "gaze_target": "decision-dial",
    "facial_cues": ["one-brow-raised", "closed-mouth-wry-smile"],
    "head_pose": "slight-tilt"
  }
}
```

### 核心字段

| 字段 | 类型 | 默认值 | 作用 |
|---|---|---|---|
| `expression_preset` | enum | `focused-operate` | 一次选择完整的角色态度；是用户最常用的入口。 |
| `intensity` | enum | `subtle` | `subtle / balanced / strong`；控制表现幅度，不改变人物年龄和身份。 |
| `gaze_target` | string | 当前动作对象 | 可写 `viewer`、`off-frame` 或具体物件 id，使眼神服务画面叙事。 |

### 可选微调

- `facial_cues`：只在确有必要时覆盖预设，使用 0–2 个提示，如 `one-brow-raised`、`brows-furrowed`、`closed-mouth-smile`、`deadpan-mouth`、`eyes-widened`。
- `head_pose`：`neutral / slight-tilt / lean-in / turn-back`。头部姿态必须与身体朝向和动作物理关系兼容。

普通用户只需要选择预设；`facial_cues` 和 `head_pose` 留给批量镜头校准或精修，不能成为每次必填项。

## 表情预设

| expression_preset | 中文含义 | 适用内容 | 默认表演线索 |
|---|---|---|---|
| `calm-explain` | 平静讲解 | 背景说明、概念解释 | 目光稳定、嘴角放松、眉形中性 |
| `focused-operate` | 专注操作 | 流程、执行、工具使用 | 视线锁定对象、轻收眉、闭口专注 |
| `skeptical-check` | 怀疑审视 | 风险、反常识、核验 | 单侧挑眉、轻微歪嘴、头部微倾 |
| `realization` | 恍然大悟 | 转折、发现、新结论 | 眼睛略睁、眉毛抬起、身体微前倾 |
| `concerned-warning` | 担忧提醒 | 警告、失败、代价 | 眉心轻收、嘴角克制、看向风险源 |
| `confident-conclusion` | 笃定收束 | 结论、方法、决策 | 稳定直视或看向成果、轻微闭口笑 |
| `playful-deadpan` | 一本正经地搞怪 | 丑萌、反差幽默 | 无辜或冷静表情与荒谬动作形成反差 |

`playful-deadpan` 只定义角色态度，不自动切换毛毡或丑萌风格；它可以被线稿、贴画、手绘和艺术版画共同使用。

## 约束与优先级

1. 内容语义先决定 `expression_preset`，动作对象再决定 `gaze_target`，最后才由风格决定表现材质。
2. 表情不能替代认知动作。角色仍必须推动、检查、连接、拆解或操作主题装置。
3. 默认 `subtle`，强调转折时可用 `balanced`；`strong` 仅用于明确需要的视觉爆点，不得持续整批使用。
4. 保持成熟脸型、眼镜、发型和服装锚点；禁止因夸张表情变成幼态大头、网红脸或陌生人物。
5. 相邻三张不得重复完全相同的 `expression_preset + gaze_target`；表情应随内容节奏变化，而不是随机轮换。
6. 当 `facial_cues` 与预设冲突时，以显式 `facial_cues` 为准；当表情与身份安全边界冲突时，以身份边界为准并降低强度。

## QA

- 能否不看文字就判断角色是专注、怀疑、发现、担忧还是笃定？
- 视线是否落在正在操作或判断的对象上，而不是无意义地看镜头？
- 表情是否跨风格保留同一态度，同时仍像同一个人？
- 表情是否抢走了“决策、流程、生意”等核心物理隐喻？若是，降低强度或删去微调线索。
