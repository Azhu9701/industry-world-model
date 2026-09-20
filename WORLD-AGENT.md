# AIMAN World Agent Guide

> 给读取、研究、观察、审核和受控执行 AIMAN World 的 Agent 的最小工作契约。

- Version: `world-agent/0.1`
- Status: Draft
- Default language: follow the task; preserve canonical field names and evidence text
- Authority: Agent is an executor or observer, not the owner of canonical truth

## 1. 先理解你的角色

Agent 可以：

- 发现和读取 World 的 Entity、Event、Relation、State、Evidence 与 Article 投影；
- 按任务范围检索来源、提取证据、解决身份、分类事件；
- 生成候选 Event、Relation、字段 Claim、冲突报告或观察材料；
- 在明确授权和受控入口下提交或执行动作，并完成读回。

Agent 不可以自行：

- 把模型输出、搜索摘要、文章共现或主体宣传变成 canonical fact；
- 绕过身份、权限、审核、审计、受控 Adapter / review boundary 或 Evidence 链；
- 因为没有记录就断言 unknown、停产、解散、量产、交付或采购可用；
- 用文章、发布时间或列表顺序替代 Event、发生时间和实体 ID；
- 将 `received`、`pending`、HTTP 200 或本地写入成功报告为已上线。

## 2. 冷启动顺序

没有 AIMAN 私有上下文时，先从仓库本身认识系统：

1. 读取 `README.md` 与 `AGENTS.md`，确认仓库角色、允许动作和验证命令。
2. 读取 `WORLD.md`，理解 Reality First、Evidence First、Canonical Identity First、Event First 等不变量。
3. 读取 `WORLD-PROTOCOL.md`，理解身份、时间、状态、幂等、错误和读回语义。
4. 读取 `protocol/README.md` 与 `protocol/schemas/`，确认当前真正可执行的 Contribution Protocol。
5. 读取任务对应的 `packs/<name>/domain.yaml`，确认合法 entity type、claim predicate、relation triple 与 event type。
6. 如果连接 deployed node，再读取 `/api/v1/meta`、`/api/v1/capabilities` 和 `/api/v1/packs/{pack}`。
7. 如果要贡献材料，先确认使用 Git-native contribution 还是已开放的 deployed proposal API；缺少明确 capability 或 authorization 时停止在候选结果。

当前公共发现链可以概括为：

```text
Repository contract → World invariants → Executable protocol → Domain pack
                   → Runtime capabilities → Read → Propose → Review
```

## 3. 标准任务流程

### 3.1 Understand

明确任务中的：

- World、范围、主体和时间窗口；
- 需要读取、提出候选还是执行已授权写入；
- 验收条件、输出格式和不能触碰的对象。

### 3.2 Search before create

先搜索 canonical Entity、alias、已有 Event、Relation、Article 和 pending 材料：

```text
搜索 Entity → 搜索相同 Event / eventKey → 搜索已有 Relation
→ 检查 Evidence / conflict → 再决定 NEW_EVENT / FOLLOW_UP / ENRICHMENT
```

不能因为名称略有差异就创建重复 Company、Robot 或 Part；也不能因为相同标题就合并两个 Event。

### 3.3 Classify the change

| 分类 | 语义 | 默认处理 |
| --- | --- | --- |
| `NEW_EVENT` | 发生了新的、可验证的状态变化 | 建议新的 Event，关联实体和证据 |
| `FOLLOW_UP` | 对已有 Event 的后续进展、兑现、修订或反转 | 关联原 Event，保留新时间和新证据 |
| `ENRICHMENT` | 补充 Entity/Relation/字段信息，没有新的状态变化 | 更新候选 Claim 或 Relation，不强行建 Event |

分类不确定时输出不确定性，不用文章发布时间替代事件时间。

### 3.4 Gather evidence

每条重要主张至少回答：

1. Source 是什么？
2. 原文哪一段直接支持它？
3. Evidence 支持的是哪个对象、哪个字段、哪个方向和哪个时间条件？
4. 这是事实、主体声明、意见、推导还是待审核候选？
5. Source 是否可复核，是否存在冲突或 provenance gap？

优先使用一手来源。新闻、聚合站、搜索摘要和模型记忆可帮助 discovery，但不能自动成为最终证据。官方来源也不代表其中每一句推断都被官方支持。

## 4. 身份、关系与时间规则

### 4.1 Identity

- 保留 canonical ID；名称只作展示或检索提示。
- 先处理 alias，再判断是否新实体。
- 品牌、公司、产品、Series、Variant、MPN、Part 不可凭名称互换。
- 身份不唯一时输出 `identity_ambiguous`，附候选和需要的证据。
- 不因官网暂时不可访问、文章沉默或搜索不到就断言主体停止经营。

### 4.2 Relation

关系输出必须包含：subject、predicate、object、方向、有效期、Evidence、状态和必要的限定条件。

先问：

```text
谁 → 以什么谓词 → 与谁有关？
证据直接支持这两个对象和这个方向吗？
这是当前关系、历史关系、声明还是推断？
```

以下不能互换：

- `compatible_with` ≠ `installed_in`
- `supplier` ≠ `partner`
- `investor` ≠ `customer`
- `announced` ≠ `commercialized`
- `capability_claim` ≠ `delivery_accepted`

