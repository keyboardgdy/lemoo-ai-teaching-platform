# APPROVAL-MATRIX-001：高风险操作审批矩阵

> 版本：1.0.0
>
> 状态：Approved — Stage 1A Engineering Boundary
>
> 日期：2026 年 8 月 13 日
>
> 安全/隐私 Owner：高端阳（2026 年 8 月 13 日批准）
>
> 批准记录：https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5#issuecomment-5278502909
>
> GitHub Work Item：[#5](https://github.com/keyboardgdy/lemoo-ai-teaching-platform/issues/5)

本文定义动作风险、重新认证、职责分离和审计要求。当前阶段 1A 只有一名自然人 A；凡要求两名不同自然人的动作均保持不可达，不能用 OpenAI Codex 充当第二批准人。

## 一、风险等级

| 等级 | 定义 | 默认控制 |
|---|---|---|
| R0 | 公开或合成数据只读，无控制副作用 | 登录与普通审计 |
| R1 | 单租户、单模拟设备、可逆低风险变更 | 服务端授权、Reason、审计、幂等 |
| R2 | 敏感数据、凭据、跨机构支持或影响多个资源 | 重新认证、影响预览、独立批准、短期授权 |
| R3 | 生产、真实设备动作、批量控制、发布/签名、跨境或不可逆操作 | 两名不同自然人、职责分离、维护窗口、回退和不可变证据 |

## 二、审批矩阵

| Action ID | 动作 | 等级 | 请求者 | 批准者 | 强制条件 | 当前状态 |
|---|---|---:|---|---|---|---|
| APR-001 | 查看本机构合成设备状态 | R0 | 授权运维 | 无额外批准 | RBAC、机构过滤、访问审计 | Stage 1A allowed |
| APR-002 | 单模拟设备 `refresh_shadow` | R1 | 设备运维 | 无额外批准 | Reason、幂等、Expiry、设备状态、完整审计 | Stage 1A candidate |
| APR-003 | 平台管理员跨机构支持查询 | R2 | 平台管理员 | 预授权支持策略；事后复核人 | 重新认证、工单/Reason、字段最小化、短 TTL | Design only |
| APR-004 | 设备机构转移/解绑 | R2 | 设备运维 | 原机构与目标机构有权人 | 所有权证据、影响预览、凭据轮换、审计 | Real device blocked |
| APR-005 | 证书吊销/重新签发 | R2 | 设备/安全运维 | 不同安全批准人 | 重新认证、原因、目标精确、回退/恢复 | Real device blocked |
| APR-006 | 诊断包采集或下载 | R2 | 设备运维 | 安全/隐私批准人 | 字段/时间窗、脱敏、短期 URL、到期删除 | Disabled |
| APR-007 | 个人数据导出、更正或删除 | R2 | 隐私运营 | 数据主体请求复核人 | 身份核验、范围预览、法定留存例外、完成证据 | Real data blocked |
| APR-008 | 启用真实 AI Provider/区域/模型 | R3 | AI/产品 Owner | 安全/隐私 + 法务/合同有权人 | ADR、DPA、子处理者、区域、Eval、预算、回退 | Disabled |
| APR-009 | 发布 Prompt/互动脚本 | R2 | AI/教研 | 不同内容/安全审核人 | 版本、Eval、适龄/注入测试、回滚 | Disabled |
| APR-010 | 发布题目或内容包 | R2 | 教研 | 不同权利/内容审核人 | Rights Record、人工审核、签名、撤回方案 | Disabled |
| APR-011 | 批量/高风险设备命令 | R3 | 设备运维 | 设备 + 安全两名不同自然人 | 精确目标、Canary、窗口、自动停止、回退 | Disabled |
| APR-012 | OTA 构建/签名/发布/回滚 | R3 | 分离角色 | 至少两名不同自然人且签名角色分离 | 阈值、离线/HSM、Counter、Canary、HIL | Disabled |
| APR-013 | 生产部署或生产 Secret 变更 | R3 | 发布/运维 | 技术 + 安全/发布批准人 | 制品 Digest、变更单、回退、窗口、监控 | Production blocked |
| APR-014 | 数据跨区域/跨境或新增子处理者 | R3 | 隐私/产品 | 法务/隐私有权人 | 适用性评估、合同机制、告知/同意、影响评估 | Blocked |

## 三、不可替代规则

1. 请求者、批准者、执行者在 R3 中不得由同一自然人完成全链。
2. Codex、CI、模型、机器人或服务账号都不是自然人批准者。
3. 批准必须绑定不可变 Action、目标集合、参数摘要、过期时间和 Commit/Artifact Digest。
4. 修改目标、扩大范围、延长窗口或改变数据用途会使原批准失效。
5. UI 按钮禁用不算控制；API、Worker、消息入口和直接数据路径必须共同拒绝。
6. 审计不可写、授权事实不确定或重新认证失败时，动作不得排队后补。

## 四、审计最小字段

`approval_id`、Action ID、请求者/批准者/执行者、组织、Reason、工单、目标与参数摘要、前后状态、风险等级、策略版本、重新认证时间、请求/批准/执行/结束时间、Commit/Artifact Digest、结果、失败分类、回退结果、`request_id`、`trace_id`。

任何未来 R2/R3 动作在没有独立自然人批准能力时保持 `disabled`。
