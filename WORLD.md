# AIMAN World Model

> Reality-First World Modeling：让机器维护一个有身份、有证据、有历史、可计算、可追溯的现实世界模型。

- Version: `world/0.1`
- Status: Draft open specification
- Scope: AIMAN.World 的机器人产业 World Model；可扩展到其他行业
- Updated: 2026-09-20

本文是总规范。机器接口契约见 [`WORLD-PROTOCOL.md`](WORLD-PROTOCOL.md)，Agent 的工作边界见 [`WORLD-AGENT.md`](WORLD-AGENT.md)。

规范中的 `MUST`、`SHOULD`、`MAY` 分别表示必须、应当和可以。本文描述目标语义与兼容边界，不把尚未上线的能力写成当前实现。

## 1. World 是什么

World 不是数据库、网站或文章集合。它是对现实持续观察后形成的、可被人和机器读取的状态与历史模型。

```text
Reality
  → Observation
  → Evidence
  → Event
  → Canonical Entity
  → Relation / State
  → Graph / Timeline / Profile
  → Article（可选的人类叙事投影）
```

在机器人产业域，`Company`、`Robot`、`Part` 是常用的 canonical entity 类型；`Graph` 是关系视图，`Timeline` 是事件与状态变化视图，`Article` 是解释层。它们不得各自维护一套事实。

核心路径可以压缩为：

```text
Reality → Evidence → Event → Entity → Relation → Robot/Company/Part
        → Graph/Timeline → Article
```

文章可以没有，事件不能因为没有文章而不存在；实体、关系和状态也不能因为页面尚未展示而失去其事实语义。

## 2. 不可破坏的不变量

### 2.1 Reality First

先观察真实世界，再让模型吸收重复出现的结构。Schema 不得迫使未经证据支持的现实变成确定值。

### 2.2 Evidence First

重要主张必须能回到具体 Evidence，而不是只回到一个来源首页或 Agent 的判断。来源是证据容器，不自动证明页面中的所有解释。

```text
Claim → Evidence → Source → observedAt / validPeriod
```

来源优先级通常为：官方产品页或公告、监管/公共记录、论文或官方仓库、合作双方公告、权威二手来源。来源等级不能替代对具体主张的直接支持。

### 2.3 Canonical Identity First

写入事实前，MUST 先确认对象是否已经存在，并处理 canonical name、alias、品牌、公司、产品、型号和 Variant 的边界。别名不是新实体；字符串相似、文章共现和模型猜测不能单独确认身份。

### 2.4 Event First，Article Second

发布、融资、量产、交付、部署、升级、停产、合作、收购、价格变化和路线转折首先是 Event。Article 解释一个或多个 Event，不替代 Event，也不成为唯一事实来源。

### 2.5 Relation 是一等对象

关系必须有方向、谓词、对象身份、时间条件、Evidence 和审核状态。`Robot` 与 `Company` 同篇出现，不自动产生 `manufactured_by`、`customer_of` 或任何其他产业关系；事件先后也不自动等于因果。

### 2.6 Unknown > Guess

无法证实时保留 `null`、`unknown`、`pending` 或 `conflict`。缺失的事实不能用占位值、默认值、模型置信度或文章发布日期补齐。

在机器 JSON 中：

| 表达 | 语义 |
| --- | --- |
| `null` | 该字段属于此投影，但当前未知或无法确定 |
| 字段省略 | 此投影没有承诺提供该字段 |
| `[]` | 已知没有项目，或该集合在当前范围内为空 |
| `pending` | 候选材料已收取，但尚未成为 canonical 事实 |
| `conflict` | 存在未解决的证据或状态冲突 |

`null`、空集合、未知状态和查询不到记录不能互相替换。

### 2.7 历史只能演化，不能静默覆盖

事实修订应保留原始来源、观察时间、有效期、修订原因和冲突关系。新 Event、Follow-up、Enrichment、Supersedes 和 Withdrawal 都是历史演化，不得把旧记录无痕改成新事实。

### 2.8 Agent 不拥有最终裁决权

Agent 可以发现、读取、整理、提出候选和执行明确授权的动作；控制平面负责身份、权限、审核、审计、写入和读回。模型输出、HTTP 200、写入返回成功或一条 pending receipt，都不能单独证明 canonical 或生产事实已经成立。

