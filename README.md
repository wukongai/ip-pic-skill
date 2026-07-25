# Custom IP Illustration Skill

[简体中文](README.md) | [English](README.en.md)

把你拥有或获授权的固定人物角色，用于文章、脚本和关键帧配图。Skill 负责内容拆解、角色动作、镜头构图、prompt、参考素材选择和 QA；真实图片生成使用当前 Agent 已经拥有的图片工具。

![虚构示例人物 Mira](examples/demo-character.svg)

> 图中的 Mira 是本仓库原创的虚构教程人物，只用于演示安装和工作流。她不会被自动设为你的角色，也不包含作者本人、私人品牌或私有知识库特征。

## 它能做什么

- 用同一角色生成 16:9、1:1、9:16 三种独立构图。
- 把文章或脚本拆成角色动作、物理隐喻和逐图 prompt。
- 优先保持人物外观、服装、道具和性格一致。
- 自动使用宿主 Agent 已有的图片工具；没有图片工具时交付完整 prompt 和 render request。
- 不要求普通用户配置 Router、provider、模型、服务地址或 API 凭证。
- 所有运行产物写入用户项目，不污染 Skill 安装目录。

## 1 分钟安装

需要 Node.js（安装）和 Python 3.10+（编译），以及一个支持 Skills 的 Agent。运行：

```bash
npx skills add wukongai/custom-ip-illustration-skill
```

安装器会让你选择目标 Agent，以及安装到当前项目还是全局环境。

Codex 非交互安装示例：

```bash
cd <你的目标项目目录>
npx skills add wukongai/custom-ip-illustration-skill \
  --skill custom-ip-illustration \
  -a codex \
  -y
```

非交互安装前请先进入目标项目目录；否则安装器可能选择全局范围。拿不准时使用上面的交互式命令。

安装 Skill 不等于购买或配置图片 API。如果当前 Agent 自带图片生成能力，Skill 会自动使用；如果没有，就进入 `compile_only`，仍然生成可复制使用的 prompt。不要把 API 凭证写进本仓库或角色资料。

## 第一次使用：先跑虚构人物教程

安装后直接对 Agent 说：

```text
用 custom-ip-illustration 的虚构人物示例，为示例文章编译 2 张 16:9 配图。
先不要真正生图，只生成 prompt 和 render request。
```

Agent 会明确告诉你它正在使用教程人物 Mira，然后读取：

- `examples/ip-profile.example.json`：人物设定；
- `examples/brief.example.json`：示例文章；
- `examples/demo-character.svg`：仅供人类预览的人物示意图。

开发者从 GitHub 克隆源码后，也可以在源码仓库根目录手动验证编译器。标准安装用户只需对 Agent 说上面的教程指令，Agent 会自行定位已安装 Skill 的脚本：

```bash
python3 scripts/compile_ip_illustration.py \
  --profile examples/ip-profile.example.json \
  --brief examples/brief.example.json \
  --output-dir /tmp/custom-ip-demo
```

成功后会得到：

```text
/tmp/custom-ip-demo/
├── prompts/
│   ├── 01-*.md
│   └── 02-*.md
├── render-request.json
└── run-manifest.json
```

## 使用你自己的 IP

第一次没有角色资料时，可以直接说：

```text
用 custom-ip-illustration 帮我创建自己的 IP 角色资料，然后给这篇文章做 3 张横版配图。
请一次只问我一个问题，保存前先给我确认。
```

Skill 会按以下顺序引导，不要求你手写 JSON：

1. 确认角色是你拥有、获授权或有许可证使用的；
2. 收集人物名称和一句身份描述；
3. 收集外观、签名特征、性格和不可漂移的连续性锚点；
4. 可选登记本次允许使用的参考图；
5. 展示角色资料摘要；
6. 得到你确认后，保存到项目的 `.custom-ip-illustration/ip-profile.json`；
7. 询问图片数量、画幅和是否真正生图，然后开始编译。

以后在同一项目中说“用我的 IP 给这篇文章配图”，Agent 会优先读取该项目资料。修改或覆盖角色资料前仍需再次确认。

角色资料是明文 JSON，可能包含外观描述、授权依据和本地参考图路径。若项目会同步到 Git 或云盘，请先确认这些信息可以同步；不希望提交时，可把 `.custom-ip-illustration/` 加入项目的 `.gitignore`。

## 图片后端怎么配置

多数用户不需要在这个 Skill 里配置任何接口：

- 宿主 Agent 有原生图片工具：自动使用；
- 只有一个兼容的第三方图片工具：自动使用；
- 有多个第三方图片工具：Agent 只询问你选哪一个；
- 没有图片工具：交付 prompt 和 manifest，不伪造图片结果。

高级用户可以连接自己的图片 MCP 或 backend，但连接方式、凭证和模型路由由该后端管理，不属于本 Skill。详见 [后端选择规则](references/backend-selection.md)。

## 可选偏好

将 `EXTEND.example.md` 复制到以下任一位置：

1. 项目：`.custom-ip-illustration/EXTEND.md`
2. XDG：`${XDG_CONFIG_HOME}/custom-ip-illustration/EXTEND.md`
3. 用户：`${HOME}/.custom-ip-illustration/EXTEND.md`

第一份存在的文件生效。偏好只允许保存风格、画幅、输出目录、批量数、语言和 backend id，不允许保存凭证或服务地址。

## 常见问题

**为什么只生成了 prompt，没有图片？**  
当前 Agent 没有可用图片工具，或你要求了“只规划 / 不生图”。这是正常的 `compile_only` 结果。

**为什么首次使用会问角色权利来源？**  
Skill 只处理用户自有、获授权或有明确许可证的角色，不会帮助复刻未经授权的受保护角色。

**虚构人物 Mira 会进入我的正式结果吗？**  
不会。只有你明确要求运行示例时才会使用她；正式任务缺少角色资料时，Skill 会先引导创建你的资料。

**Mira 的示例素材可以复用吗？**  
可以。Mira 及示例 SVG 是仓库贡献者为教程原创的素材，随本仓库明确授权使用，范围见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。

**需要配置特定 Router 吗？**  
不需要。Skill 只识别宿主当前提供的图片工具，不依赖某个特定路由方案。

## 开发与验证

开发者如果要阅读源码、修改模板或贡献代码：

```bash
git clone https://github.com/wukongai/custom-ip-illustration-skill.git
cd custom-ip-illustration-skill
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_release.py --root . --manifest public-release-manifest.json
```

本项目运行时仅依赖 Python 标准库。

## 更新与卸载

- 更新：重新运行安装命令，或按你的 Skill 管理器更新仓库版本。
- 卸载：通过 Skill 管理器移除 `custom-ip-illustration`；手工安装时删除对应 Skill 目录。
- 用户项目中的角色资料和生成图片不属于 Skill 安装目录，卸载不会自动删除它们。

安全问题见 [SECURITY.md](SECURITY.md)，贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。
