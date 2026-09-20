# AIMAN World Protocol

> 面向机器和 Agent 的开放数据与协作协议。

- Version: `world-protocol/0.1`
- Status: Draft
- Transport: REST/HTTP、MCP、CLI 或其他受控 Adapter 均可承载
- Encoding: UTF-8 JSON；时间使用 RFC 3339

本文件定义跨传输的最小语义。现有接口可以保留历史响应形状；新接口和适配器应使用本协议的 `recordType`、`schemaVersion`、身份、证据、时间和状态语义。

当前仓库中，[`protocol/README.md`](protocol/README.md) 与 `protocol/schemas/` 定义 **v0.3 可执行 Contribution Protocol**；本文件定义更上层的跨传输语义和演进方向。两者冲突时，当前可执行 Schema 决定“现在能提交什么”，本文件决定“语义为什么这样设计、未来扩展必须保持哪些不变量”。

## 1. 设计目标

协议必须让陌生 Agent 能够回答：

1. 这是哪个 World、哪个 canonical entity 或哪个 Event？
2. 这条主张来自什么 Evidence，Evidence 支持的具体范围是什么？
3. 事件何时发生，状态何时有效，什么时候被观察或采集？
4. 这是 accepted fact、主体声明、意见、pending、conflict 还是 unknown？
5. 当前请求可以读什么、提出什么、写什么，读回应检查什么？

协议不把 Agent 的自然语言输出当作 canonical record，也不把 transport 成功当作事实成功。

## 2. 通用约定

### 2.1 标识与时间

- `id`、`eventKey`、`requestId`、`evidenceRefs` 是不透明标识；客户端不得从字符串格式推断业务含义。
- `eventKey` 用于事件幂等；同一个现实 Event 的重试应复用同一个稳定 key。
- `occurredFrom` / `occurredTo` 表示事件发生区间。
- `validFrom` / `validTo` 表示断言或状态有效区间。
- `observedAt` 表示观察发生时间；`capturedAt` 表示来源被采集时间。
- `createdAt` 表示系统记录时间，不能冒充事件时间。
- 不确定的时间返回 `null`，不能用响应排序、文章发布日期或当前时间猜测。

### 2.2 通用记录

所有新版本记录 SHOULD 至少包含：

```json
{
  "recordType": "world-event",
  "schemaVersion": "world-event/1",
  "id": "opaque-id",
  "knowledgeStatus": "accepted_fact",
  "evidenceRefs": [],
  "warnings": []
}
```

`schemaVersion` 是记录契约版本，不是服务部署版本。`warnings` 用于显式报告未知、冲突、投影降级和 provenance gap。

### 2.3 引用

实体、事件、关系、状态和文章之间应优先传稳定引用：

```json
{
  "id": "robot:opaque-id",
  "entityType": "robot",
  "canonicalName": "可选的当前展示名"
}
```

`canonicalName` 方便阅读但不是主键。名称匹配有歧义时，响应 MUST 返回 `identity_ambiguous` 或候选列表，不能静默选择一个。

## 3. 发现与能力协商

### 3.1 Repository-first

陌生 Agent 在本仓库中的最小发现顺序：

```text
README.md
  → AGENTS.md
  → WORLD.md
  → WORLD-PROTOCOL.md
  → WORLD-AGENT.md
  → protocol/README.md
  → packs/<name>/domain.yaml
```

其中：

- `WORLD.md` 定义 World Model 的核心不变量。
- `WORLD-PROTOCOL.md` 定义跨传输语义。
- `WORLD-AGENT.md` 定义 Agent 如何观察、建模、提交和读回。
- `protocol/README.md` 与 JSON Schema 定义当前真正可执行的公共贡献格式。
- `packs/<name>/domain.yaml` 定义当前领域允许的 entity type、claim predicate、relation triple 和 event type。

### 3.2 Deployed runtime

连接运行中的节点时，Agent SHOULD 先读取：

```text
GET /api/v1/meta
  → GET /api/v1/capabilities
  → GET /api/v1/packs/{pack}
  → read endpoints
  → proposal endpoint only when capability + authorization allow it
```

能力声明必须是真实可调用能力的集合。没有被 runtime 广告或没有权限的能力不得由 Agent 猜测存在。

MCP、well-known manifests、CLI 或其他 Adapter 可以承载本协议，但 v0.1 不要求每个 deployment 都实现这些 transport。一个 Adapter 的存在不能创造第二套知识模型。

## 4. 贡献与观察载荷

当前开源仓库的可执行公共 intake 是 **World Model Contribution Protocol v0.3**。最小 packet 形状为：

```json
{
  "protocol_version": "0.3.0",
  "contribution_id": "contrib:stable-id",
  "pack": "robotics",
  "created_at": "2026-09-20T00:00:00Z",
  "contributor": {
    "id": "agent:example",
    "type": "agent"
  },
  "idempotency_key": "stable-retry-key",
  "summary": "What changed in the world",
  "entities": [],
  "claims": [],
  "relations": [],
  "events": [],
  "evidence": []
}
```

具体字段以 `protocol/schemas/contribution.schema.json` 为准。语义不变量是：

