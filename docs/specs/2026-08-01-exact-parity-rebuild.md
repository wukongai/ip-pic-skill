# IP Pic 原版等价脱敏重建 Spec

## 状态与事实源

- 日期：2026-08-01
- 工作分支：`codex/exact-parity-rebuild`
- 产品名：`ip-pic` / “IP 配图”
- 唯一行为事实源：当前工作树中的 Image Factory `skills/ip-illustration-factory`、其共享 IP 核心、模板、脚本和回归测试。
- 失败对照：`/private/tmp/ip-pic-style-parity-20260731` 的 `0.2.0-rc.1`，只用于证明能力缺失。

## 观察到的回归

1. 原版正式表含 13 个结构模板；失败候选只有 8 个通用重写模板。
2. 原版 direct-integrated 三处要求图文融合并有文字存在/可读 QA；失败候选写成“文字可选”。
3. 原版当前 72 个 IP 相关回归测试通过。
4. 原版还有一个未列入正式表、但由回归测试保护的 top-card v5 兼容模板。
5. 原版有 6 个正交渲染风格；失败候选增加了一个非原版 selectable editorial style。

## 功能要求

### P1 完整导演

- 输入只需 `content.headline/summary/points` 与授权角色；视觉 subject、metaphors、action 和 character performance 可以省略。
- 输出 `ip-director-plan/v1`。
- 显式专家覆盖优先，director plan 必须反映最终合并值并保留默认 provenance。
- 相邻和最近 6 张满足原版构图、裁切、朝向、动作和表演轮换。

### P2 模板与风格

- parity manifest 必须登记原版 Skill 目录全部文件。
- 13 个正式结构模板逐一保留结构字段和 prompt 语义。
- top-card v5 保留兼容回归，不计入 13 个正式结构。
- 6 个渲染风格逐一保留；风格 profile 不得含身份、scene、canvas、delivery、provider 或凭证字段。
- 风格切换不得改变 template、角色、画布、delivery 或 director plan。

### P3 选择与画布

- IP 文章在编译前必须有 `selection_receipt.status=confirmed`。
- source 只能是 `user-explicit` 或 `user-accepted-recommendation`。
- 回执必须分别包含 business type、delivery mode、canvas 和 style variant。
- 推荐值必须先展示再被接受；模板默认不等于用户确认。
- 画布支持 16:9、1:1、3:4、9:16 与 320–8192 范围内自定义尺寸。

### P4 文字与发布

- direct-integrated 必须生成少量可读画面文字，纯插画为 QA FAIL。
- two-step raw 必须无字，final 必须有确定性标题层且 raw 不可发布。
- 视频关键帧 raw 必须无字，final 必须来自确定性 `video_text_overlay`。
- 数据模块只有源内容存在真实数字时可用。

### P5 参考图

- 支持 `primary_reference`、`native_multi_reference`、`reference_board`、`candidate_handoffs`。
- 每个素材必须含 path、purpose、ownership、required。
- 只选择本图需要的授权素材；候选 handoff 稳定且独立可执行。
- 教程角色不含私人参考图；用户参考图不写入 prompt 正文。

### P6 批量、重建与失败

- 短文可生成 1 张，长文按认知锚点生成 4–8 张。
- 批量输出 shot manifest、item manifest、batch receipt 和连续性报告。
- 部分失败保留成功图；重试只处理失败项。
- 整批重建创建新目录和新 manifest，不继承已否决图片或构图惯性。
- 每 3 张执行人物、构图、隐喻、文字和安全区 QA。

### P7 后端

- 四条公开路径消费相同 handoff。
- backend adapter 不得改写 prompt、director、template、manifest QA 或输出合同。
- OpenAI Direct 只从仓库外环境变量读凭证。
- Codex Image Tool 与 host ai-router 由宿主调用并回填真实文件；CLI 不伪造成功。
- prompt-only 不进行网络调用。

### P8 安全与发行

- 私人身份、外貌、服装、饰品、bible、品牌锁定、参考图、私有路径和业务信息零泄漏。
- Ian MIT LICENSE 与 NOTICE 保留；不分发小黑角色或示例图。
- 不包含知识卡片、封面、海报、OB、布丁、训练营或平台发布能力。
- 不包含私有 ai-router provider、adapter、凭证、余额、重试或 fallback。
- 所有输出新建；禁止覆盖、目录穿越和 symlink 逃逸。

## 机器验收

1. `python3 -m unittest discover -s tests -v`
2. `python3 scripts/verify_parity.py --manifest parity/ip-parity-manifest.json --source-root "$IMAGE_FACTORY_SOURCE"`
3. `python3 scripts/verify_release.py`
4. 原版/公开版同输入 golden 比较：director、template、prompt 文字策略、handoff、manifest、QA。
5. 三个真实后端 adapter + prompt-only 合同测试。
6. Codex Image Tool direct-integrated 真实 E2E。

## 人工视觉验收

- 阿拓跨 6 风格仍为同一角色。
- 13 个结构家族能观察到原版构图意图，而非模板名不同但画面同质。
- direct-integrated 的中文短字可读且与画面融合。
- two-step 和视频 overlay 字形、层级、安全区正确。
- 长文批次满足动作、表情、视线、朝向、尺度和构图轮换。

人工视觉未完成前，状态最多为“自动化与真实文件 E2E 通过，等待视觉验收”。
