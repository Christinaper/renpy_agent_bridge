# agent/config.py

import os
import glob
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR   = PROJECT_ROOT / "game" / "exports"

def resolve_session(session_arg=None):
    """
    解析当前要跟踪的 session。
    优先级：命令行参数 > 环境变量 > 自动检测最新
    """
    if session_arg:
        return session_arg

    env_session = os.environ.get("BRIDGE_SESSION")
    if env_session:
        return env_session

    # 自动检测：找最新的 state_*.json
    pattern = str(EXPORT_DIR / "state_*.json")
    files = glob.glob(pattern)
    if not files:
        return None  # 游戏还没启动

    latest = max(files, key=os.path.getctime)
    # 从文件名提取 session_id
    # state_a3f4b2c1.json → a3f4b2c1
    stem = Path(latest).stem          # "state_a3f4b2c1"
    sid  = stem.replace("state_", "") # "a3f4b2c1"
    return sid

def get_paths(session_id):
    return {
        "state":  EXPORT_DIR / f"state_{session_id}.json",
        "action": EXPORT_DIR / f"action_{session_id}.json",
    }