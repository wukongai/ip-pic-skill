# Ian Xiaohei 上游继承映射

本 skill 是 `Ian Xiaohei Illustrations` 的项目内架构派生适配，不安装为第二个全局入口。上游版本锁定在 [`upstream.lock.json`](../upstream.lock.json)。“派生”指工作流与工程结构有明确来源，不代表最终视觉必须接近未授权第三方角色样式。

## 保留的核心工作流

1. 先读正文，提炼认知锚点；不平均配图。
2. 每张只表达一个判断、流程、状态或隐喻。
3. 先选择结构类型，再发明低科技、怪诞但成立的物理隐喻。
4. 固定 IP 必须参与关键动作，不能只是贴纸或主持人立牌。
5. 示例只做工作流理解，不复制物件、姿态、空间拓扑或标签位置。
6. 每张单独生成并经过 QA；最终中文走确定性后处理。
7. 用镜头清单控制构图、尺度、朝向、动作和位置轮换。

## 明确解耦的视觉决策

- 人物尺度不继承：已授权角色视频默认 38%–52%，而不是小操作员尺度。
- 画风不继承：采用保留所选角色 profile 的连续性锚点的成熟卡通编辑插画。
- 字体系统不继承：采用粗黑中文主张与红色手绘强调线。
- 信息层级不继承：人物与主题共同主导，不强制“内容装置大于人物”。
- 数据版式不固定：只有存在真实数据时使用 data-evidence。

## 文件映射

| 上游文件 | 本地派生文件 | 修改 |
|---|---|---|
| `SKILL.md` | `../SKILL.md` | 保留工作流，接入 IP Pic 路由、dry-run/apply 与视频边界 |
| `references/style-dna.md` | `style-dna.md` | 仅保留可复用的克制、单图单意与少量强调色；人物尺度和编辑画风由本地 profile 重定义 |
| `references/xiaohei-ip.md` | `ip-role-and-action.md` | 将未授权第三方角色替换为用户自有真人 IP；保留“参与但不抢结构”原则 |
| `references/composition-patterns.md` | `composition-patterns.md` | 保留 8 类结构、物理隐喻法和动作池；增加人物尺度/朝向轮换 |
| `references/prompt-template.md` | `prompt-template.md` | 改成 image_brief + custom IP + raw/text-overlay 两阶段提示合同 |
| `references/qa-checklist.md` | `qa-checklist.md` | 增加内容主导、动作多样、平台安全区和角色一致性检查 |

## 明确的派生扩展

- 用户自有真人 IP 角色圣经和姿势库。
- 独立的已授权角色品牌 profile、编辑型镜头版式和中文字体系。
- 静态竖屏 / 移动端竖屏 9:16 关键帧。
- 一句大字观点与少量批注的确定性叠加。
- IP Pic 的 route / manifest / shared render handoff / review / publish 合同。

## 不继承的内容

- Ian 的“未授权第三方角色”角色外形、示例图和具体案例构图。
- 原仓库的全局安装方式；本项目只暴露 `ip-pic`。
- 微信二维码、作者营销资产和与配图生产无关的仓库内容。

来源：<https://github.com/helloianneo/ian-xiaohei-illustrations>，MIT License，Copyright (c) 2026 Ian。