- Entity 建议身份，不自动证明任意属性。
- Claim、Relation 和 Event 必须引用 Evidence。
- incoming factual status MUST 是 `proposed`。
- `pack` 必须声明所有 entity type、claim predicate、relation triple 与 event type。
- `contribution_id` 和 `idempotency_key` 必须稳定，重试不能制造第二个现实事实。
- CI 通过只代表结构与 ontology 合法，不代表事实已经 verified。
- 第一方来源也不能绕过 conflict check、identity resolution 与 review。

部署中的 proposal API 是另一种 intake transport，但遵守同一边界：**proposal is not canonical truth**。

## 5. 读取协议

公开读响应应尽可能返回可组合、可追溯的 records，而不是只返回不可解释的页面文本。客户端必须保留 canonical identity、时间、status 和 Evidence 语义。

当前 runtime 的主要入口包括：

| 语义 | 当前入口 | 说明 |
| --- | --- | --- |
| Meta / capability | `/api/v1/meta`、`/api/v1/capabilities` | 先发现真实部署能力 |
| Domain pack | `/api/v1/packs/{pack}` | 当前可执行领域词汇 |
| Entity | `/api/v1/entities`、`/api/v1/entities/{id}` | canonical identity/read model |
| Relation | `/api/v1/relations` | typed relation read model |
| Event | `/api/v1/events`、`/api/v1/timeline` | event 与时间投影 |
| Graph | `/api/v1/graph` | relation/event 的图投影 |
| Proposal | `/api/v1/proposals` 或兼容 ingest route | 受 capability/authorization 控制的候选入口 |
| Review | `/api/v1/review-tasks` | 审核状态，不是贡献者自授真值 |

具体路由能力以 `/api/v1/capabilities` 和当前实现为准；文档中出现的目标接口不能覆盖 runtime 的真实 capability。

## 6. Transport 映射

REST/HTTP 是当前参考 runtime 的主要 transport。MCP、CLI、Git Pull Request 或其他 Adapter MAY 映射相同语义，但必须遵守以下规则：

- transport 只能承载 World Model 语义，不能创造另一套 canonical identity。
- 参数和结果 SHOULD 保留 stable identity、Evidence、时间与 review status。
- 没有 canonical write 权限时，“提交 proposal”不得显示为“修改事实”。
- transport 内部错误不能通过空结果伪装成“没有事实”。
- Git-native contribution、deployed proposal API 与未来 MCP/CLI 都必须收敛到同一个 review/materialization 边界。

## 7. 错误码与可恢复性

错误响应 SHOULD 具有稳定结构：

```json
{
  "error": {
    "code": "identity_ambiguous",
    "message": "无法唯一确定 canonical entity",
    "retryable": false,
    "details": {"candidates": []}
  },
  "requestId": "request-id"
}
```

最小错误码：

| code | 含义 | Agent 行为 |
| --- | --- | --- |
| `invalid_request` | 参数或 schema 不合法 | 修正后重试 |
| `not_found` | 该范围内不存在记录 | 不凭空创建 |
| `identity_ambiguous` | 身份匹配不唯一 | 保持 pending，补证据 |
| `evidence_missing` | 主张没有充分 Evidence | 不升级为事实 |
| `unauthorized` / `forbidden_scope` | 缺少身份或范围权限 | 停止，不绕过认证 |
| `unsupported` | 当前能力未开放 | 读取 capability，换只读路径 |
| `conflict` | 证据或状态冲突 | 保留冲突并请求复核 |
| `rate_limited` | 请求频率受限 | 按提示退避，避免重复写入 |
| `internal_error` | 服务端未完成请求 | 先确认 readback，再决定是否重试 |

`internal_error`、超时和 HTTP 200 都不能被解释为已写入或已发布。

## 8. 幂等、审核与读回

任何可能触发外部写入或产生候选记录的请求 SHOULD 带 `requestId`；事件候选 MUST 带稳定 `eventKey`。重试前先查询 receipt、稳定 ID 或审核状态。

受控写入的最低闭环为：

```text
authorize → validate → write/propose → return stable id
→ readback → evidence/identity/relation check → project
```

服务不得以客户端传入的 `status=approved`、`confidence=1` 或 `canonical=true` 直接授予事实状态。审核状态由控制平面产生。

## 9. 安全与权限边界

- 公开读、账户贡献、公司 Agent 和生产运维是不同权限域。
- Agent 只能调用 capability endpoint 或 deployment contract 宣布且当前身份获准的能力。
- 不提供数据库、密钥、任意 Shell 或绕过业务路由的写入方式。
- 贡献中的商业意图、主体声明、意见和客观事实必须分开。
- 生产系统中，代码版本、迁移完成、服务存活和 HTTP 200 都不能单独证明业务完成；需要实际路径与读回证据。

## 10. 兼容与扩展

扩展只允许 additive：新字段、新记录类型和新能力必须不破坏旧消费者。客户端应忽略未知字段；服务端应保留旧 ID 和已有语义。

以下变化需要新的 major 版本或明确迁移：删除字段、改变字段类型、改变 ID 指向、把 `null` 改成“无”、把 pending 改成 accepted、把主体声明改成事实、把只读能力改成写能力。

本协议不冻结完整行业 ontology。只有真实冲突、查询需求或跨系统互操作证明需要时，才增加枚举和约束。
