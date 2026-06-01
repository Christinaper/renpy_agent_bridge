# Agent-RenPy-Bridge

**LLM-Enhanced Multi-Modal Access 的游戏语义桥接原型。**

这个项目不是为了证明“LLM 能玩一个 Ren'Py demo”，也不是要用 JSON 取代人类直接体验游戏画面。

它验证的是一个更底层的命题：

> 游戏应当原生暴露开发者标注的语义状态与可执行动作，而不是让辅助技术在屏幕像素上二次猜测游戏。

在这个方向里，JSON 不是给人类直接阅读的最终界面。JSON 是给 LLM 或其他适配器消费的语义真相。LLM 再把同一份语义转换成多种人类友好的输出形式，比如自然语言描述、语音播报、简化摘要、命令式导航、测试日志或个性化辅助说明。

## 当前状态

**当前阶段:** v0.2 Bridge Prototype

**验证结果:** Semantic JSON Loop Proof Validated

v0.2 已经验证：

- Ren'Py 可以导出语义 JSON。
- Agent 可以读取 JSON 并写回结构化动作。
- 游戏可以通过 `advance` / `choice` 动作推进到 `finished`。
- 全程不依赖视觉识别、OCR、鼠标坐标或 UI 自动化。

这不是最终形态，而是第一阶段的桥接原型。

## 避免误解

这个项目 **不是**：

- 让人类直接消费 JSON。
- 替代 Ren'Py 现有 self-voicing。
- 声称已经符合 WCAG 或完整无障碍标准。
- 声称当前 demo 已经是生产级 A11y 方案。
- 把 LLM 当成唯一目标用户。

这个项目 **是**：

- 让游戏运行时暴露开发者写入的语义真相。
- 让 LLM 作为适配器层，把语义转换成人类友好输出。
- 验证游戏可以被非视觉、非像素、非坐标的方式驱动。
- 为 screen reader、语音交互、键盘/开关设备、认知辅助、自动测试和非视觉游戏体验打基础。

## 核心架构

```text
Ren'Py runtime
  -> exports semantic state.json

LLM / assistive adapter
  -> reads semantic truth
  -> generates human-facing output or chooses an action
  -> writes action.json

Ren'Py runtime
  -> consumes semantic action
  -> advances game
```

关键点：

- `state.json` 是运行时语义状态，不是 OCR 结果。
- `actions[]` 是当前合法动作，不是坐标猜测。
- LLM 是适配器层，可以服务 Agent，也可以服务人类体验。
- 同一份语义可以生成不同输出：详细讲述、简短摘要、语音提示、自动测试动作、认知辅助说明。

## v0.2 验证内容

| 指标 | 结果 |
| --- | --- |
| 场景数 | 3 |
| 总 turn 数 | 16 |
| `advance` 动作 | 13 |
| `choice` 动作 | 3 |
| 最终状态 | `mode: "finished"` |
| 像素输入 | 无 |
| UI 自动化 | 无 |

文档：

- 愿景文档: [VISION.md](VISION.md)
- v0.2 英文 handoff: [docs/handoff-v0.2.md](docs/handoff-v0.2.md)
- v0.2 中文 handoff: [docs/handoff-v0.2.zh.md](docs/handoff-v0.2.zh.md)
- v0.2 英文验证记录: [docs/v0.2-validation.md](docs/v0.2-validation.md)
- v0.2 中文验证记录: [docs/v0.2-validation.zh.md](docs/v0.2-validation.zh.md)
- v0.3 规划交接: [docs/v0.3-plan.md](docs/v0.3-plan.md)
- JSON schema: [docs/schema.json](docs/schema.json)

## 仓库结构

```text
a11y_renpy_bridge/
├── agent/
│   └── simple_player.py        # Ollama 参考 Agent
├── game/
│   ├── a11y.rpy                # Ren'Py 侧桥接运行时
│   ├── script.rpy              # 3 场景 demo
│   └── exports/                # 运行时 JSON 文件
├── docs/                       # 协议、验证、规划文档
├── PROJECT_CONTEXT.md          # 当前项目上下文
├── VISION.md                   # 长期愿景
└── README.md
```

注意：文档不要放进 `game/` 目录。Ren'Py 会递归扫描 `game/**/*.rpy`，临时脚本副本可能污染 label 索引。

## 运行 v0.2 验证

清理旧状态：

```bash
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/state.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/action.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/choice.txt
```

通过 Ren'Py Launcher 或 SDK 启动项目根目录：

```text
D:\02_Dev\Projects\Games\a11y_renpy_bridge
```

然后在 WSL2 中运行 Agent：

```bash
cd /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/agent
python3 simple_player.py
```

期望最终输出：

```text
=== turn 16 | The End ===
Mode: finished
Text: Agent behavior logged.
Actions: []
Game finished.
```

## v0.2 已知限制

这些限制不推翻 v0.2 的验证结论：

- Ren'Py UI 会因为阻塞等待看起来卡住。
- 每次干净运行前需要清理 `game/exports/*`。
- 尚无 `session_id`。
- 尚无完善的 Ollama 超时、JSON 格式错误 retry/fallback。
- choice turn 会复用上一句 `narrative.current_text` 作为上下文。
- 当前只覆盖视觉小说式对白和菜单动作。

## v0.3 方向

v0.3 不扩展成完整 A11y 标准，也不追求 LLM 智能性。

v0.3 主题是：

```text
Runtime Health
```

目标是让 v0.2 的桥接闭环变得：

- session-safe
- non-blocking
- observable
- failure-aware

详见 [docs/v0.3-plan.md](docs/v0.3-plan.md)。
