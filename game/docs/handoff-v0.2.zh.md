# v0.2 交接文档：Semantic JSON Loop Proof

## 里程碑

**阶段:** Bridge Prototype  
**版本:** v0.2  
**状态:** JSON 语义闭环验证完成  
**日期:** 2026-05-15

本阶段验证一个窄而关键的命题：

> 游戏运行时可以把语义状态和可执行动作暴露为 JSON，让外部辅助客户端不依赖像素、OCR、鼠标坐标或 UI 自动化也能推进游戏。

v0.2 不是项目最终形态。它是桥接原型：Ren'Py 导出 JSON，Agent 读写文件，游戏通过语义动作完成一轮流程。

## 本阶段真正验证的是什么

这个项目不应被描述成“让 LLM 玩一个 Ren'Py demo”。Demo 只是最小测试场。

真正验证的是 infra 层 A11y 思路：

- A11y 应该在游戏/运行时层实现。
- 游戏应该暴露正在发生什么。
- 游戏应该暴露当前合法动作。
- 辅助技术应该选择语义动作，而不是从渲染像素中猜测。

LLM Agent 只是一个参考客户端，不是 A11y 层本身。

## 已验证闭环

1. Ren'Py 发布 `game/exports/state.json`。
2. Agent 读取 `turn_id`、`mode`、`scene`、`narrative` 和 `actions`。
3. Agent 选择一个动作。
4. Agent 写入 `game/exports/action.json`。
5. Ren'Py 消费并删除 `action.json`，推进剧情。
6. Ren'Py 导出下一轮状态。
7. 当 `mode` 变成 `finished` 时，Agent 正常退出。

v0.2 观测结果：

| 指标 | 结果 |
| --- | --- |
| 场景数 | 3 |
| 总 turn 数 | 16 |
| `advance` 动作 | 13 |
| `choice` 动作 | 3 |
| 最终 mode | `finished` |
| 像素输入 | 无 |
| UI 自动化 | 无 |

## 协议文件

状态文件：

```text
game/exports/state.json
```

动作文件：

```text
game/exports/action.json
```

Schema：

```text
game/docs/schema.json
```

## state.json 形态

```json
{
  "schema_version": "0.2",
  "timestamp": "2026-05-15T14:30:22.123456",
  "turn_id": 3,
  "mode": "awaiting_action",
  "scene": {
    "id": "room",
    "name": "The Room",
    "description": "A minimal space with one object",
    "accessibility": {
      "visual_description": "A gray room with a square object in the center",
      "audio_cues": [],
      "complexity": "low"
    }
  },
  "narrative": {
    "current_text": "There is an object here.",
    "speaker": null
  },
  "actions": [
    {
      "id": "choice_000",
      "type": "choice",
      "index": 0,
      "text": "Interact with object",
      "semantic_label": "engage",
      "cognitive_load": "low"
    }
  ],
  "player_state": {
    "history": [],
    "current_label": "room"
  }
}
```

## action.json 形态

推进对白：

```json
{
  "turn_id": 1,
  "action": {
    "id": "advance",
    "type": "advance"
  }
}
```

选择菜单：

```json
{
  "turn_id": 3,
  "action": {
    "id": "choice_000",
    "type": "choice",
    "index": 0
  }
}
```

## 关键文件

- `game/a11y.rpy`: 桥接运行时、状态导出、动作消费、`agent_say`、`agent_choice`、`a11y_finish`
- `game/script.rpy`: 3 场景 demo
- `agent/simple_player.py`: 使用 Ollama 的参考 Agent
- `game/docs/schema.json`: v0.2 schema
- `game/docs/v0.2-validation.md`: 英文验证记录
- `game/docs/v0.2-validation.zh.md`: 中文验证记录

## 复现方式

清理旧运行时文件：

```bash
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/state.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/action.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/choice.txt
```

通过 Ren'Py launcher 或 SDK 启动项目。

在 WSL2 中运行 Agent：

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

## v0.2 健康状态

对 v0.2 目标来说是健康的：

- JSON 语义闭环完整跑通。
- 普通对白可表示为 `advance`。
- 菜单选项可表示为 `choice`。
- Agent 可以不依赖像素输入完成 demo。
- `finished` 可以让 Agent 正常退出。

但还不是健康的运行时：

- Ren'Py UI 在等待 Agent 时可能看起来卡住。
- 如果存在旧 export 文件，启动顺序很脆弱。
- 没有 `session_id`。
- 没有完善的 Ollama/JSON retry 或 fallback。
- 没有 debug overlay 或 heartbeat。

## v0.2 可接受限制

这些不是 v0.2 阻塞项：

- 每次干净运行前需要手动清理 `game/exports/*`。
- 当前等待逻辑会阻塞 Ren'Py 主线程。
- choice turn 会复用上一句 `narrative.current_text` 作为上下文。
- 目前只有 `advance` 和 `choice` 两类动作。
- 原型只覆盖视觉小说式对白和菜单选择。

## 阶段边界

v0.2 应收口为：

```text
Semantic JSON Loop Proof Validated
```

不要继续把运行时健康要求塞进 v0.2。它们应进入 v0.3。

## v0.3 建议范围

**主题:** Runtime Health

推荐事项：

- 增加 `session_id`。
- 用 Ren'Py 友好的非阻塞等待替代阻塞等待。
- 增加 debug overlay，显示 `mode`、`turn_id`、当前文本和可用动作。
- 增加 timeout 和 error mode。
- 增加基础 Agent retry/fallback。
- 增加明确的 choice context。

更丰富的 A11y 语义、作者工具、多引擎支持和真实辅助客户端，应放在 bridge runtime 健康之后。

## 对应文档

- 英文 handoff: `game/docs/handoff-v0.2.md`
- 英文验证记录: `game/docs/v0.2-validation.md`
- 中文验证记录: `game/docs/v0.2-validation.zh.md`
