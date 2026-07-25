# Custom IP Illustration Skill

把你自己的固定角色用于文章、脚本和关键帧配图。Skill 负责内容拆解、角色动作、镜头构图、prompt、参考素材选择和 QA；真实图片生成使用当前 Agent 已经拥有的图片工具。

## 特点

- 不内置作者角色或品牌资产。
- 默认 `backend: auto`，普通用户无需理解 Router、provider 或模型参数。
- 没有图片后端时仍会交付完整 prompt 和 render request，并明确标记 `compile_only`。
- 支持 16:9、1:1、9:16 三套独立构图，不做机械裁切。
- API key 和其他凭证始终由图片后端管理，不进入 Skill。
- 所有产物写入用户项目，不污染 Skill 安装目录。

## 安装

普通用户推荐使用标准 Skills 安装器：

```bash
npx skills add wukongai/custom-ip-illustration-skill
```

安装器会让你选择目标 Agent 和项目级或全局范围。需要非交互安装时，可使用：

```bash
npx skills add wukongai/custom-ip-illustration-skill \
  --skill custom-ip-illustration \
  -a codex \
  -y
```

安装 Skill 不等于安装图片 API；如果宿主没有图片工具，Skill 会自动使用 compile-only 模式。

开发者如果要阅读源码、修改模板或贡献代码，再克隆仓库：

```bash
git clone https://github.com/wukongai/custom-ip-illustration-skill.git
cd custom-ip-illustration-skill
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 最短使用路径

1. 准备自己的角色说明和可选参考图。
2. 告诉 Agent：“用我的 IP 给这篇文章做 3 张 16:9 配图。”
3. 首次使用时确认角色 ownership、外观锚点、性格和禁止变化项。
4. Skill 先保存 prompt，再自动选择当前可用的图片工具。

示例：

```bash
python3 scripts/compile_ip_illustration.py \
  --profile examples/ip-profile.example.json \
  --brief examples/brief.example.json \
  --output-dir /tmp/custom-ip-demo
```

## 可选偏好

复制 `EXTEND.example.md` 到以下任一位置：

1. 项目：`.custom-ip-illustration/EXTEND.md`
2. XDG：`${XDG_CONFIG_HOME}/custom-ip-illustration/EXTEND.md`
3. 用户：`${HOME}/.custom-ip-illustration/EXTEND.md`

第一份存在的文件生效。偏好只允许保存风格、画幅、输出目录、批量数、语言和 backend id，不允许保存凭证或服务地址。

## 后端行为

- 有宿主原生图片工具：直接使用。
- 只有一个兼容第三方图片工具：直接使用。
- 有多个第三方图片工具：询问一次。
- 没有图片工具：交付 prompt 和 manifest，不伪造图片结果。

高级用户可以接入自己的图片 MCP 或 backend，但连接方式、凭证和模型路由由该后端自己管理。

## 开发与验证

本项目仅依赖 Python 标准库：

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_release.py --root . --manifest public-release-manifest.json
```

## 更新与卸载

- 更新：重新运行安装命令，或按你的 Skill 管理器更新仓库版本。
- 卸载：通过 Skill 管理器移除 `custom-ip-illustration`；手工安装时删除对应 Skill 目录。
- 用户项目中的角色资料和生成图片不属于 Skill 安装目录，卸载不会自动删除它们。

## 安全与贡献

安全问题见 [SECURITY.md](SECURITY.md)，贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。
