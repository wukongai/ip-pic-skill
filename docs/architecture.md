# IP Pic 架构

## 设计原则

公开版采用“原版行为内核 + 公开发行适配层”，而不是重新发明一套相似工作流。

```text
自然语言与内容
  -> selection receipt / ownership
  -> content director
  -> structural template
     × character profile
     × render style profile
     × delivery mode
     × canvas
  -> prompt + director plan + render handoff + run manifest
  -> backend adapter
  -> raw/final files
  -> per-image QA
  -> retry failed items / batch receipt
```

## 模块边界

| 模块 | 职责 | 不得负责 |
|---|---|---|
| `selection.py` | 校验用户确认回执、业务类型、画布、风格和文字策略 | 静默选择默认值 |
| `director.py` | 生成认知结构、动作、表演、尺度、朝向、裁切与批次轮换 | 选择后端或读取凭证 |
| `styles.py` | 解析 6 个原版渲染风格并保证 `render-style-only` | 改变身份、scene、画布或文字策略 |
| `templates.py` | 发现并校验 13 个正式结构与兼容结构 | 用风格词切换业务结构 |
| `compiler.py` | 归一化 brief，合并正交层，编译 prompt 和 manifest | 调用图片 API |
| `references.py` | 选择 primary、多参考、reference board 或候选 handoff | 上传无授权素材 |
| `handoff.py` | 输出 provider-neutral 渲染合同 | 写 provider、model、凭证、重试或 fallback |
| `publish.py` | two-step 确定性中文文字层；保留 raw | 覆盖 raw 或伪造文字成功 |
| `batch.py` | 连续性、部分失败、失败重做、整批重建 | 把旧失败图当新参考 |
| `qa.py` | 逐图结构检查、文件检查和人工视觉验收清单 | 用文件存在替代视觉判断 |
| `backends/*` | 把同一 handoff 适配到四条公开路径 | 修改上游 director、template、prompt 或 QA |
| `parity.py` | 校验映射覆盖与双端归一化 golden | 把身份差异计为行为差异 |

## 行为内核

下列模块从私有上游共享核心提取并做最小脱敏：

- `character_performance`
- `ip_director`
- `ip_style_variants`
- `delivery_modes`
- IP 画布与布局部分
- `reference_strategy` / `reference_board`
- `render_handoff`
- `publish_layout`
- IP batch / content outline / final deliverable selection
- 视频关键帧确定性文字层

原版编译器中知识卡片、封面、海报、渠道路由、发布平台和私有运行时分支不进入公开仓。

## 模板与风格

- 结构模板保持原版字段与 prompt 语义；文件 id 允许将私人品牌前缀替换为中性 `ip-` 前缀。
- 13 个正式结构来自原版 `SKILL.md` 表；另有一个未列入表但受回归测试保护的 top-card v5 兼容结构单独登记。
- 6 个可选渲染风格保持原版语义：`minimal-lineart`、`playful-craft`、`sticker-collage`、`expressive-handdrawn`、`pop-impact`、`art-print`。
- 原版品牌 profile 与角色 style profile 不作为公开渲染风格；它们由公开角色 profile 与中性 editorial baseline 替换。

## 文字策略

### direct-integrated

- prompt 首部、中部和结尾都必须要求一次生成图文融合成品。
- 少量短标题、标签或手写说明必须与角色动作、物件和认知关系组成同一画面。
- manifest 的 `final_image` 与直接渲染结果相同。
- QA 必须包含 `integrated_text_present` 和 `integrated_text_legible`；纯插画失败并重做。

### two-step-publish

- raw prompt 必须禁止汉字、英文、数字、伪字、logo 和水印。
- 公开确定性 compositor 合成 kicker、粗黑观点、单条红线、蓝色补充和真实数据证据。
- raw 与 final 路径不同；output 已存在或指向 raw 时失败关闭。

### 视频关键帧

- raw 保持无字；确定性 `video_text_overlay` 生成 final。
- 方屏左右文字落点、竖屏观点区、字幕走廊、底部和右侧平台安全区保持原版合同。

## 后端适配

四条路径消费同一个 `image-render-handoff/v1`：

- `codex-image-tool`：宿主 Agent 调用 Codex Image Tool。
- `openai-direct`：本地 adapter 读取仓库外环境凭证并调用 OpenAI Images API。
- `host-ai-router`：宿主 Agent 调用已安装 ai-router；仓库不含其实现或配置。
- `prompt-only`：只输出 prompt、handoff 和 manifest。

Codex 与 ai-router 是 host-mediated adapter，Python CLI 只生成可验证请求和回填合同，不能伪装成已调用宿主工具。

## 状态与不覆盖

- 每次运行写入新的输出目录。
- 现有文件、符号链接、raw 图和 final 图一律不覆盖。
- batch receipt 记录每张 `planned/compiled/rendered/qa_passed/failed`。
- `retry_failed` 只消费同一次 batch receipt 的失败项。
- `full_rebuild` 新建 shot manifest，拒绝旧 raw、旧 prompt 和已否决图片。

## 验证层级

1. 静态发行与隐私门禁。
2. 单元与 contract 测试。
3. 原版/公开版归一化 golden。
4. 真实后端文件 E2E。
5. 用户人工视觉验收。

低层通过不能代表高层通过。
