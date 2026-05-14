# agent/simple_player.py
import json
import re
import subprocess
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = PROJECT_ROOT / "game" / "exports" / "state.json"
CHOICE_PATH = PROJECT_ROOT / "game" / "exports" / "choice.txt"
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

def read_state():
    """读取游戏状态"""
    with open(STATE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def ask_ollama(prompt):
    """调用Ollama获取决策"""
    result = subprocess.run(
        ['ollama', 'run', MODEL, prompt],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ollama run failed")
    return result.stdout.strip()

def make_decision(state):
    """
    技术验证版决策：
    - 不追求智能
    - 只验证流程
    """
    choices = state['choices']
    
    # 构造最简prompt
    prompt = f"""You are playing a text game.

Scene: {state['scene']['name']}
Text: {state['narrative']['current_text']}

Available choices:
"""
    for i, choice in enumerate(choices):
        prompt += f"{i}: {choice['text']}\n"
    
    prompt += "\nRespond with ONLY the number of your choice (0, 1, or 2). No explanation."
    
    # 调用LLM
    response = ask_ollama(prompt)
    
    # 解析响应（容错）
    match = re.search(r"\d+", response)
    if match:
        choice_num = int(match.group(0))
        if 0 <= choice_num < len(choices):
            return choice_num
    
    # 失败时随机选择
    return 0

def write_choice(choice_index):
    """写入选择文件"""
    CHOICE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHOICE_PATH, 'w') as f:
        f.write(str(choice_index))

def play_one_turn():
    """执行一轮决策"""
    state = read_state()
    choices = state.get('choices', [])

    if not choices:
        print(f"\n=== {state['scene']['name']} ===")
        print("No choices available. Game may be finished.")
        return False
    
    print(f"\n=== {state['scene']['name']} ===")
    print(f"Text: {state['narrative']['current_text']}")
    print(f"Choices: {[c['text'] for c in choices]}")
    
    decision = make_decision(state)
    
    print(f"Agent chose: {decision} - {choices[decision]['text']}")
    
    write_choice(decision)
    print("Choice written. Waiting for Ren'Py...")
    return True

def wait_for_next_state(last_timestamp):
    """等待Ren'Py消费选择并导出下一帧状态"""
    start = time.time()
    while time.time() - start < 45:
        if CHOICE_PATH.exists():
            time.sleep(0.2)
            continue

        try:
            state = read_state()
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.2)
            continue

        if state.get("timestamp") != last_timestamp:
            return True

        time.sleep(0.2)

    return False

def play_loop():
    """持续游玩，直到游戏导出无选项状态或等待超时"""
    print(f"Using Ollama model: {MODEL}")
    print(f"State: {STATE_PATH}")

    while True:
        state = read_state()
        last_timestamp = state.get("timestamp")

        if not play_one_turn():
            break

        if not wait_for_next_state(last_timestamp):
            print("Timed out waiting for Ren'Py to advance.")
            break

if __name__ == "__main__":
    play_loop()
