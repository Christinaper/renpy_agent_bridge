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
            # self.state_file  = os.path.join(self.export_dir, f"state_{sid}.json")
            # self.action_file = os.path.join(self.export_dir, f"action_{sid}.json")
            self.state_file  = os.path.join(self.export_dir, "state_%s.json"  % sid)
            self.action_file = os.path.join(self.export_dir, "action_%s.json" % sid)
            # legacy 路径保留用于兼容性检测
            self.legacy_choice_file = os.path.join(self.export_dir, "choice.txt")

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
            return {
                "current_text": getattr(store, "current_narrative", ""),
                "speaker": getattr(store, "current_speaker", None),
            }

        def _export_actions(self):
            return list(getattr(store, "current_actions", []))

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
        agent_action = a11y.wait_for_action()
    return agent_action


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
