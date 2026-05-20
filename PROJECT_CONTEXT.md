# A11y-RenPy-Bridge - Project Context

**当前版本:** v0.2.0
**最后更新:** 2026-05-20
**当前阶段:** Bridge Prototype / Semantic JSON Loop Proof
**状态:** 技术验证完成，但不是最终形态

---

## 一句话

这个项目验证一个命题：

> 游戏应当原生暴露语义状态与可执行动作，而不是让辅助技术在屏幕像素上二次猜测游戏。

当前 v0.2 不是“让 LLM 玩一个 Ren'Py demo”的终点，而是证明 **Ren'Py 可以导出 JSON，Agent 可以读写 JSON，游戏可以被语义动作推进到 finished**。

---

## 当前已验证

- 3 个场景完整通关
- 16 个 turn 单调推进
- 13 个 `advance` 动作推进对白
- 3 个 `choice` 动作完成菜单选择
- 最终导出 `mode: "finished"`
- 不依赖视觉输入、OCR、鼠标坐标或 UI 自动化

这说明 **JSON semantic control loop 成立**。

---

## 当前不是

v0.2 还不是：

- 生产级无障碍客户端
- 屏幕阅读器集成
- 稳定运行时协议
- 通用游戏 Agent 框架
- 完整 A11y 标准

它是第一阶段的桥接原型。

---

## 关键文件

1. `game/a11y.rpy` - Ren'Py 侧桥接运行时
2. `game/script.rpy` - 3 场景 demo
3. `agent/simple_player.py` - Ollama 参考 Agent
4. `docs/handoff-v0.2.md` - 英文 canonical handoff
5. `docs/handoff-v0.2.zh.md` - 中文 handoff
6. `docs/v0.2-validation.md` - 英文验证记录
7. `docs/v0.2-validation.zh.md` - 中文验证记录
8. `docs/schema.json` - v0.2 JSON schema

---

## 架构速览

```text
Ren'Py runtime
  -> writes game/exports/state.json
Agent
  -> reads state.json
  -> chooses one action
  -> writes game/exports/action.json
Ren'Py runtime
  -> consumes action.json
  -> advances game
  -> exports next state
```

核心字段：

- `turn_id`: 同步当前 turn
- `mode`: `idle`, `awaiting_action`, `finished`
- `actions[]`: 当前合法语义动作
- `narrative.current_text`: 当前叙事文本或选择上下文

---

## v0.2 已知限制

这些限制不阻塞 v0.2 的验证结论：

1. **UI 阻塞** - 当前等待 `action.json` 的逻辑会阻塞 Ren'Py 主线程。
2. **需要清理旧状态** - 运行前应删除 `game/exports/state.json` 和 `action.json`。
3. **缺少 session_id** - Agent 可能读到上一轮残留 state。
4. **错误恢复弱** - Ollama 超时、JSON 异常等还没有完整 retry/fallback。
5. **choice 上下文不够干净** - choice turn 会复用上一句 `narrative.current_text` 作为上下文。

---

## Ren'Py 文件索引注意事项

Ren'Py 会递归扫描 `game/` 下的 `.rpy` 文件。

因此不要把临时脚本、备份脚本或文档草稿放到 `game/docs/`、`game/tmp/` 等子目录里。比如 `game/docs/copy.rpy` 会被当作正式脚本加载，可能造成：

- `label start` / `label end` 重复定义
- 脚本索引混乱
- 启动时报 `LabelNotFound: could not find label 'start'`

文档应放在根目录 `docs/`，临时文件应放在根目录 `tmp/` 或仓库外。

---

## v0.3 建议边界

v0.3 不应急着扩展成完整 A11y 标准，推荐聚焦：

- `session_id`
- 非阻塞等待
- Debug overlay
- timeout / error mode
- Agent retry / fallback
- choice context 字段

主题可以定为：

```text
v0.3 Runtime Health
```

---

## A11y 方向

正确的长期方向不是让外部工具看图猜游戏，而是在 infra 层暴露：

- 发生了什么
- 当前可做什么
- 每个动作的语义是什么
- 玩家状态如何变化

LLM 只是一个参考客户端。未来同一接口应能服务 screen reader、keyboard-only client、switch-access client、test bot 和认知辅助工具。

---

## 快速运行

清空旧状态：

```bash
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/state.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/action.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/choice.txt
```

启动 Ren'Py 项目后，在 WSL2 中运行：

```bash
cd /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/agent
python3 simple_player.py
```

期望结束：

```text
Mode: finished
Game finished.
```

---

## 给下一个 AI 助手

不要把 v0.2 说成最终产品。它是 **Bridge Prototype**。

不要把项目定位成“LLM 玩游戏”。更准确的定位是：

> Semantic game accessibility interface prototype.

优先保持阶段边界清楚：文档、验证、演示先于新功能。
