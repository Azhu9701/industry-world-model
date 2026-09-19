# Identity Resolutions

Living ledger of explicit identity decisions. Every entry is evidence-backed and
never silently merged (RFC §14 Phase 0 acceptance; AGENTS.md invariants).
v0.4 backfill consumes this file when minting immutable global IDs.

## RES-001 — Booster T1 / Booster T2 slug inversion（2026-09-19，open: slug fix deferred）

**Finding** (Phase 0 census F4): production `robots` rows carry inverted `url_slug`:

| url_slug | row name | actual product | evidence in row |
| --- | --- | --- | --- |
| `booster-t1` | Booster T2 | **T2**（旗舰：31 DoF、Jetson Thor T5000、~1.4 m / 42–43 kg） | description + `product_url=https://www.booster.tech/cn/booster-t2/` |
| `booster-t1-2` | Booster T1 | **T1**（紧凑：30 kg、23 DoF、竞赛/教育/开源） | description + `product_url=https://www.booster.tech/cn/booster-t1` |

External verification (2026-09-19): booster.tech T2 official page（Thor T5000、31 DoF）与 T1 定位（30 kg、RoboCup 竞赛平台）与行内数据一致。

**Resolution**:
1. **Identity（现在）**：T1 与 T2 是两个独立的 canonical 实体。v0.4 backfill 给各自铸造独立 immutable ID；行内身份事实（name/description/product_url/evidence）已正确，无需改库。
2. **URL（后置，单独任务）**：`booster-t1`/`booster-t1-2` 两个 URL slug 不在 v0.4 中顺手改。先查索引、外链与 Agent 缓存引用，再决定 `/robot/booster-t1` ↔ `/robot/booster-t2` 的最终 canonicalize/redirect 方案。
3. 两个当前 slug 在 v0.4 中登记为 pre-migration alias，映射到正确实体，直到路由迁移完成。

**Rule this entry establishes**: url_slug 是导入产物，不是身份；immutable ID 永远挂在「被证据支撑的现实对象」上，而不是 slug 上。

## RES-002 — Italian Institute of Technology 双写法（2026-09-19，open: profile merge）

census F6 近重复簇：`Italian Institute of Technology` 与 `Italian Institute of Technology (IIT)`。裁决待做：合并为一个 canonical company（opaque ID），`(IIT)` 写法降级为 alias。在 v0.4 backfill 前完成即可。

## RES-003 — Rainbow vs Rainbow Robotics（2026-09-19，open: needs human review）

census F6 近重复簇：`Rainbow` 与 `Rainbow Robotics`。是否同一对象未核实（Rainbow Robotics 为韩星人形厂商；裸名 Rainbow 可能是另一主体或数据残缺）。**禁止自动合并**；核实后在本台账记录裁决。
