# ROADMAP_v0.4.md — Semantic Depth

> 这份文件是 v0.4 阶段的规划文档。v0.3 的实施历史见 `handoff.md`（已冻结，
> 不再追加）。v0.4 开始实施后，按 handoff.md 同样的 "Commit N" 节奏在本文件
> 追加实施记录，不要混回 handoff.md。

---

## 0. 这个阶段在整体路线里的位置

```
v0.2  Bridge Prototype     ✅ 完成 —— 证明闭环能跑
v0.3  Runtime Health       ✅ 完成 —— 证明闭环不会突然挂掉
v0.4  Semantic Depth       🔄 本文档 —— 把语义素材做厚实
v0.5  Assistive Clients    ⏸ 未开始 —— 第一次面向真实用户产生价值
v0.6  Authoring Workflow   ⏸ 未开始
```

**诚实评估：v0.4 结束后，项目对终端用户仍然没有直接价值。** `state.json` 会
变得语义更丰富，但它依然是 JSON——没有人会直接读 JSON 来玩游戏。v0.4 的产出
是给 v0.5 用的原材料，不是给玩家用的功能。这不是悲观，是阶段定位的诚实表述，
避免规划时不自觉地把 v0.5 的活提前混进来做。

**v0.4 不做什么（边界）：**
- ❌ 不做"LLM 把语义转成自然语言讲述"——这是 v0.5 Adapter 的工作
- ❌ 不做多客户端（screen reader bridge、keyboard-only client）——v0.5
- ❌ 不碰通信机制，继续文件轮询
- ❌ 不解决 D-09（session 终止协议）——独立评审，不与本阶段混
- ❌ 不实现 schema 版本协商逻辑（D-07）——只做 schema 文档化，不做协商代码
- ❌ 不重新设计 schema 让它"更通用"——新字段都应该从 demo 游戏的具体场景标注
  里长出来，不是先画一个理想模型再往里填内容

**为什么不把 v0.5 提前合并进来：** 如果语义素材（场景描述、动作后果等）还不
厚实就去做"LLM 讲述"实验，LLM 只能靠自己编造细节填补空白——这正好违背项目
愿景的核心原则（"开发者标注语义真相，模型不该自己猜"）。先把地基素材做厚实，
再建适配器，两件事才能都做到位。

---

## 1. 任务清单与依赖关系

```
D-10 场景语义补全         （独立，最简单，先做；同时是 D-12 的隐藏前提）
D-11 动作后果语义落地      （独立，管道已通，只填数据）
D-13 认知负荷场景聚合      （依赖 D-11：聚合的是 D-11 填好的 cognitive_load 数据）
D-12 历史语义化           （依赖 D-10 + D-11：场景语义和 semantic_label 都要先备好）
D-14 schema 文档化        （收尾，基于前四项最终落地的字段结构归档）
```

**依赖关系说明（D-12 的隐藏依赖，v0.3 规划阶段漏掉的一环）：**
D-12 要做的 `narrative_thread` 结构里，每一条历史记录都会关联 `scene` 字段
（如 `"scene": "room"`）。如果 D-10 没做完，这个 `scene` 字段只是个空壳 ID，
不携带任何语义，D-12 做出来的历史摘要会很单薄。所以 D-12 必须排在 D-10 *和*
D-11 都完成之后，不能只满足 D-11 这一个前提。

---

## 2. 详细任务说明

### D-10：场景级语义补全

**现状：** `_export_scene()`（a11y.rpy）已经导出 `visual_description`/
`audio_cues`/`complexity` 三个字段，管道早就通了。但 `scenes` dict
（script.rpy）里，目前只有 `crossroad` 和 `echo` 填了非空的 `audio_cues`，
`room`/`end` 是占位的空值，四个场景没有一个是按统一标准认真填写的。

**待办：** 给 `room`/`crossroad`/`echo`/`end` 四个场景的 `visual_desc`/
`audio_cues`/`complexity` 补齐有意义的内容，作为"开发者标注语义"的范例。

**不做：** 不新增场景，不改导出结构（`_export_scene` 代码不用动）。

**验证方式：**
跑全流程，在 Agent 侧 `describe_state()` 临时打印 `state["scene"]`，确认
四个场景在对应 turn 都能看到非空的语义字段（沿用 v0.3 Commit 7 验证教训：
不要依赖最终落盘的 `state_*.json`，跟随 turn 实时观察）。

---

### D-11：动作后果语义落地（consequence_hint / emotional_weight）

**现状：** `_export_actions()`（a11y.rpy）已经支持这两个字段的导出
（`if val: entry[field] = val`），这是 v0.3 就做好的管道。但 `script.rpy`
里 `room_choices`/`crossroad_choices`/`finish_choices` 三组 choice 没有任何
一处真正填了这两个字段——管道通了，没有水流过去。