## 3. 核心对象

### 3.1 Source、Evidence 与 Claim

- `Source`：承载公开信息的 URI、文档、记录或受控观察来源。
- `Evidence`：从 Source 中定位出的摘录、表格、字段、观察结果或可重复事实，用于支持一个具体 Claim。
- `Claim`：对实体、关系、事件或状态的可判断陈述；必须标注其是事实、主体声明、意见还是尚待审核的候选。

Evidence 最小应能表达：

```json
{
  "id": "evidence:opaque-id",
  "source": {"uri": "https://example.com/source", "publisher": "Example"},
  "quote": "原文中直接支持主张的片段",
  "locator": "section-or-page-or-json-path",
  "capturedAt": "2026-09-20T00:00:00Z",
  "evidenceKind": "official_primary",
  "assertionKind": "accepted_fact"
}
```

若没有可复核的原始位置，应明确记录 provenance gap；不得伪造 Quote、Locator 或 URL。

### 3.2 Canonical Entity

```json
{
  "recordType": "world-entity",
  "schemaVersion": "world-entity/1",
  "id": "robot:opaque-id",
  "entityType": "robot",
  "canonicalName": "Canonical name",
  "aliases": ["observed name"],
  "status": "active",
  "evidenceRefs": ["evidence:opaque-id"]
}
```

`id` 是稳定引用；展示名称可变。现阶段实现可以复用项目已有的 `entity_type + canonical_name` 身份约定，但不得因为开放规范而凭愿景新建第二套 canonical entity 主表。

### 3.3 Event

Event 表示改变产业或实体状态的历史事实：

```json
{
  "recordType": "world-event",
  "schemaVersion": "world-event/1",
  "id": "event:opaque-id",
  "eventKey": "stable-idempotency-key",
  "eventType": "product_release",
  "title": "事件标题",
  "occurredFrom": "2026-09-20T00:00:00Z",
  "occurredTo": null,
  "entityRefs": [{"id": "company:opaque-id", "role": "subject"}],
  "evidenceRefs": ["evidence:opaque-id"],
  "knowledgeStatus": "accepted_fact",
  "stateChanges": []
}
```

事件发生时间、来源发布时间、Evidence 采集时间和记录创建时间必须分开。无法确定发生时间时保留未知，不能用文章发布日期代替。

### 3.4 Relation

```json
{
  "recordType": "world-relation",
  "schemaVersion": "world-relation/1",
  "id": "relation:opaque-id",
  "subject": {"id": "robot:opaque-id", "entityType": "robot"},
  "predicate": "uses",
  "object": {"id": "part:opaque-id", "entityType": "part"},
  "validFrom": null,
  "validTo": null,
  "evidenceRefs": ["evidence:opaque-id"],
  "knowledgeStatus": "pending"
}
```

谓词必须说明方向和语义；`compatible_with` 不等于 `installed_in`，`announced` 不等于 `commercialized`，`capability_claim` 不等于交付验收。

### 3.5 State

State 是由已批准 Event 产生的、带有效期的时间化断言，不是 Event 的替代物：

```json
{
  "recordType": "world-state",
  "schemaVersion": "world-state/1",
  "subject": {"id": "robot:opaque-id", "entityType": "robot"},
  "dimension": "commercialization",
  "value": "pilot",
  "validFrom": "2026-09-20T00:00:00Z",
  "validTo": null,
  "observedAt": "2026-09-20T01:00:00Z",
  "stateStatus": "known",
  "sourceEventId": "event:opaque-id",
  "evidenceRefs": ["evidence:opaque-id"]
}
```

`unknown` 和 `conflict` 是显式状态；没有记录不等于已记录的 unknown。

## 4. 标准更新闭环

一次现实变化的最小闭环是：

