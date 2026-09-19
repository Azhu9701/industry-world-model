# Phase 0 — Identity & Route Collision Census（Robot World）

Date: 2026-09-19
Method: **read-only**. Production corpus pulled via `psql` (SELECT only, user `emibot_app`); normalization done offline; no schema, URL, or data change.
Implements: `docs/multi-world-architecture-v0.1.md` §14 Phase 0（"generate current robotics identity/event collision inventory; identify route slug collisions under /robot/*"）.

## 0. Corpus

| source | rows | notes |
| --- | --- | --- |
| `robots` | 805 | 772 with `url_slug` (all distinct); 33 without |
| `company_profiles` | 96 | canonical_name is the only company identity today |
| `entity_aliases` | 58 | all `entity_type=company` |
| `parts` / `part_series` | 13 / 2 | ADR-0005 domain |
| `industry_events` | 140 | 140/140 distinct `event_key` |
| `world_events` / `world_relations` | 0 | empty in emibot production — v0.3 IWM runtime corpus below |
| IWM contributions | 2 files | 10 entities + 2 events (`viabot`, `_example-openbot-x1`) |

Comparison normalization used (must be ratified in v0.4 spec): NFC → casefold → whitespace collapse → punctuation to space → `_`/space to `-` → collapse/strip `-`.

## 1. Headline conclusions

1. **`/robot/*` 保留路由：零冲突（Phase 0b PASS）。** 772 个 slug 与 RFC §8.2 保留字 `{timeline, graph, search, evidence, entities, capabilities, about}` 无一相撞；前端 `/robot/` 下当前只有 `$id.tsx` 一个动态路由，无静态子路由需要腾挪。`/timeline`、`/graph` 已存在，可按 RFC §8.4 原地升格为 Global 视图，无需 301。
2. **slug 空间本身非常干净。** 772 slug 全局唯一；归一化后零碰撞；零个格式越界（全部符合 `^[a-z0-9]+(-[a-z0-9]+)*$`）。`entity:robot:<slug>` 可立即映射 772 个。
3. **最大的缺口不是碰撞，而是 key 派生政策：57/96 的 canonical 公司只有中文名。** 别名表只覆盖了其中 4 家（优必选→UBTECH、宇树→Unitree、普渡→PUDU、达闼→CloudMinds）。`entity:company:<key>` 的 ASCII 规则（EN 别名注册 / 拼音 / 允许 CJK）是 v0.4 前必须裁决的开放项。
4. **身份碎片化集中在 robots.company 自由文本：283 个不同写法中 197 个没有任何 canonical profile。** 但近重复写法只有 2 簇（Italian Institute of Technology 两种拼法、Rainbow vs Rainbow Robotics）——问题主要是「缺档案」而非「一物多档」。
5. **发现 1 条真实身份/URL 错位：`booster-t1` ← Booster T2，`booster-t1-2` ← Booster T1**（同为加速进化）。URL 与产品代际相反，v0.4 映射前需 editorial 修正或显式 alias。

## 2. Findings（逐项，显式列出、不静默合并）

### F1 — 保留路由冲突：无
772 slug ∩ 7 保留字 = ∅。另：未来 `/robot/search`、`/robot/entities` 等上线路由时不受现有数据阻碍。

### F2 — Robot slug 质量：干净
- 772/772 唯一，归一化碰撞 0，格式越界 0。

### F3 — 33 个 robot 无 slug（占 4.1%）
无法直接产出 `entity:robot:<slug>`。含 2026-09-19 Sensor Round 001 新入库 4 件（ANSCER AR250/AR650/AR1250、AI Sapiens K1）、远征A3 Ultra、NAO、小迪（比亚迪）等。v0.4 backfill 前需补 slug 或定义 name→key 派生规则。
完整清单：`id Robot202606151764/1765`（ROLA ×2）、`Robot202609021948/1949/1950`、`Robot202609041951/1952/1953/1955`、`Robot202609091956–1976`、`Robot202609180219414406d0b`、`Robot20260919093445547a5fa`、`Robot20260919094302690f984`、`Robot20260919094318743acd0`、`Robot20260919094334555257f`。

