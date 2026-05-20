# A11y-RenPy-Bridge Handoff

## Current Milestone

**v0.2: Semantic JSON Loop Verified**

This milestone validates the core idea of the project: a game runtime can expose semantic state and available actions as JSON, and an external agent can complete a full playthrough by writing structured actions back to the game. The verified path does not use screen vision, OCR, mouse coordinates, or UI automation.

This is an accessibility-infrastructure proof of concept, not a production-ready assistive client.

## What Was Proven

The current Ren'Py demo can be completed through this loop:

1. Ren'Py exports `game/exports/state.json`.
2. Agent reads `turn_id`, `mode`, `scene`, `narrative`, and `actions`.
3. Agent writes `game/exports/action.json`.
4. Ren'Py consumes `action.json`, deletes it, and advances.
5. Ren'Py eventually exports `mode: "finished"`.
6. Agent exits normally.

Validation evidence is in [game/docs/v0.2-validation.md](game/docs/v0.2-validation.md).

Observed successful run:

- Total turns: 16
- Dialogue advance actions: 13
- Choice actions: 3
- Final state: `mode == "finished"`
- No pixel input required

## Protocol Shape

State file:

```text
game/exports/state.json
```

Important fields:

- `schema_version`: currently `0.2`
- `turn_id`: monotonic turn number within a run
- `mode`: `idle`, `awaiting_action`, or `finished`
- `scene`: semantic scene metadata
- `narrative`: current text and speaker
- `actions`: available semantic actions
- `choices`: compatibility view of choice actions
- `player_state`: history and current semantic label

Action file:

```text
game/exports/action.json
```

For dialogue advance:

```json
{
  "turn_id": 1,
  "action": {
    "id": "advance",
    "type": "advance"
  }
}
```

For choices:

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

Schema reference:

```text
game/docs/schema.json
```

## Important Files

- `game/a11y.rpy`: bridge runtime, state export, action consumption, `agent_say`, `agent_choice`, `a11y_finish`
- `game/script.rpy`: demo game using the bridge
- `agent/simple_player.py`: WSL2/Ollama reference agent
- `game/docs/schema.json`: v0.2 state schema
- `game/docs/v0.2-validation.md`: validation notes and run result

## How To Reproduce

Clear stale export files before each v0.2 run:

```bash
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/state.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/action.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/choice.txt
```

Start the Ren'Py game, click Start, then run the agent from WSL2:

```bash
cd /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/agent
python3 simple_player.py
```

Expected result:

```text
=== turn 16 | The End ===
Mode: finished
Actions: []
Game finished.
```

## Current Health

Healthy for v0.2's goal:

- JSON semantic loop works end to end.
- Dialogue can be represented as `advance`.
- Menus can be represented as `choice`.
- The agent can complete a full playthrough.
- `finished` lets the agent stop cleanly.

Not healthy for runtime usability yet:

- The Ren'Py UI appears frozen during agent waits.
- Startup order is fragile if stale `state.json` remains.
- There is no `session_id`.
- There is no retry/fallback policy for Ollama failures.
- There is no debug overlay or heartbeat.

## Known Limitations

These are accepted for v0.2 and should not block the milestone:

- Manual cleanup of `game/exports/*` is required before a clean run.
- Blocking wait uses sleep inside Ren'Py-side logic, so the game window may look unresponsive.
- `narrative.current_text` may repeat between a dialogue turn and the following choice turn because the choice reuses the previous text as context.
- Agent error recovery is minimal.
- Only two action types exist: `advance` and `choice`.

## A11y Direction

This project is on the accessibility-infrastructure path because it moves interaction away from pixels and toward runtime-owned semantics:

- The game exposes what is happening.
- The game exposes what actions are valid.
- The assistive client chooses from semantic actions instead of guessing screen coordinates.

LLM control is only one reference client. The same interface should eventually support screen readers, keyboard-only clients, switch-access clients, test bots, and cognitive assistance tools.

## v0.3 Recommended Scope

**v0.3: Runtime Health**

Recommended work:

- Add `session_id` to isolate runs and avoid stale state.
- Replace blocking waits with Ren'Py-friendly non-blocking waits using `pause`.
- Add a debug overlay showing `mode`, `turn_id`, text, and actions.
- Add timeout/error modes instead of silent blocking.
- Add basic agent retry/fallback for Ollama timeout and invalid JSON.
- Decide whether choice turns should carry a dedicated prompt text instead of reusing `narrative.current_text`.

Avoid expanding v0.3 into full accessibility semantics. Richer semantics should be a later phase after runtime health is stable.

## Milestone Boundary

v0.2 should be considered complete when the handoff state is accepted:

```text
Semantic JSON Loop Verified
```

The next work should start from v0.3 rather than continuing to add robustness requirements to v0.2.