1. **Observe**：记录观察对象、来源、时间和任务范围。
2. **Evidence**：提取直接支持 Claim 的证据位置和原文，不把整页 URL 当作充分证据。
3. **Classify**：先判断 `NEW_EVENT`、`FOLLOW_UP` 或 `ENRICHMENT`，并检查重复事件。
4. **Resolve**：搜索 canonical entity 与 alias；身份不确定时停在候选或 pending。
5. **Model**：形成 Event、Relation、State 或字段 Claim；保留方向、时间和状态。
6. **Review / Apply**：通过现有受控入口提交、审核和写入；公共贡献入口不直接写 canonical。
7. **Read back**：按稳定 ID 重新读取，检查 Evidence、Entity、Relation、Timeline 和相关投影。
8. **Project**：需要人类阅读时再生成 Article，并双向关联 Event；Article 不能反向替代 Event。

失败、冲突、未知和未完成的步骤必须留在结果中，不能用“成功”掩盖断点。

## 5. 公共投影视图

| 视图 | 主要回答 | 权威语义 |
| --- | --- | --- |
| Profile | 这个 Company / Robot / Part 是什么 | Entity 与字段 Claim 的投影 |
| Graph | 谁与谁有什么关系 | Relation 的投影 |
| Timeline | 什么在何时发生、状态如何变化 | Event 与 State 的投影 |
| Article | 人如何理解一个或多个变化 | Event 的叙事投影，不是事实源 |

在本开源框架里，Profile、Graph 和 Timeline 都是 canonical truth 的读模型；它们不能各自维护一份独立事实。Article 是可选的下游投影，不属于 World Model 核心真值层。

Domain Pack 可以增加领域词汇，World 可以增加命名空间、成员资格和读投影，但都不能复制或分叉 canonical Entity、Claim、Relation、Event 与 Evidence。

## 6. Agent-first 兼容原则

每个公开读面 SHOULD 提供：稳定 identity、状态语义、Evidence 引用、时间字段、可预测错误和能力发现入口。

新增字段应当是 additive；消费者 MUST 忽略未知字段，生产者 MUST 保留既有字段和 ID。破坏语义、删除字段或改变 ID 含义需要升级 major 版本并提供迁移说明。

仓库中的协议 Schema、Domain Pack、示例、API capability、Agent Guide 和运行时实现必须共享同一事实口径。尚未实现的目标能力不能仅因为写进文档就被视为已存在。

## 7. 当前开源实现映射与边界

本规范与 `industry-world-model` 当前实现对齐，但不把目标状态冒充为已实现能力：

- 公共贡献协议与 JSON Schema：[`protocol/README.md`](protocol/README.md) 与 `protocol/schemas/`。
- 可执行领域词汇：`packs/<name>/domain.yaml`；Robotics 是第一参考实现。
- Git-native 候选材料：`contributions/<pack>/<slug>/contribution.json`，通过 `scripts/validate-contributions.py` 校验。
- canonical runtime、读模型与 proposal/review 边界：`apps/api/`。
- Agent proposal gateway：`apps/agent/`；Agent 不拥有 canonical truth。
- Multi-World 目标架构与身份迁移：[`docs/multi-world-architecture-v0.1.md`](docs/multi-world-architecture-v0.1.md)。
- 当前 v0.3 Contribution Protocol 是本文件原则的可执行子集；本文件中的更广语义只有在 Schema、API 或 materializer 实现后才成为运行时能力。

当前 runtime 已有 Entity、Alias、Source、Claim、Evidence、Relation、Event、EventEntity、MediaAsset、IngestJob、ReviewTask 与 ChangeLog。Snapshot 仍主要是外部版本/差异契约；公共贡献不能自行把 proposed 状态升级为 canonical verified truth。

当前没有因此自动获得统一跨行业 ontology、通用约束求解器、公开 canonical write API、自动 entity resolution、采购执行权限或已完成的 Multi-World v0.4 迁移。

## 8. 思想谱系（Intellectual Lineage）

Reality-First World Modeling 不是宣称从零发明一套与软件工程历史无关的方法。它更像是把几条已经成熟、但长期分散在不同领域的工程传统重新组合到 Agent 时代。

### 8.1 Running Code 与由摩擦生长的规范

互联网工程长期强调先让真实实现互操作，再根据运行中的失败、歧义和兼容问题收敛协议。AIMAN 的 `Spec by Friction` 延续这个方向：规范先给出最小不变量，真实 Agent 调用暴露重复摩擦后，再把问题逐级固化为文档、Schema、CLI gate、CI 或 runtime fail-closed 约束。

