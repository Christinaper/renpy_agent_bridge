# 🎮 A11y-RenPy-Bridge

**Make visual novels accessible to AI agents and assistive technologies through semantic JSON interfaces.**

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/yourusername/a11y-renpy-bridge/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Ren'Py](https://img.shields.io/badge/Ren'Py-8.3%2B-red.svg)](https://www.renpy.org/)

> 🎯 **Core Idea:** Instead of using pixel-based vision and UI automation, expose game narrative and player actions as structured JSON, enabling LLM agents to play visual novels through semantic understanding.

---

## 🌟 What This Is

A **technical validation** that proves visual novels can be played entirely through a JSON API, without:
- ❌ Computer vision
- ❌ Screen reading
- ❌ Mouse/keyboard automation
- ❌ Pixel-level input

Instead:
- ✅ Game exports semantic state (scene, dialogue, available actions)
- ✅ Agent reads JSON and makes decisions via LLM
- ✅ Game consumes agent's choice and progresses

**Result:** Full playthrough of a 3-scene demo (16 turns) with 100% success rate.

---

## 🎬 Quick Demo

```bash
# Terminal 1: Start Ren'Py game
./renpy.exe game

# Terminal 2: Start AI agent
cd agent
python3 simple_player.py
```

**Agent output:**
=== turn 1 | The Room ===
Text: You are in a room.
Actions: ['Continue']
Agent action: advance - Continue
=== turn 3 | The Room ===
Text:
Actions: ['Interact with object', 'Ignore object']
Agent action: choice - Interact with object
...
=== turn 16 | The End ===
Mode: finished
Game finished.

**[📺 Watch full demo video](#)** *(TODO: add link)*

---

## 🏗️ Architecture
┌─────────────────┐
│   Ren'Py Game   │
│   (script.rpy)  │
└────────┬────────┘
│ exports
↓
state.json
{
"turn_id": 3,
"mode": "awaiting_action",
"scene": {...},
"actions": [
{"type": "choice", "text": "Interact", "index": 0},
{"type": "choice", "text": "Ignore", "index": 1}
]
}
│ reads
↓
┌─────────────────┐
│   AI Agent      │
│  (LLM decision) │
└────────┬────────┘
│ writes
↓
action.json
{
"turn_id": 3,
"action": {"type": "choice", "index": 0}
}
│ consumes
↓
┌─────────────────┐
│   Ren'Py Game   │
│  (progresses)   │
└─────────────────┘

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## 📦 Installation

### Prerequisites

**Ren'Py side (Windows/Mac/Linux):**
- [Ren'Py 8.3+](https://www.renpy.org/latest.html)

**Agent side (Linux/WSL2):**
- Python 3.8+
- [Ollama](https://ollama.com/) with `llama3.2:1b` model

### Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/a11y-renpy-bridge.git
cd a11y-renpy-bridge

# 2. Install Ollama (if not already)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b

# 3. Install Python dependencies
cd agent
pip install -r requirements.txt

# 4. Clear exports directory (first run only)
rm -rf game/exports/*
mkdir -p game/exports
```

---

## 🚀 Usage

### Step 1: Start Ren'Py Game

**Option A: Via Ren'Py Launcher**
1. Open Ren'Py Launcher
2. Select `a11y-renpy-bridge` project
3. Click "Launch Project"

**Option B: Command Line**
```bash
# Windows
.\renpy.exe game

# Linux/Mac
./renpy.sh game
```

### Step 2: Start AI Agent

```bash
cd agent
python3 simple_player.py
```

### Step 3: Watch the Magic ✨

The agent will:
1. Read game state from `game/exports/state.json`
2. Call Ollama to make decisions
3. Write choices to `game/exports/action.json`
4. Repeat until game finishes

**Expected runtime:** 2-5 minutes (depends on LLM speed)

---

## 📊 V0.2 Validation Results

| Metric | Result |
|--------|--------|
| **Total turns** | 16 |
| **Advance actions** | 13 (auto-progress dialogue) |
| **Choice actions** | 3 (LLM decisions) |
| **Success rate** | 100% (no manual intervention) |
| **Turn progression** | Monotonic (1→16, no gaps) |
| **State machine** | Correct (awaiting_action → finished) |
| **LLM calls** | 3 (only for choices, performance optimized) |

See [docs/handoff-v0.2.md](docs/handoff-v0.2.md) for full report.

---

## 🎯 Use Cases

### 1. Accessibility
Enable screen reader users to play visual novels through semantic interfaces instead of OCR.

### 2. AI Research
- Benchmark LLM narrative understanding
- Study decision-making in story-driven games
- Generate training data for game AI

### 3. Automated Testing
Test game logic without manual playthrough or pixel-based automation.

### 4. Content Creation
Generate playthroughs for walkthroughs, reviews, or analysis.

---

## 🛠️ Technical Details

### JSON Schema

**state.json:**
```json
{
  "schema_version": "0.2",
  "turn_id": 3,
  "mode": "awaiting_action",
  "scene": {
    "id": "room",
    "name": "The Room",
    "description": "A minimal space with one object"
  },
  "narrative": {
    "current_text": "",
    "speaker": null
  },
  "actions": [
    {
      "id": "choice_000",
      "type": "choice",
      "index": 0,
      "text": "Interact with object"
    }
  ],
  "player_state": {
    "history": ["interact_room"],
    "current_label": "room"
  }
}
```

Full schema: [docs/schema.json](docs/schema.json)

### Action Types

- **`advance`**: Progress dialogue (like clicking "Continue")
- **`choice`**: Select from menu options (requires `index` field)

### Agent Decision Logic

```python
# Performance optimization: skip LLM for single advance actions
if len(actions) == 1 and actions[0]["type"] == "advance":
    return actions[0]

# Use LLM for choices
prompt = f"""Scene: {scene_name}
Available actions:
0. {action_0_text}
1. {action_1_text}

Respond with JSON: {{"action_index": 0}}"""

response = ask_ollama(prompt)
```

See [agent/simple_player.py](agent/simple_player.py) for full implementation.

---

## ⚠️ Known Limitations (v0.2)

### 🟡 UI Freeze During Turns
**Issue:** Ren'Py window becomes unresponsive while waiting for agent  
**Cause:** Blocking `time.sleep()` in main thread  
**Impact:** Cosmetic only, functionality works fine  
**Workaround:** Use separate terminal windows  
**Fix planned:** v0.3 will use threading

### 🟡 Manual Session Cleanup
**Issue:** Must delete `game/exports/*` before each run  
**Cause:** No session isolation  
**Impact:** Inconvenient startup  
**Workaround:** `rm -rf game/exports/*` before launch  
**Fix planned:** v0.3 will add session IDs to filenames

### 🟡 Empty narrative.current_text at Choice Points
**Issue:** Turn 3 (choice) shows empty text to avoid duplication with Turn 2  
**Impact:** Choice context not in JSON (but available in `actions[].text`)  
**Fix planned:** v0.3 will add `choice_context.preceding_text` field

See [docs/handoff-v0.2.md#known-limitations](docs/handoff-v0.2.md#known-limitations) for details.

---

## 🗺️ Roadmap

### ✅ v0.1 (Week 1)
- [x] JSON export from Ren'Py
- [x] 3-scene demo game
- [x] Schema definition

### ✅ v0.2 (Week 2)
- [x] AI agent integration
- [x] Full playthrough validation
- [x] Turn-based synchronization

### 🚧 v0.3 (Planned)
- [ ] Non-blocking UI (threading)
- [ ] Session ID isolation
- [ ] `choice_context` field for richer context
- [ ] Error recovery and retry logic
- [ ] Debug overlay UI

### 🔮 v0.4+ (Future)
- [ ] Multi-game support (plugin system)
- [ ] Web API instead of file polling
- [ ] Real-time dashboard
- [ ] Performance metrics

See [docs/v0.3-roadmap.md](docs/v0.3-roadmap.md) for detailed plan.

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

### Good First Issues
- [ ] Add more test games (different genres)
- [ ] Implement other LLM backends (GPT-4, Claude)
- [ ] Create visualization tools for playthrough logs
- [ ] Write tutorials for integrating with existing Ren'Py games

---

## 📚 Citation

If you use this in research, please cite:

```bibtex
@software{a11y_renpy_bridge_2026,
  author = {Your Name},
  title = {A11y-RenPy-Bridge: Semantic JSON Interface for Visual Novel Accessibility},
  year = {2026},
  url = {https://github.com/yourusername/a11y-renpy-bridge},
  version = {0.2.0}
}
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- [Ren'Py](https://www.renpy.org/) - Visual novel engine
- [Ollama](https://ollama.com/) - Local LLM runtime
- Inspired by accessibility research in interactive fiction

---

## 📞 Contact

- **Issues:** [GitHub Issues](https://github.com/yourusername/a11y-renpy-bridge/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/a11y-renpy-bridge/discussions)
- **Email:** your.email@example.com

---

## ⭐ Star History

If this project helps your research or development, please consider starring it!

---

*Built with ❤️ for accessibility and AI research*