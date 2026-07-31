# IP 配图风格变体

`ip-illustration-factory` 是业务结构，不等于一种固定画风。人物身份、认知动作、构图轮换、文字安全区和确定性叠字属于稳定层；编辑卡通、毛毡手作、贴纸拼贴或丑萌怪趣属于可切换的风格层。

## 分层

1. **身份层**：`visual.ip_profile` 与角色身份 profile，回答“是谁”，跨风格保持稳定。
2. **文字策略层**：`delivery_mode`，回答“少量短字是否与画面一次生成”。
3. **画布层**：16:9、1:1、3:4、9:16 或自定义宽高，回答“成品是什么比例”。
4. **渲染风格层**：线条、材质、形状、幽默语气和色彩，回答“看起来像什么”。

新风格不新建全局 skill、business_id 或画幅模板。它通过独立 `render-style-only` profile 记录风格事实，并叠加到当前场景的结构基底模板。旧 `*-video-square-*` 模板保留用于历史样图和专项回归，但不再充当自然语言风格选择器。

## 当前可选风格

| style_variant_id | render style profile | 定位 | 状态 |
|---|---|---|---|
| `minimal-lineart` | `minimal-lineart-style-v1` | 纯白底、极简黑线、低科技怪物件与少量强调色 | production · 个人推荐 |
| `playful-craft` | `playful-craft-style-v1` | 毛毡为主、贴纸轮廓为辅、一本正经地胡闹 | experimental |
| `sticker-collage` | `sticker-collage-style-v1` | 手撕纸、贴画拼贴、印刷网点与错位套色 | experimental |
| `expressive-handdrawn` | `expressive-handdrawn-style-v1` | 墨线、马克笔、蜡笔和松弛草稿痕迹 | experimental |
| `pop-impact` | `pop-impact-style-v1` | 高饱和撞色、粗轮廓与第一秒视觉爆点 | experimental |
| `art-print` | `art-print-style-v1` | 木刻、单版画、水粉色域与艺术书构成 | experimental |

六个风格是同级可选项。用户已指定 `minimal-lineart` 为个人推荐；只有用户说“按默认/沿用推荐”时才采用，不把模板 JSON 的 `default_for_scene` 当作用户确认。六种 profile 均不得携带 scene、aspect、size、delivery_mode 或 layout 选择，因此同一个 16:9 短字正文结构可以独立切换毛毡、拼贴等视觉表面。

## 变体边界

- 风格可以改变人物的材质、表情强度和形状语言，但不能改变身份锚点。
- “贴纸风”不等于把人物缩成角落贴纸；角色仍需执行核心认知动作。
- “丑萌”允许不对称、笨拙和表情反差，不允许幼态化、恶意丑化或身体羞辱。
- 一张只使用一个主笑点；幽默必须帮助观众理解主题。
- 新风格先以 `experimental` 加入，经过样图和跨镜头一致性验收后再升为 `production`。