### F4 — 同名产品的 slug 后缀无身份语义（4 族）
URL 的 `-2/-3` 后缀反映导入顺序，不是身份。v0.4 key 需要「公司限定」规则消歧：

| 族 | slug | 产品 | 厂商 |
| --- | --- | --- | --- |
| apollo | `apollo` | 镜识 Apollo | 镜识科技 |
| | `apollo-2` | Apollo 2 | Apptronik |
| | `apollo-3` | Apollo | Apptronik |
| c1 | `c1` | Striding AI C1 | 正行创新 |
| | `c1-2` | C1 | 伽利略机器人 |
| e1 | `e1` | Noetix E1 | 松延动力 |
| | `e1-2` | E1 | 伽利略机器人 |
| | `e1-xingzhetaishan` | E1（行者泰山） | 优宝特机器人 |
| booster | `booster-t1` | **Booster T2** | 加速进化 |
| | `booster-t1-2` | **Booster T1** | 加速进化 |

前三族是同名不同物（合法，key 应加公司限定）；booster 族是同一厂商两代产品 URL 互相错挂——**唯一一条建议在 v0.4 之前修正的数据问题**。

### F5 — Company key 派生政策缺口（53 家无 ASCII 形态）
96 家 canonical 公司中 57 家纯中文名；`entity_aliases` 仅覆盖 4 家。候选政策（v0.4 裁决）：
- A. 编辑补录 EN 别名（53 家，工作量大但 key 质量最高，且 alias 本身就是资产）；
- B. 拼音 slug（如 `yushu-keji`，机械可生成，但与品牌英文名不符）；
- C. 允许 CJK 进 canonical key（URI 会 percent-encode，`/id/` 可读性差）；
- 建议 A 为主、B 兜底，C 不采用。

### F6 — robots.company 身份碎片化（197/283 无档案）
robots.company 是自由文本。283 个不同值中 197 个在 company_profiles 中无对应（ANSCER Robotics、Ghost Robotics、LG Electronics、META…）。近重复簇仅 2 个：
- `Italian Institute of Technology` = `Italian Institute of Technology (IIT)`；
- `Rainbow` vs `Rainbow Robotics`（需人工裁决是否同对象）。
结论：v0.4 backfill 的公司身份工作量主要在**补录 profile**，不在消歧合并。

### F7 — 事件身份：key 全唯一，但 v0.4 造 key 需 correction 语义
`industry_events.event_key` 140/140 唯一、字符集全部合法。形态：`legacy-blog-*` 84 条、日期前缀式 ~56 条。两类显式清单：
- 23 条归档事件共享同一标题「开源追踪归档｜重复快照校正」（`legacy-blog-12/14/17–42/78/81/83`）——若按标题造 key 会全部相撞；必须保留现有 key 或引入 `event:<subject>:<action>:<period>` 主语派生。
- 3 对 `-launch` / `-launch-corrected` 事件同标题不同 key（Agility Digit 5、Unitree G1+、蓝虫 Mantis）。v0.4 需裁决：corrected 是**同一 canonical Event 的修订版**还是独立事件（RFC §7 未覆盖 revision 语义）。

### F8 — IWM v0.3 语料与生产语料：零相撞
10 entities + 2 events 与 772 robot slug、96 company slug 无一相撞（`openbot-x1`、`viabot` 等均为新造）。`UNIQUE(pack, entity_type, entity_key)` 现状下 runtime 内亦无实际重复行。

## 3. Phase 0 最终裁决（2026-09-19，全部收口）

```text
Phase 0
├── Route namespace                PASS
├── Robot/Event inventory          PASS
├── Explicit collision census      PASS
├── Global identity semantics      DECIDED
├── Event revision semantics       DECIDED
├── Known identity bug             1（Booster，待修）
└── v0.4 migration readiness       READY AFTER FIX
```