### 4.3 Time

分开记录：发生时间、有效期、来源发布时间、观察时间、采集时间和记录创建时间。未知就保持未知。事件先后只能表示时间关系，不能自动生成因果关系。

## 5. 输出候选，而不是越权裁决

推荐的 Agent 结果形状：

```json
{
  "decision": "accept|pending|skip|conflict",
  "classification": "NEW_EVENT|FOLLOW_UP|ENRICHMENT",
  "canonicalEntities": [],
  "events": [],
  "relations": [],
  "evidence": [],
  "unknowns": [],
  "conflicts": [],
  "requestedAction": "review",
  "readback": {"required": true, "performed": false}
}
```

`accept` 在此处只表示 Agent 认为材料满足“可提交审核”的条件，不表示服务端已经批准 canonical fact。若没有明确的受控写入能力，`requestedAction` 应为 `review`，而不是 `write_canonical`。

## 6. Article 生成规则

文章生成必须发生在事实建模之后：

```text
公开事实 → Evidence → Event → Entity / Relation / State
         → Timeline / Graph readback → Article
```

生成 Article 前检查：

- Event 已有稳定 ID 或明确说明仍是候选；
- 文章中的公司、机器人、Part 都能回到 canonical identity；
- 关系方向和时间条件没有被叙事改写；
- 事实、主体声明、意见、商业意图和预测分开；
- 预测写成带条件、观察指标和反证信号的可验证假设；
- Article 绑定 Event 后，Event 仍能脱离 Article 独立读取。

如果 Event 未注册或 Evidence 不足，生成研究材料或草稿并报告缺口，不创建看似已核验的文章。

## 7. 读回验收

任何受控写入、候选提交或文章绑定后，Agent MUST 做与动作相称的读回：

```text
稳定 ID / eventKey
  → Entity identity
  → Evidence refs / status
  → Relation direction
  → Event date / valid period
  → Graph / Timeline / State projection
  → Article binding（如有）
```

读回失败时保留“已提交但未核验”，不得报告完成。公共贡献入口的 receipt 只证明材料已收取或进入审核队列。

## 8. 必须停下来的情况

遇到以下任一情况，停止升级事实，输出缺口或请求人工/控制平面处理：

- canonical identity 有多个候选；
- Source 可访问但不直接支持具体 Claim；
- 只有搜索摘要、转载或单方营销声明；
- 需要推断因果、量产、交付、停产、采购可用性或安装关系；
- Event 日期未知却要求精确时间线排序；
- 目标 Event 无法通过 canonical identity、pack 和 Evidence 唯一对应；
- `/api/v1/capabilities` 或 deployment contract 未宣布写能力，或当前身份没有对应 scope；
- 写入后无法以稳定 ID 读回；
- 请求要求数据库直写、秘密、任意 Shell、绕过认证或覆盖历史。

应输出 `unknown`、`pending`、`conflict` 或 `unsupported`，并说明下一步所需的 Evidence、身份确认或权限。

## 9. 当前能力边界

本开源仓库的公共 Agent 边界是 **review-first contribution**：

- `protocol/schemas/` 定义当前公共贡献可以表达的结构，不存在“文档写了就自动支持”的能力。
- Git-native contribution 写入 `contributions/<pack>/<slug>/contribution.json`，通过 CI/validator 后仍只是 proposed material。
- deployed Agent 可以通过 `/api/v1/proposals` 提交候选，但只有 capability 与 authorization 明确允许时才可调用。
- `packs/<name>/domain.yaml` 是可执行 vocabulary；未声明的 entity、predicate、relation triple 或 event type 不能偷偷写入。
- `apps/api` 持有 canonical runtime、review 与 materialization 边界；`apps/agent` 是 proposal gateway，不拥有 truth。
- Multi-World 当前仍是 v0.4+ 目标架构；v0.3 的 pack-scoped identity 不得被 Agent 假装成已经完成的 global identity。
- MCP、well-known manifest、采购、生产或其他 action capability 只有在具体 deployment 明确实现并广告后才存在，不能从本规范自动推断。

如果文档、Schema、capability endpoint 和实际行为不一致，以**更保守的真实运行边界**为准，并把差异记录为规范或实现缺口；不要通过猜测补齐能力。

## 10. 最小 Agent 检查清单

完成一次任务前，逐项确认：


- [ ] 已读取仓库契约、当前 pack，以及 deployed runtime 的 capability（如适用）。
- [ ] 已搜索 canonical Entity、alias、已有 Event、Relation 和 pending 材料。
- [ ] 已区分 `NEW_EVENT` / `FOLLOW_UP` / `ENRICHMENT`。
- [ ] 每条重要主张都有直接 Evidence 或明确缺口。
- [ ] 时间、方向、状态和主体声明没有被猜测填充。
- [ ] 只使用当前身份被授权的接口。
- [ ] 写入或提交后已按稳定 ID 做 readback，或明确标记未核验。
- [ ] Article（如有）只是 Event 的解释层。
- [ ] 输出了 Unknown、Conflict、Pending 和剩余风险，而不是只输出结论。
