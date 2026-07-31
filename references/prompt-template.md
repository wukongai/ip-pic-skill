# 自定义 IP 配图提示合同

派生自上游 `prompt-template.md`，由 IP Pic 的 `image_brief + template` 编译，不手写成一次性大 prompt。

## 生成前变量

- `theme`：当前认知锚点。
- `shot_type`、`structure_type`、`composition_family`。
- `core_idea`、`physical_metaphor`。
- `ip_role`、`ip_scale`、`orientation`、`action`、`visual_anchor_position`。
- `text_layout_variant`：`square-left` 或 `square-right`。
- `labels`：2–5 个短词，仅供确定性后处理。

## Raw 生图合同

```text
Generate one standalone {aspect} Chinese content illustration.

Editorial co-lead:
The authorized selected authorized character and the conceptual subject form one connected visual statement. The character is a strong brand anchor, while the object, relationship, or data module carries the content value.

Theme: {theme}
Shot type: {shot_type}
Structure type: {structure_type}
Core idea: {core_idea}
Physical metaphor: {physical_metaphor}

IP role:
Use the authorized character bible. Role={ip_role}; scale={ip_scale}; orientation={orientation}; action={action}; anchor={visual_anchor_position}.

Visual DNA:
Clean premium polished 2D editorial illustration on a pure white background. Use the approved character sheet and approved primary-style image as the identity/style reference: fine controlled ink contours, simplified mature facial planes, layered hand-painted color and restrained multi-step shading, with subtle fabric and object texture. Preserve recognizable real-person spirit without photographic skin, lens lighting or realistic hair strands. The result must remain unmistakably illustrated, but must not look like flat clip-art or a corporate vector mascot. Burgundy and deep-navy wardrobe anchors; restrained red/orange/blue information accents.

Metaphor discipline:
Use familiar subject-specific objects joined into one tangible metaphor. One orange main motion path may explain the action. Do not default to generic factory machinery, steampunk pipes/gears, floating glass UI, dashboards or module-card grids.

Constraints:
One image explains one structure. Default character height is about 34%-48%, adjusted by shot type and crop; partial body is allowed. Character and subject share a believable physical scale. Do not shrink the character into a corner sticker, make her a giant, or reduce the subject to decorative icons. For `two-step-publish`, do not generate final Chinese text, titles, logos, UI, watermarks, PPT grids or dense explanations; the publish-layout stage adds the title band later. For `direct-integrated`, allow only a small number of short, legible Chinese labels or annotations physically integrated with the IP action and concept; never generate a text wall or unrelated copy.
If text_layout_variant=square-left, keep x=110..920,y=180..1040 continuous white or very low-detail; place the character and primary metaphor mainly on the right/lower side. If square-right, keep x=1128..1938,y=180..1040 clear and place the main scene on the left/lower side. This is a real reserved overlay zone, not decorative empty space.
Edge policy: the left and right edges may be full or allow local bleed for visual energy, but the bottom 12%-15% must remain continuous, clean, low-detail negative space. Keep feet, bases, cards, arrows, ropes and key devices above the bottom margin; do not fill the bottom edge and do not draw a white 占位框.
```

## 文字后处理合同

- 默认一句粗黑观点：8–18 个汉字，最多三行，并使用红色手绘强调线。
- 场景短标签：0–4 个，每个 2–8 个汉字。
- 只有 `data-evidence` 镜头使用数据模块：最多一个主数字和两个辅助事实。
- 大字和短批注必须来自 `image_brief.content`。
- 信息证据必须能够在口播原文中逐句找到依据，禁止为了“数据感”编造数字。
- 逐字口播字幕不写入静态图片。
- 文字落点避开人物面部、关键道具、底部平台区和右侧操作区。

## 迭代顺序

1. 内容不突出：先重写人物与主题的动作关系或切换版式，不机械缩小人物。
2. 动作单一：更换 `ip_scale + orientation + action`，不重写整个风格。
3. 太像 PPT：删节点、边框和整齐网格，改成一个物理场景。
4. 太普通：更换物理隐喻、景别或动作，不只靠重复站姿增加人物存在感。
5. 中文问题：`two-step-publish` 保持 raw 不变，修改确定性 publish-layout manifest；`direct-integrated` 则重新生成一次图文融合画面。
6. 人物偏真实：移除真人照片的材质影响，以角色三视图为主参考，强化轮廓线、概括色块和赛璐璐明暗；不得靠美颜或磨皮修补。
7. 批量单调：先更换 `composition_family + crop + body_weight + action`，再调整物件；不只改变人物左右位置。
8. 角色漂移：检查授权素材清单、角色锚点和共享 handoff 是否完整，不在本业务 Skill 内补下游执行细节。
9. 核心文字缺失：`two-step-publish` 检查确定性 publish-layout 是否完成；`direct-integrated` 重新生成图文融合画面。不得把错误模式的 raw 冒充为最终图。