### 决议 1 — Global identity 用不可变 opaque ID（替代「英文优先、拼音兜底」草案）

```text
entity:company:01K5...   entity:robot:01K6...   event:01K7...
```

英文别名、拼音只承担可读 slug / alias，**不承担身份**。`/id/entity/company/<id>` 是机器身份锚点；`canonical_slug` 只是人类友好地址，可重定向。名字可变、别名可增、slug 可换，ID 永不变。§4 草案中的政策 A/B/C 作废，CJK 问题就此一次解决。

### 决议 2 — Event revision 语义

> 修正文档不是新历史；现实再次发生，才是新事件。

同一现实发生 + 日期/标题/描述/证据纠正 = **同一 Canonical Event + 新 revision**（`supersedes_revision` + `reason: factual_correction`），历史版本保留、不静默覆盖（F7 的 3 对 `-corrected` 事件迁移后走 revision 合并）；只有现实中再次发生才建新 Event，事件间用 `follow_up_of` / `enabled_by` / `supersedes` 连接。

### 决议 3 — Booster T1/T2：先修 identity，URL 后置

见 `docs/identity-resolutions.md` RES-001。两行生产数据的身份事实（name/描述/官方 product_url）已核验各归其位，错的只是 url_slug 挂反；给未来 immutable ID 正确挂靠即可，**slug/路由迁移单独走**（先查索引与外链引用，再定 canonicalize/redirect），不与 v0.4 混做。

## 4. Phase 0 acceptance 对照（RFC §14）

| acceptance | 状态 |
| --- | --- |
| every current robotics Entity/Event maps to one candidate global canonical key | **PASS（政策已定）**：opaque ID 生成即可覆盖全部对象；772 robots/96 companies/13 parts/2 series/140 events 全部可挂靠，33 无 slug robot 与 53 无 ASCII 公司不再构成阻塞（决议 1） |
| duplicate/collision list is explicit | **PASS** = 本文档 F1–F8 + `docs/identity-resolutions.md` |
| current v0.3 validation remains green | **PASS**（census 只读；RFC 183123c 验证结论仍有效） |
| no production URL or database migration required yet | **PASS**（仅 SELECT） |

## 5. 复现（census 脚本已入库）

```bash
# 1) 导出只读语料（不提交；exports/ 已 gitignore）
mkdir -p exports/phase0
python3 scripts/phase0-identity-census.py --print-sql   # 完整 SQL/query contract
# robots 用 \copy CSV（名字含换行），其余表 psql -A -t -F '|' 到 exports/phase0/*.tsv

# 2) 跑 census
python3 scripts/phase0-identity-census.py --data exports/phase0
python3 scripts/phase0-route-collision-census.py --data exports/phase0/robots.csv \
    --routes-file <静态 /robot/* 路由清单，可选>
```

脚本仅依赖标准库；新增 World 或每次 v0.x 升级重跑同一套即可。2026-09-19 原始导出与脚本运行记录留存于本机会话 `/tmp/iwm-census/`。

## 6. 进入 v0.4 前的动作清单（已按决议更新）

1. ~~裁决 canonical key 的 CJK 政策~~ → 已定：opaque ID（决议 1）。
2. ~~事件 revision 语义~~ → 已定（决议 2），写进 v0.4 spec。
3. Booster：identity 决议已记录（RES-001），slug/路由迁移单独立项（决议 3）。
4. company_profiles 补录 197 个缺失厂商（F6，分批，先高频厂商）——补录对象挂 opaque ID，不再阻塞 key 政策。
5. 33 个无 slug robot 补 slug（F3）——服务于人类友好地址，不再阻塞身份。
6. 写 **v0.4 Protocol Spec**：`World` / `WorldMembership` / immutable Global ID / Event Revision 四件套 + 本 census 的归一化规则（§0）正式进 identity 规范。
