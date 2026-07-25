# Extension Contracts

v0.1 支持三类扩展，但顶层 Skill 不宣称未安装扩展的能力。

## Template Pack

新增模板必须符合 `schemas/template.schema.json`，并提供唯一 `id`、独立画幅合同、layout、text policy、constraints 和 negative prompt。新画幅不能只是已有模板的裁切。

## Profile Pack

Profile pack 只能提供用户自己管理的角色 schema 和 onboarding 辅助。公开扩展不得捆绑未授权人物、客户角色或隐含默认身份。

## Renderer Adapter

Renderer adapter 接收：

- prompt 路径；
- width、height 和 canvas；
- 输出路径；
- 本次选中的参考图。

它不得要求业务 brief 携带 provider、model、API key、base URL、timeout、retry 或 fallback。凭证留在 adapter 自己的安全配置中。

## Article And Card Examples

普通文章配图扩展可以复用 content anchor 和 template pack 合同。知识卡片扩展只能展示 schema 映射接口；排版体系、内容知识库和成熟商业模板不属于本 Skill。