因此，规范不是现实之前完成的蓝图，而是现实使用留下的压缩记录。

### 8.2 XP / Agile / Lean：反馈优先于过早抽象

XP、Agile 与 Lean Software Development 都强调短反馈回路、简单设计和避免为尚未发生的需求预造复杂抽象。Reality-First Development 采用相同原则：先让最小结构在真实工作中产生价值，只有当某种错误、重复劳动或协调成本持续出现时，才提升抽象层级。

不是“先设计完整系统，再寻找使用场景”，而是“先观察稳定需求，再让系统长出对应结构”。

### 8.3 Domain-Driven Design：让模型服从领域

DDD 强调模型来自对真实领域的持续理解，并允许模型随着理解加深而重构。Reality-First World Modeling 接受同一约束：当现实不能被当前 Schema 正确表达时，优先检查模型是否缺少概念，而不是把现实强塞进已有字段。

Canonical Entity、明确的业务语义与领域词汇都继承了这条传统。

### 8.4 Event Sourcing：变化本身是一等事实

Event Sourcing 的关键启发是：当前状态不是全部历史，状态应当能够由曾经发生的变化解释。AIMAN 因此把 Event 作为一等对象，区分 `new_event`、`follow_up`、`enrichment`、`supersedes` 等历史语义，并避免用覆盖当前字段的方式抹去过去。

AIMAN 在此基础上进一步要求 Event 绑定 Evidence，并明确观察时间、发生时间、有效时间和记录时间。

### 8.5 Knowledge Graph / Semantic Web / Provenance：实体、关系与可追溯性

知识图谱与语义网传统提供了 Entity、Relation、Canonical Identity、Provenance 等重要基础。开放世界假设也提醒我们：模型中没有一条记录，不等于现实中不存在；未知必须能够作为合法认知边界存在。

AIMAN 因此坚持 `Unknown > Guess`，并要求重要 Claim 能够追溯到 Evidence 与 Source。关系不只是自然语言描述，而是带方向、时间、角色和证据的可计算对象。

### 8.6 Digital Twin：让数字模型持续追随现实

Digital Twin 追求现实对象与数字表示之间的持续同步。AIMAN 将这个思想从单一设备、工厂或物理系统扩展到产业世界：Company、Robot、Part、Event、Funding、Deployment、Open Source、BOM 和 Supply Chain 都可以成为持续变化的模型对象。

目标不是一次性复制现实，而是持续缩短“现实发生变化”到“机器能够可靠读取该变化”之间的延迟。

### 8.7 AIMAN 的组合

这些传统分别解决了不同问题：

- Running Code / IETF-style evolution：规范如何从真实互操作中成熟。
- XP / Agile / Lean：何时应该抽象，何时不应该。
- DDD：模型如何贴近真实领域。
- Event Sourcing：如何保存变化和历史。
- Knowledge Graph / Semantic Web：如何表达身份与关系。
- Provenance：如何回答“凭什么相信”。
- Digital Twin：如何持续同步现实与数字模型。

Reality-First World Modeling 的工作，是把它们组合成一个面向 Agent 的连续闭环：

**Reality → Observation → Evidence → Identity → Event / Relation / State → Readback → Projection → Reality**

这里的重点不是声称每个组成部分都是新发明，而是把这些成熟工程思想放进同一个机器可读、证据可追溯、持续演化的 World Model 中。

这也形成 AIMAN 两个互补的方法：

- **Reality-First Development**：让真实使用决定软件如何生长。
- **Reality-First World Modeling**：让真实证据决定知识如何生长。

两者共享同一个原则：

> **不要让抽象先于现实成熟。**

## 9. 版本与演进

规范演进按以下顺序：先观察真实调用和失败，再补最小字段或语义；不为未来行业预造空泛框架。

1. `world/0.x`：允许新增记录类型和字段，必须保持未知字段可忽略。
2. 发生真实兼容问题时，新增显式版本和迁移说明；不静默改变旧字段语义。
3. 只有在实体、关系、事件、证据和时间语义长期稳定后，才冻结更高版本。

扩展必须回答：它表示现实中的什么、证据在哪里、时间如何解释、身份如何稳定、谁有权写入、如何读回、旧 Agent 如何安全忽略它。
