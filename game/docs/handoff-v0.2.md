# v0.2 Handoff: Semantic JSON Loop Proof

## Milestone

**Stage:** Bridge Prototype  
**Version:** v0.2  
**Status:** Semantic JSON loop proof validated  
**Date:** 2026-05-15

This milestone validates a narrow but important claim:

> A game runtime can expose semantic state and executable actions as JSON, allowing an external assistive client to drive play without relying on pixels, OCR, mouse coordinates, or UI automation.

This is not the final project shape. v0.2 is the bridge prototype: Ren'Py exports JSON, an agent reads and writes files, and the game completes through semantic actions.

## What This Is Really Testing

The project should not be framed as "an LLM plays a Ren'Py demo." The demo is only the smallest testbed.

The tested infrastructure idea is:

- Accessibility should be implemented at the game/runtime layer.
- The game should expose what is happening.
- The game should expose what actions are valid.
- Assistive technologies should choose from semantic actions instead of guessing through rendered pixels.

The LLM agent is one reference client, not the accessibility layer itself.

## Proven Loop

1. Ren'Py publishes `game/exports/state.json`.
2. The agent reads `turn_id`, `mode`, `scene`, `narrative`, and `actions`.
3. The agent chooses an action.
4. The agent writes `game/exports/action.json`.
5. Ren'Py consumes `action.json`, deletes it, and advances.
6. Ren'Py exports the next state.
7. The loop ends when `mode` becomes `finished`.

Observed v0.2 run:

| Metric | Result |
| --- | --- |
| Scenes | 3 |
| Total turns | 16 |
| Advance actions | 13 |
| Choice actions | 3 |
| Final mode | `finished` |
| Pixel input | None |
| UI automation | None |

## Protocol Files

State:

```text
game/exports/state.json
```

Action:

```text
game/exports/action.json
```

Schema:

```text
game/docs/schema.json
```

## State Shape

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

## Action Shape

Advance:

```json
{
  "turn_id": 1,
  "action": {
    "id": "advance",
    "type": "advance"
  }
}
```

Choice:

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

## Important Files

- `game/a11y.rpy`: bridge runtime, exporter, action consumer, `agent_say`, `agent_choice`, `a11y_finish`
- `game/script.rpy`: 3-scene demo game
- `agent/simple_player.py`: reference agent using Ollama
- `game/docs/schema.json`: v0.2 schema
- `game/docs/v0.2-validation.md`: validation notes
- `game/docs/v0.2-validation.zh.md`: Chinese validation notes

## Reproduction

Clear stale runtime files:

```bash
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/state.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/action.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/choice.txt
```

Start the Ren'Py project through the Ren'Py launcher or SDK.

Run the agent from WSL2:

```bash
cd /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/agent
python3 simple_player.py
```

Expected final state:

```text
=== turn 16 | The End ===
Mode: finished
Text: Agent behavior logged.
Actions: []
Game finished.
```

## v0.2 Health

Healthy for the v0.2 goal:

- JSON semantic loop works end to end.
- Dialogue is represented as `advance`.
- Menu options are represented as `choice`.
- Agent completes the demo without pixel input.
- `finished` lets the agent exit cleanly.

Not yet healthy for runtime usability:

- Ren'Py UI can appear frozen while waiting for the agent.
- Startup is fragile if stale export files remain.
- There is no `session_id`.
- There is no robust retry/fallback policy for Ollama or malformed JSON.
- There is no debug overlay or heartbeat.

## Accepted v0.2 Limits

These are not v0.2 blockers:

- Manual cleanup of `game/exports/*` is required before a clean run.
- The current wait logic blocks Ren'Py's main thread.
- Choice turns reuse the previous `narrative.current_text` as context.
- Only `advance` and `choice` actions exist.
- The prototype only covers visual-novel style dialogue and menus.

## Milestone Boundary

v0.2 should be closed as:

```text
Semantic JSON Loop Proof Validated
```

Do not continue adding runtime-health requirements to v0.2. Start them under v0.3.

## Recommended v0.3 Scope

**Theme:** Runtime Health

Recommended items:

- Add `session_id`.
- Replace blocking waits with Ren'Py-friendly non-blocking waits.
- Add a debug overlay showing `mode`, `turn_id`, current text, and available actions.
- Add timeout and error modes.
- Add basic agent retry/fallback.
- Add explicit choice context.

Richer accessibility semantics, authoring tools, multi-engine support, and real assistive clients should come after the bridge runtime is healthy.

## Companion Documents

- Chinese handoff: `game/docs/handoff-v0.2.zh.md`
- English validation: `game/docs/v0.2-validation.md`
- Chinese validation: `game/docs/v0.2-validation.zh.md`
