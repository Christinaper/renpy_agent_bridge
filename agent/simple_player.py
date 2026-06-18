# agent/simple_player.py
import json
import os
import re
# import subprocess
import requests
import time
import argparse

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
print("__file__ =", __file__)
print("cwd =", Path.cwd())

print("sys.path:")
for p in sys.path:
    print(repr(p))

from config import resolve_session, get_paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "game" / "exports"
# STATE_PATH = EXPORT_DIR / "state.json"
# ACTION_PATH = EXPORT_DIR / "action.json"
LEGACY_CHOICE_PATH = EXPORT_DIR / "choice.txt"
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
AGENT_STATE_TIMEOUT = 120
AGENT_LLM_TIMEOUT   = 60
MAX_ERRORS          = 5

# def read_state():
#     """读取游戏状态"""
#     with open(STATE_PATH, "r", encoding="utf-8") as f:
#         return json.load(f)

def wait_for_state(paths, last_turn_id=None, timeout=AGENT_STATE_TIMEOUT):
    deadline = time.time() + timeout
    """等待Ren'Py导出新的可用状态"""
    while True:
        if time.time() > deadline:
            return None
        try:
            # state = read_state()
            with open(paths["state"], "r", encoding="utf-8") as f:
                state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.2)
            continue

        if "turn_id" not in state or "mode" not in state:
            time.sleep(0.2)
            continue

        if last_turn_id is None or state.get("turn_id") != last_turn_id:
            return state

        time.sleep(0.2)


def ask_ollama(prompt, timeout=AGENT_LLM_TIMEOUT):
    """调用Ollama HTTP API获取决策"""
    try:
        resp = requests.post(
            "%s/api/generate" % OLLAMA_API_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.Timeout:
        print("[LLM TIMEOUT] ollama 在 %ss 内未响应" % timeout)
        return None
    except requests.exceptions.ConnectionError:
        print("[LLM ERROR] 无法连接 Ollama API (%s)，请确认服务已启动" % OLLAMA_API_URL)
        return None
    except requests.exceptions.RequestException as e:
        print("[LLM ERROR] %s" % e)
        return None

def fallback_action(state):
    actions = state.get("actions", [])
    if not actions:
        return None
    if len(actions) == 1 and actions[0].get("type") == "advance":
        return actions[0]
    for a in actions:
        if a.get("type") == "choice":
            print("[FALLBACK] LLM 不可用，选择第一个 choice: %s" % a.get("text"))
            return a
    return actions[0]

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
    if response is None:
        return fallback_action(state)
    action_index = parse_action_index(response, len(actions))
    return actions[action_index]

def write_action(turn_id, action, paths):
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

    action_path = paths["action"]
    tmp_path = action_path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, action_path)


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
    print(f"[DEBUG] full narrative dict: {narrative}")   # ← 临时加这一行，无条件打印

    if "semantic" in narrative or "author_note" in narrative:
        print(f"[SEMANTIC] {narrative.get('semantic')}")
        print(f"[AUTHOR_NOTE] {narrative.get('author_note')}")

def play_loop(paths):
    """持续游玩, 直到Ren'Py导出finished状态"""
    clear_legacy_choice_file()

    print(f"Using Ollama model: {MODEL}")
    print("State:  %s" % paths["state"])
    print("Action: %s" % paths["action"])
    print("Session: %s" % paths["state"].stem.replace("state_", ""))

    last_turn_id = None
    consecutive_err = 0

    while True:
        state = wait_for_state(paths, last_turn_id)
        if state is None:
            session_id = paths["state"].stem.replace("state_", "")
            print("[FATAL] session %s 已失联（%ss 无更新，可能游戏已重启或关闭）" % (session_id, AGENT_STATE_TIMEOUT))
            print("[FATAL] Agent 不会自动切换 session")
            print("[FATAL] 如需连接新 session, 请重新运行: python simple_player.py")
            break
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
            consecutive_err += 1
            print("[ERROR] 连续错误 %d/%d" % (consecutive_err, MAX_ERRORS))
            if consecutive_err >= MAX_ERRORS:
                print("[ERROR] 连续错误过多，退出")
                break
            time.sleep(1.0)
            continue
        consecutive_err = 0

        print(f"Agent action: {action.get('type')} - {action.get('text', action.get('id'))}")
        write_action(state["turn_id"], action, paths)
        last_turn_id = state.get("turn_id")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", help="Session ID (留空则自动检测)")
    args = parser.parse_args()

    session_id = resolve_session(args.session)
    if session_id is None:
        print("等待游戏启动...")
        # 轮询直到 state_*.json 出现
        while session_id is None:
            time.sleep(0.5)
            session_id = resolve_session()

    paths = get_paths(session_id)
    print("Session: %s" % session_id)

    play_loop(paths)

if __name__ == "__main__":
    main()
