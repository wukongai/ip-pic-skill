# 连续内容整批重生成规约

用于用户要求“全部重新生成”或在新会话从头生产 7 分钟口播配图。目标是重建 shot manifest，不继承已否决批次的 raw 图、prompt 漂移或构图惯性。

## 开始前

1. 重新读取口播稿，按段落转折和认知锚点规划镜头；不得从旧图片倒推内容。
2. 默认 1:1 方屏，建议每 14–20 秒一张基础关键帧；通过 下游视频工具 的推近、横移和局部裁切把单张使用时长控制在 8–12 秒。
3. 新建独立输出目录与 shot manifest。旧批次只保留为审计，不进入参考图集合。
4. 参考图只使用用户明确批准且有权使用的角色三视图、字体和画面基线。被否决为偏写实、工业泛化、UI 化、人物漂移或构图单调的输出全部排除。
5. 人物一致性批次只登记真实存在且获授权的人物素材与用途。
6. IP Pic 编译 prompt、共享 render handoff 与确定性 `video_text_overlay` 计划，随后交回主入口继续。

## Shot manifest 必填字段

- `anchor_id`、`source_excerpt`、`duration_hint`
- `kicker`、`headline`、`support`
- `structure_type`、`shot_type`、`composition_family`
- `ip_scale`、`crop`、`orientation`、`body_weight`、`action`
- `physical_metaphor`、`familiar_objects[]`、`orange_motion_path`
- `visual_anchor_position`、`subtitle_safe_zone`
- `text_layout_variant`: `square-left` 或 `square-right`；raw 必须为对应文字区预留连续白底。

## 批量轮换门禁

- 相邻镜头不得重复 `composition_family + crop + orientation + action`。
- 最近六张至少覆盖四种方屏构图家族；每六张至少有一次坐姿、一次俯视局部、一次双手近景、一次背侧身、一次跨画面对角动作和一次装置主导。
- 同一具象物件不得跨三个不相邻主题重复使用；天平、环形闭环、桥、磁扣等强隐喻在整批中需限制次数。
- 每张只有一个主隐喻系统；2–5 个物件必须由一条动作或路径统一。
- 静态文字只保留栏目名、核心观点和一行补充；逐字字幕由 下游视频工具 处理。

## 两阶段生产

1. Raw：只生成人物、动作、主题隐喻和明确的 `square-left/square-right` 文字留白；人物严格执行 `CARTOON-IDENTITY-001`，隐喻执行 `METAPHOR-001`。
2. Overlay：确定性叠加栏目名、核心观点、红色强调线和一行补充，执行 `IP-TYPE-001`；不得依赖模型正确生成标题。
3. 每完成 3 张做一次人物、构图、隐喻和字幕安全区 QA；不通过时只重生失败镜头，不把失败图继续当参考。
4. 对外预览、发布和后续 下游视频工具 输入只读取 `final_image`；raw 只留在 `_ip-pic/` 技术目录。

## 新会话交接语义

新会话收到“按 连续内容口播稿全部重新生成”时，应先展示新的 shot plan 与第一张 1:1 校准图；用户确认风格后再执行完整批次。除非用户明确要求，不复用旧输出目录中的任何生成图。
