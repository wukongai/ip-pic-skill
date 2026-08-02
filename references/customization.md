# IP Pic 定制与个人 fork

本页回答三个问题：

1. 用户能否换风格和字体？可以。
2. 用户能否修改已有样式？可以，但要在个人 fork 中做。
3. 用户能否新增第七种风格？可以，但修改后不再是官方固定六风格的原版等价发行物。

## 一、无需修改 Skill 的定制

以下操作是任务输入，不改变官方 Skill：

- 文章在六种内置 `style_variant_id` 中切换。
- 更换自有或已授权的 `visual.ip_profile` 和参考图。
- 修改标题、摘要、要点、画布和构图。
- 在 `direct-integrated` 与 `two-step-publish` 之间选择。
- 为 `two-step-publish` 指定有使用权的中文字体。

这是普通用户优先选择。

## 二、创建个人 fork

先退出原 Skill 目录，在其父目录执行：

```bash
cp -R ip-pic ip-pic-my-fork
cd ip-pic-my-fork
test -f SKILL.md && echo "个人 fork 已创建"
```

目标 `ip-pic-my-fork` 必须是一个不存在的新目录，避免 `cp` 合并或覆盖旧文件。

建议立即记录基线：

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

`verify_release.py` 验证的是官方发行合同。个人 fork 新增风格后，它可能按设计失败；不要删除该门禁来伪装官方通过。

## 三、修改已有文章风格

注册表在：

```text
profiles/render-styles.json
```

六个 profile 在：

```text
profiles/render-styles/
```

实际文件名是：

- `minimal-lineart-v1.json`
- `playful-craft-v1.json`
- `sticker-collage-v1.json`
- `expressive-handdrawn-v1.json`
- `pop-impact-v1.json`
- `art-print-v1.json`

不要使用不存在的 `*-style-v1.json` 文件名。

修改 profile 时必须保持：

```json
{
  "schema_version": "render-style-profile/v1",
  "id": "与注册表 entry.id 完全一致",
  "scope": "render-style-only"
}
```

风格 profile 只能写材质、线条、色彩、形状和表面语气。不得写入：

- 角色身份或 character bible
- 参考图
- 业务 scene
- canvas
- delivery mode
- provider、model、API key

验证加载：

```bash
python3 -c "from pathlib import Path; from ip_pic.styles import list_styles; print([item['id'] for item in list_styles(Path.cwd())])"
```

再对同一中性角色、同一内容重新生成六风格对照图并人工验收。修改内置 profile 后，这个个人 fork 的视觉语义已经不同于官方等价版本。

## 四、新增第七种文章风格

1. 复制一个最接近的 profile 为新文件，例如 `my-style-v1.json`。
2. 把 profile 内 `id` 改为唯一值，例如 `my-style`。
3. 保持 `schema_version` 和 `scope` 不变。
4. 在 `profiles/render-styles.json` 的 `styles` 数组新增 entry。
5. entry 的 `id` 必须与 profile `id` 一致，`profile` 必须是准确文件名。
6. 运行上面的 `list_styles` 命令。
7. 用新 `style_variant_id` 编译一个全新任务并看图。

新增第七种后，官方 `verify_release.py` 和“恰好六风格”测试应当失败。这不是运行时不能加载，而是在提醒你：它已经是个人 fork，不能冒充官方原版等价包。

## 五、修改 two-step 标题带

内置标题带：

- `extensions/title-bands/editorial-ink-v2.json`
- `extensions/title-bands/editorial-warm-v1.json`

最安全做法：

1. 复制到个人 fork 中的新文件，例如 `my-title-band-v1.json`。
2. 修改 JSON 内 `id` 为 `my-title-band-v1`。
3. 只调整 `canvas`、`colors`、`typography`、`fonts`、`font_indices`、`decoration`。
4. 在新 brief 的 `selection_receipt.publish_extension_id` 写 `my-title-band-v1`。
5. 使用全新任务 id 和输出目录完成编译、raw 渲染和合成。
6. 人工检查缺字、换行、裁切、标题区与主视觉重叠。

不要直接覆盖两个官方标题带。用户只想换本机字体时，无需 fork，使用：

```bash
python3 scripts/compose_publish_layout.py \
  --run-manifest path/to/run-manifest.json \
  --layout-manifest path/to/publish-layout-custom-font-01.json \
  --output-image path/to/publish/custom-font-01/final.png \
  --font-path "/full/path/to/ChineseFont.ttf"
```

Windows/Linux 的文章 two-step 必须显式传 `--font-path`；原版默认标题带使用 macOS 字体路径。始终为自定义字体指定新的 layout manifest 和 final，避免覆盖旧结果或回执。

## 六、修改 direct-integrated 字体样式

此模式的字是图像模型一次生成，不是本机字体渲染。任务级别不能通过字体文件精确控制。

官方 prompt 规则在 `src/ip_pic/typography.py` 和 [typography-system.md](typography-system.md)。在个人 fork 中修改它会改变原版直出视觉合同，必须：

1. 先写 prompt 合同测试。
2. 再修改规则。
3. 对六种风格做真实生成对照。
4. 检查文字可读、只保留一条强调线、没有楷体/儿童体/细字重漂移。

## 七、修改视频风格或字体

文章 style registry 不控制视频。视频使用正式模板：

- `ip-editorial-video-square-v1`
- `ip-minimal-lineart-video-square-v1`
- `ip-playful-craft-video-square-v1`
- `ip-sticker-collage-video-square-v1`
- `ip-expressive-handdrawn-video-square-v1`
- `ip-pop-impact-video-square-v1`
- `ip-art-print-video-square-v1`
- 以及竖屏和字幕安全结构。

只换字体时，在编译输出的 `video-text-overlay.json` 顶层写 `font_path`，1:1 方屏标题可另写 `headline_font_path`。这不修改模板。

Windows 必须显式配置；Linux 只有脚本列出的 Noto CJK 路径存在时才会自动回退。已有视频 final 时复制 overlay，把顶层 `output_dir` 改到新目录并保留 `items[].output_file` 文件名；不要添加不存在的 `output` 或 `result_receipt` 字段。

新增视频视觉结构或文字 recipe 需要个人 fork、模板测试和真实安全区回归；它不是在文章 registry 增加一行就能完成的。

## 八、回退

任务级输入出错：

- 保留旧输出。
- 修正 brief。
- 使用新 id 和新输出目录重新编译。

个人 fork 改坏：

- 回到修改前的备份目录，或用版本控制恢复明确的单个文件。
- 不运行会清空整个工作区的破坏性重置。
- 恢复后重新运行全部测试和发行检查。

如果不确定改动是否越过官方等价边界，最安全的判断是：只要改了 `templates/`、`profiles/render-styles/`、`extensions/` 或 `src/ip_pic/typography.py`，就把产物标记为个人 fork，并重新做真实视觉回归。
