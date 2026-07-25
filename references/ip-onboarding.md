# IP Onboarding

首次使用只收集影响身份一致性和授权的字段。一次问一个关键问题，不要求用户理解 schema。

## 必填

1. `ownership.status`
   - `user_owned`：用户本人创作并拥有。
   - `licensed`：通过许可证获得使用权。
   - `authorized`：权利人明确授权。
2. `ownership.basis`：一句话说明权利来源，不需要上传合同。
3. `identity`：角色名称和一句身份描述。
4. `appearance`：整体外观和至少一个签名特征。
5. `personality.traits`：影响动作和表情的性格词。
6. `continuity_anchors`：跨图不可漂移的轮廓、配色、服装或道具。

## 参考图

- 只登记用户允许本次工作使用的图片。
- 每张写明 `purpose` 和 `authorized: true`。
- 授权素材库存不等于每张图都要使用；编译器只挑选身份、外观和风格所需素材。
- 参考路径只进入 render request，不进入 prompt 正文。

## 停止

- 用户不知道角色权利来源。
- 用户明确要求模仿一个不属于自己的受保护角色。
- 身份一致性依赖的参考图不可访问。
