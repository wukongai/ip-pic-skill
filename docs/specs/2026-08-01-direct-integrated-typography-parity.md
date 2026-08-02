# Direct-integrated 原版文字样式等价修正

## 背景

公开候选的 `direct-integrated` 真实 E2E 已能生成正确中文，但标题字形偏细、偏楷宋，未复现原版实际工作流中的粗字、单条手绘强调线和蓝色辅助层级。

原版 CLI 只编译“少量短标题、标签或手写说明”的内容约束；原版宿主工作流还会读取 `references/typography-system.md`，把文字视觉规则补进渲染上下文。公开版真实 E2E 直接消费 CLI prompt，因而丢失了宿主层补充。

## 目标

保持 `direct-integrated` 一次生成图文融合，不切换到 `two-step-publish`，并把原版宿主文字系统编译为稳定、可测试的 prompt 合同。

## 文字视觉合同

`direct-integrated` prompt 必须包含一个独立的“直出中文字样式”结构块：

- 核心观点为 8–18 个汉字，最多三行；
- 主标题使用大号、厚重、端正的黑色中文展示字，视觉接近现代粗黑体或稳重的编辑型宋黑混合；
- 禁止楷体、书法体、儿童体、细宋体、细字重和空心描边字；
- 全图最多一组强调线：标题下方一条不规则手绘线，长度约为标题字块的 55%–82%；
- 栏目名使用端正、中等偏粗的说明蓝字，参考 `#4B79A6`；
- 补充判断使用更小的 medium/semibold 浅蓝字，参考 `#6E93B7`；
- 文字仍需与人物动作、物件和信息路径形成一个整体，不得退化为独立海报标题卡；
- 不得同时使用整词红字、多条红线和红色框。

这些约束来源于原版 `skills/ip-illustration-factory/references/typography-system.md`，不复制私人身份、品牌、参考图片或路径。

## 边界

- `direct-integrated` 仍是一次生成，默认选择不变。
- `two-step-publish`、视频关键帧确定性文字脚本和字体回退链不变。
- 四种后端只消费更新后的同一 render handoff，不允许各自追加或改写文字规则。
- 本次不开放用户字体配置；后续可在不改变默认 recipe 的前提下增加公开 typography preset。
- 私有上游不修改。

## 可执行设计

新增 `src/ip_pic/typography.py`，集中提供不可变的 direct-integrated prompt 行。`src/ip_pic/compiler.py` 只在 `delivery_mode=direct-integrated` 时插入该结构块。

回归测试直接验证：

1. direct-integrated prompt 含完整粗字、单条线、蓝色层级与禁用字形合同；
2. two-step prompt 不含直出文字样式块；
3. 原版 typography 事实源仍包含相同语义，防止公开 recipe 脱离唯一行为事实源；
4. 后端 handoff 保持只读传递，不产生后端分叉。

## 验收

- 新回归测试在实现前因缺少“直出中文字样式”块而失败；
- 实现后新增测试、47 项既有行为测试、64/64 parity 和发行扫描全部通过；
- 使用与上一轮相同的阿拓内容重新运行 Codex Image Tool 真实 E2E；
- 人工确认标题比旧候选更粗、更端正，并出现单条手绘强调线；
- 结构测试与真实视觉结论分开记录。