**待办：** 给三组 choice 补上 `consequence_hint`（这个选择会导向什么）和
`emotional_weight`（trivial/low/medium/high）。

**示例（crossroad_choices 的其中一项）：**
```python
{
    "text": "Go left",
    "semantic_label": "explore_path_a",
    "cognitive_load": "low",
    "consequence_hint": "通向较暗的叙事分支，呼应房间互动的选择",
    "emotional_weight": "medium",
}
```

**验证标准：** 导出的 `actions[]` 数组每个 choice 项都能看到这两个字段
（沿用 D-10 同样的实时打印验证方式）。

---

### D-13：认知负荷的场景级聚合

**依赖：** D-11 完成（聚合的数据源是 D-11 填好的 `cognitive_load`）。

**现状：** `cognitive_load` 目前只存在于单个 choice 上，没有场景级别的汇总。

**待办：** `_export_scene()` 新增 `accessibility.cumulative_load` 字段，
基于当前场景所有 choice 的 `cognitive_load` 做聚合（建议取最高值，
简单直接，不引入复杂的加权逻辑）。

**验证标准：** crossroad 场景（三选项）的 `cumulative_load` 应该能区分于
room 场景（两选项）——具体数值不重要，重点是聚合逻辑跑起来、且结果合理。

---

### D-12：历史语义化（choice_history 关联语义标签）

**依赖：** D-10（场景语义）+ D-11（semantic_label 数据）都完成。

**现状：** `_export_player_state()` 只导出原始 `choice_history`
（字符串数组，如 `["interact_room", "path_left"]`），是给程序读的标识符，
不携带语义。

**待办：** 新增 `player_state.narrative_thread` 字段，把 `choice_history`
和已有的 `semantic_label`/场景信息关联成结构化记录：
```json
"narrative_thread": [
  {"choice": "interact_room", "semantic_label": "engage", "scene": "room"},
  {"choice": "path_left", "semantic_label": "explore_path_a", "scene": "crossroad"}
]
```

**不做：** 不生成自然语言摘要（"玩家选择了探索并触碰了物体"这种文本）——
那是 v0.5 Adapter 的工作。D-12 只负责把结构化的语义关联打好，不负责把它
翻译成人话。

---

### D-14：schema 文档化与版本归档

**依赖：** D-10~D-13 全部完成（基于最终落地的字段结构来归档，不要边做边写，
否则文档和代码会不同步）。

**现状：** v0.3 阶段已经产出 `schema_v0.3.json`，作为基线。

**待办：**
- 新建 `game/docs/schema_v0.4.json`：在 v0.3 基础上，记录 D-10~D-13
  新增/填实的字段（场景的 `cumulative_load`、actions 的 `consequence_hint`/
  `emotional_weight` 不再是"管道已通但无数据"，而是"管道通且有真实数据"、
  新增的 `narrative_thread`）
- `schema_version` 值改为 `"0.4"`

**不做：** 不实现 schema 校验逻辑，不做版本协商代码（D-07 独立处理，不在
本阶段范围）。

---

## 3. 实施顺序（含验证节点）

按 Commit 节奏来，每个都是独立可验证单元，不需要每次跑完整 16 turn
（这些改动不影响 Agent 的决策逻辑——Agent 只读 `type`/`index`，新字段对它
透明），用 D-10 同款的"实时打印 + 跟随 turn 观察"方式验证即可。

```
Commit 8  — D-10  场景语义补全
Commit 9  — D-11  动作后果语义落地
Commit 10 — D-13  认知负荷场景聚合
Commit 11 — D-12  历史语义化
Commit 12 — D-14  schema 文档化（收尾）
```

---

## 4. v0.4 完成后的状态判断（诚实版本）

**能自信说的：**
- ✅ 语义字段不再是"管道通但没数据"的占位状态，demo 游戏的全部场景和选项
  都有真实、有意义的语义标注
- ✅ schema 文档完整反映 v0.4 结束时的真实导出结构，v0.5 的 Adapter 开发者
  可以直接依据它工作，不需要再回头改桥接层

**仍然不能说的：**
- ❌ 项目对终端用户（视障玩家、想闭眼玩游戏的人等）产生了直接价值——
  这要等到 v0.5
- ❌ 已经验证语义字段确实能提升 LLM 讲述质量——这需要 v0.5 才能检验，
  v0.4 阶段只负责"把素材做好"，不负责"验证素材有没有用"

**如果想提前感受到"有用"的反馈（不计入正式版本路线）：**
可以在 v0.4 收尾后，写一个一次性的、不进版本号的小脚本，手动把某个 turn 的
完整 JSON 喂给 LLM，让它生成一段中文叙述。这不是产品功能，是给自己一个
"地基真的能支撑起一根柱子"的验证，确认语义字段的厚度对叙述质量有没有
实际帮助。明确标注成实验性脚本，不要和 v0.5 的正式范围混在一起。