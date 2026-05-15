# agent/simple_player.py
import json
import os
import re
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "game" / "exports"
STATE_PATH = EXPORT_DIR / "state.json"
ACTION_PATH = EXPORT_DIR / "action.json"
LEGACY_CHOICE_PATH = EXPORT_DIR / "choice.txt"
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")


def read_state():
    """读取游戏状态"""
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def wait_for_state(last_turn_id=None):
    """等待Ren'Py导出新的可用状态"""
    while True:
        try:
            state = read_state()
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.2)
            continue

        if "turn_id" not in state or "mode" not in state:
            time.sleep(0.2)
            continue

        if last_turn_id is None or state.get("turn_id") != last_turn_id:
            return state

        time.sleep(0.2)


def ask_ollama(prompt):
    """调用Ollama获取决策"""
    result = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ollama run failed")
    return result.stdout.strip()


def parse_action_index(response, action_count):
    """从LLM响应中解析动作下标"""
    try:
        data = json.loads(response)
        idx = int(data.get("action_index", 0))
        if 0 <= idx < action_count:
            return idx
    except Exception:
        pass

    json_match = re.search(r"\{.*\}", response, flags=re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            idx = int(data.get("action_index", 0))
            if 0 <= idx < action_count:
                return idx
        except Exception:
            pass

    number_match = re.search(r"\d+", response)
    if number_match:
        idx = int(number_match.group(0))
        if 0 <= idx < action_count:
            return idx

    return 0


def choose_action(state):
    """选择一个语义动作。单一advance动作无需调用LLM。"""
    actions = state.get("actions", [])
    if not actions:
        return None

    if len(actions) == 1 and actions[0].get("type") == "advance":
        return actions[0]

    prompt = f"""You are playing a Ren'Py game through an accessibility interface.
Choose exactly one available action.

Scene: {state['scene']['name']}
Text: {state['narrative'].get('current_text', '')}

Actions:
"""
    for idx, action in enumerate(actions):
        semantic = action.get("semantic_label", "")
        suffix = f" [{semantic}]" if semantic else ""
        prompt += f"{idx}. {action.get('text', action.get('id', ''))}{suffix}\n"

    prompt += '\nRespond with JSON only: {"action_index": 0}'

    response = ask_ollama(prompt)
    action_index = parse_action_index(response, len(actions))
    return actions[action_index]


def write_action(turn_id, action):
    """原子写入Agent动作"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "turn_id": turn_id,
        "action": {
            "id": action.get("id"),
            "type": action.get("type"),
        },
    }

    if action.get("type") == "choice":
        payload["action"]["index"] = action.get("index", 0)

    tmp_path = ACTION_PATH.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, ACTION_PATH)


def clear_legacy_choice_file():
    """避免旧choice.txt干扰0.2协议观察"""
    if LEGACY_CHOICE_PATH.exists():
        LEGACY_CHOICE_PATH.unlink()


def describe_state(state):
    scene = state.get("scene", {})
    narrative = state.get("narrative", {})
    actions = state.get("actions", [])

    print(f"\n=== turn {state.get('turn_id')} | {scene.get('name', 'Unknown')} ===")
    print(f"Mode: {state.get('mode')}")
    print(f"Text: {narrative.get('current_text', '')}")
    print(f"Actions: {[a.get('text', a.get('id')) for a in actions]}")


def play_loop():
    """持续游玩，直到Ren'Py导出finished状态"""
    clear_legacy_choice_file()

    print(f"Using Ollama model: {MODEL}")
    print(f"State: {STATE_PATH}")
    print(f"Action: {ACTION_PATH}")

    last_turn_id = None

    while True:
        state = wait_for_state(last_turn_id)
        describe_state(state)

        mode = state.get("mode")
        if mode == "finished":
            print("Game finished.")
            break

        if mode != "awaiting_action":
            last_turn_id = state.get("turn_id")
            continue

        action = choose_action(state)
        if action is None:
            print("No available actions. Stopping.")
            break

        print(f"Agent action: {action.get('type')} - {action.get('text', action.get('id'))}")
        write_action(state["turn_id"], action)
        last_turn_id = state.get("turn_id")


if __name__ == "__main__":
    play_loop()
