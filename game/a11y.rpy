# game/a11y.rpy
# A11y-RenPy-Bridge: Accessibility Export Module
# Version: 0.2
# Purpose: Export semantic game state and consume semantic agent actions.

init python:
    import json
    import os
    import time
    from datetime import datetime
    import uuid
    import threading

    a11y_turn_id = 0
    a11y_mode = "idle"
    current_actions = []
    session_id = str(uuid.uuid4())[:8]  # 例如: "a3f4b2c1"

    class A11yExporter:
        """
        Export Ren'Py game state to structured JSON.
        Enables assistive clients and AI agents to play without pixel-level vision.
        """

        def __init__(self):
            self.version = "0.3"
            self.export_dir_base = os.path.join(renpy.config.gamedir, "exports")
            self.export_dir = self.export_dir_base
            self.ensure_export_dir()
            self._update_paths()
        
        def _update_paths(self):
            # session_id 从 store 读取（init python 里已经生成）
            sid = getattr(store, "session_id", "default")

            # 文件路径带 session_id
            self.state_file  = os.path.join(self.export_dir, "state_%s.json"  % sid)
            self.action_file = os.path.join(self.export_dir, "action_%s.json" % sid)
            # legacy 路径保留用于兼容性检测
            self.legacy_choice_file = os.path.join(self.export_dir, "choice.txt")

            print("store.session_id =", getattr(store, "session_id", None))
            print("state_file =", self.state_file)

        def ensure_export_dir(self):
            if not os.path.exists(self.export_dir):
                os.makedirs(self.export_dir)

        def reset_session(self):
            store.session_id = str(uuid.uuid4())[:8]
            self._update_paths()
            store.a11y_turn_id = 0
            store.a11y_mode = "idle"
            store.current_actions = []
            store.current_narrative = ""
            store.menu_items = []

            for path in (self.state_file, self.action_file, self.legacy_choice_file):
                if os.path.exists(path):
                    os.remove(path)

        def export_state(self):
            return {
                "schema_version": self.version,
                "timestamp": datetime.now().isoformat(),
                "turn_id": getattr(store, "a11y_turn_id", 0),
                "mode": getattr(store, "a11y_mode", "idle"),
                "scene": self._export_scene(),
                "narrative": self._export_narrative(),
                "actions": self._export_actions(),
                "choices": self._export_choices(),
                "player_state": self._export_player_state(),
            }

        def _export_scene(self):
            scene_id = getattr(store, "current_scene_id", "unknown")
            scene_data = getattr(store, "scenes", {}).get(scene_id, {})

            return {
                "id": scene_id,
                "name": scene_data.get("name", "Unnamed Scene"),
                "description": scene_data.get("description", ""),
                "accessibility": {
                    "visual_description": scene_data.get("visual_desc", ""),
                    "audio_cues": scene_data.get("audio_cues", []),
                    "complexity": scene_data.get("complexity", "low"),
                },
            }

        def _export_narrative(self):
            # 追加语义字段 semantic
            base = {
                "current_text": getattr(store, "current_narrative", ""),
                "speaker":      getattr(store, "current_speaker",   None),
            }
            semantic = getattr(store, "_semantic_ctx", None)
            if semantic:
                base["semantic"] = semantic
            author_note = getattr(store, "_author_note", None)
            if author_note:
                base["author_note"] = author_note
            return base

        def _export_actions(self):
            # return list(getattr(store, "current_actions", []))
            # 重写（规范化 + 语义字段）
            raw_actions = list(getattr(store, "current_actions", []))
            result = []
            for action in raw_actions:
                entry = {
                    "id":   action.get("id",   ""),
                    "type": action.get("type", ""),
                    "text": action.get("text", ""),
                }
                if action.get("type") == "choice":
                    entry["index"] = action.get("index", 0)
                for field in ("semantic_label", "cognitive_load",
                            "consequence_hint", "emotional_weight"):
                    val = action.get(field)
                    if val:
                        entry[field] = val
                result.append(entry)
            return result

        def _export_choices(self):
            choices = []
            for action in getattr(store, "current_actions", []):
                if action.get("type") != "choice":
                    continue

                choices.append({
                    "id": action.get("id", "choice_%03d" % len(choices)),
                    "text": action.get("text", ""),
                    "accessibility": {
                        "semantic_label": action.get("semantic_label", ""),
                        "cognitive_load": action.get("cognitive_load", "medium"),
                    },
                })

            return choices

        def _export_player_state(self):
            return {
                "history": getattr(store, "choice_history", []),
                "current_label": getattr(store, "current_scene_id", "unknown"),
            }

        def save_to_file(self):
            state = self.export_state()
            filepath = self.state_file
            tmp_path = filepath + ".tmp"

            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            os.replace(tmp_path, filepath)
            return filepath

        def publish(self, mode, actions):
            store.a11y_turn_id = getattr(store, "a11y_turn_id", 0) + 1
            store.a11y_mode = mode
            store.current_actions = actions
            return self.save_to_file()

        def wait_for_action(self, timeout=30.0):
            deadline = time.time() + timeout

            while time.time() < deadline:
                if not os.path.exists(self.action_file):
                    time.sleep(0.2)
                    continue

                try:
                    with open(self.action_file, "r", encoding="utf-8") as f:
                        action = json.load(f)
                except Exception:
                    time.sleep(0.2)
                    continue
                finally:
                    if os.path.exists(self.action_file):
                        os.remove(self.action_file)

                if action.get("turn_id") == getattr(store, "a11y_turn_id", 0):
                    return action

            return None

    a11y = A11yExporter()

    class ActionWatcher:
        """
        在后台线程轮询 action 文件。
        主线程通过 is_ready() 和 get_result() 获取结果。
        不调用任何 renpy.* API。
        """

        def __init__(self, action_file, expected_turn_id, timeout=60.0):
            self.action_file      = action_file
            self.expected_turn_id = expected_turn_id
            self.timeout          = timeout

            self._result   = None   # 成功时的 action dict
            self._error    = None   # 失败时的错误字符串
            self._ready    = False
            # self._thread   = None

        def start(self):
            t = threading.Thread(target=self._poll, daemon=True)
            t.start()

            # self._thread = threading.Thread(
            #     target=self._poll,
            #     daemon=True           # 游戏退出时自动结束线程
            # )
            # self._thread.start()

        def _poll(self):
            deadline = time.time() + self.timeout

            while time.time() < deadline:
                if not os.path.exists(self.action_file):
                    time.sleep(0.1)
                    continue

                try:
                    with open(self.action_file, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                except (json.JSONDecodeError, OSError):
                    time.sleep(0.1)
                    continue
                finally:
                    # 无论读取是否成功，消费掉文件
                    try:
                        os.remove(self.action_file)
                    except OSError:
                        pass

                # 验证 turn_id
                if raw.get("turn_id") != self.expected_turn_id:
                    # turn_id 不匹配：过期数据，忽略，继续等
                    time.sleep(0.1)
                    continue

                # 验证 action 结构
                action = raw.get("action", {})
                action_type = action.get("type")

                if action_type not in ("advance", "choice"):
                    # self._error = f"unknown action type: {action_type!r}"
                    self._error = "unknown action type: %r" % action_type
                    self._ready = True
                    return

                if action_type == "choice" and "index" not in action:
                    # self._error = "choice 类型缺少 index 字段"
                    self._error = "choice missing index"
                    self._ready = True
                    return

                self._result = raw
                self._ready  = True
                return

            # 超时
            # self._error = f"timeout: agent 在 {self.timeout}s 内未响应"
            self._error = "timeout: agent did not respond within %ss" % self.timeout
            self._ready = True

        def is_ready(self):
            return self._ready

        def get_result(self):
            """返回 (action_dict_or_None, error_str_or_None)"""
            return self._result, self._error


label a11y_reset_session:
    python:
        a11y.reset_session()
    return


label a11y_export:
    python:
        a11y.save_to_file()
    return


label a11y_publish(mode, actions):
    python:
        a11y.publish(mode, actions)
    return


label a11y_wait_for_action:
    python:
        # agent_action = a11y.wait_for_action()
        # 创建 watcher 并启动后台线程
        _watcher = ActionWatcher(
            action_file      = a11y.action_file,
            expected_turn_id = getattr(store, "a11y_turn_id", 0),
            timeout          = 60.0,
        )
        _watcher.start()

    # Ren'Py 主循环：每 0.1s 检查一次 watcher
    # 这里 pause 是非阻塞的，UI 可以响应
    while not _watcher.is_ready():
        $ renpy.pause(0.1)

    python:
        _action_result, _action_error = _watcher.get_result()

        if _action_error:
            # 写入 store，供后续处理
            store.bridge_last_error = _action_error
            store.bridge_action     = None
        else:
            store.bridge_last_error = None
            store.bridge_action     = _action_result

    return store.bridge_action
    # return agent_action


label agent_say(speaker, text):
    if AGENT_MODE:
        python:
            current_speaker = speaker
            current_narrative = text
            actions = [{
                "id": "advance",
                "type": "advance",
                "text": "Continue",
            }]

        call a11y_publish("awaiting_action", actions)
        call a11y_wait_for_action
    else:
        python:
            renpy.say(speaker, text)

    return


label agent_choice(choice_items):
    if AGENT_MODE:
        python:
            actions = []
            for idx, item in enumerate(choice_items):
                actions.append({
                    "id": "choice_%03d" % idx,
                    "type": "choice",
                    "index": idx,
                    "text": item.get("caption", item.get("text", "")),
                    "semantic_label": item.get("semantic", item.get("semantic_label", "")),
                    "cognitive_load": item.get("cognitive_load", "medium"),
                    "consequence_hint": item.get("consequence_hint"),
                    "emotional_weight": item.get("emotional_weight"),
                })

        call a11y_publish("awaiting_action", actions)
        call a11y_wait_for_action

        python:
            agent_action = _return or {}
            choice_index = agent_action.get("action", {}).get("index", 0)
            if choice_index < 0 or choice_index >= len(choice_items):
                choice_index = 0

        return choice_index

    return 0


label a11y_finish:
    python:
        current_actions = []
        a11y.publish("finished", [])
    return
