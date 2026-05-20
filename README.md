# A11y-RenPy-Bridge

**A bridge prototype for game accessibility infrastructure.**

This project is not trying to prove that an LLM can play one Ren'Py demo. It validates a broader hypothesis:

> Games should natively expose semantic state and executable actions, so assistive technologies do not have to guess the game through screen pixels.

v0.2 proves a narrow but important loop: a Ren'Py game exports semantic JSON, an external agent reads it, writes a structured action, and the game advances to completion without vision, OCR, mouse coordinates, or UI automation.

## Status

**Current milestone:** v0.2 Semantic JSON Loop Proof
**Stage:** Bridge Prototype
**Validated:** Yes, on a 3-scene Ren'Py demo with 16 turns

This is not the final form of the project. It is the first bridge prototype: file-based JSON, one Ren'Py demo, one Ollama-backed reference agent.

## Why This Matters

Most game accessibility tooling is forced to work from the outside: inspect pixels, infer UI state, emulate clicks, and hope the screen did not change. That is fragile.

This project explores a different direction:

- The game runtime owns the truth.
- The game exports semantic state.
- The game exports valid actions.
- Assistive clients choose from those actions.

LLM play is only one reference client. The same interface should eventually support screen readers, keyboard-only clients, switch-access clients, test bots, cognitive assistance tools, and other accessibility clients.

## What v0.2 Proves

The validated loop is:

1. Ren'Py writes `game/exports/state.json`.
2. Agent reads `turn_id`, `mode`, `scene`, `narrative`, and `actions`.
3. Agent writes `game/exports/action.json`.
4. Ren'Py consumes the action and advances.
5. The loop repeats until Ren'Py exports `mode: "finished"`.
6. Agent exits cleanly.

Validation result:

| Metric | Result |
| --- | --- |
| Total turns | 16 |
| Advance actions | 13 |
| Choice actions | 3 |
| Final mode | `finished` |
| Pixel input | None |
| UI automation | None |

Full reports:

- English handoff: [docs/handoff-v0.2.md](docs/handoff-v0.2.md)
- Chinese handoff: [docs/handoff-v0.2.zh.md](docs/handoff-v0.2.zh.md)
- English validation: [docs/v0.2-validation.md](docs/v0.2-validation.md)
- Chinese validation: [docs/v0.2-validation.zh.md](docs/v0.2-validation.zh.md)
- Schema: [docs/schema.json](docs/schema.json)

## Repository Layout

```text
a11y_renpy_bridge/
├── agent/
│   └── simple_player.py        # Reference agent using Ollama
├── game/
│   ├── a11y.rpy                # Bridge runtime
│   ├── script.rpy              # Demo game
│   └── exports/                # Runtime JSON files, ignored by git
├── docs/                       # Protocol and validation docs
├── PROJECT_CONTEXT.md          # Short Chinese project context
└── README.md
```

## Requirements

Ren'Py side:

- Ren'Py 8.x
- The demo project opened through the Ren'Py launcher or SDK

Agent side:

- Python 3.8+
- Ollama
- `llama3.2:1b` model, or another model via `OLLAMA_MODEL`

The reference agent currently uses only the Python standard library. There is no `requirements.txt`.

Keep documentation outside `game/`. Ren'Py recursively scans `game/` for `.rpy` scripts, so scratch copies such as `game/docs/copy.rpy` can corrupt script indexing.

## Run The v0.2 Proof

Clear stale runtime files before each v0.2 run:

```bash
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/state.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/action.json
rm -f /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/game/exports/choice.txt
```

Start the Ren'Py project from the Ren'Py launcher or your local SDK.

Then run the agent from WSL2:

```bash
cd /mnt/d/02_Dev/Projects/Games/a11y_renpy_bridge/agent
python3 simple_player.py
```

Expected final output:

```text
=== turn 16 | The End ===
Mode: finished
Text: Agent behavior logged.
Actions: []
Game finished.
```

## Protocol Snapshot

`state.json`:

```json
{
  "schema_version": "0.2",
  "turn_id": 3,
  "mode": "awaiting_action",
  "scene": {
    "id": "room",
    "name": "The Room"
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
      "semantic_label": "engage"
    }
  ],
  "player_state": {
    "history": [],
    "current_label": "room"
  }
}
```

`action.json`:

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

Action types in v0.2:

- `advance`: continue dialogue
- `choice`: select a menu option by `index`

## Known v0.2 Limits

These do not invalidate the v0.2 proof:

- Ren'Py UI can appear frozen because the current wait loop blocks the main thread.
- Stale `game/exports/*` files must be cleared before a clean run.
- There is no `session_id`.
- There is no robust Ollama retry/fallback policy.
- Choice turns reuse the previous `narrative.current_text` as context, which is acceptable for the proof but should be improved for data quality.
- The prototype only covers visual-novel style dialogue and menu choice actions.

## Next Stage

Recommended v0.3 theme:

**Runtime Health**

Likely work:

- Add `session_id`.
- Replace blocking waits with Ren'Py-friendly non-blocking waits.
- Add a debug overlay for `mode`, `turn_id`, text, and actions.
- Add timeout/error modes.
- Add basic agent retry/fallback.
- Add richer choice context.

Richer accessibility semantics, authoring tools, and multi-engine support should come after the bridge runtime is healthy.

## License

License is not finalized in this repository yet.
