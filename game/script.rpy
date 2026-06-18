# game/script.rpy
# A11y-RenPy-Bridge Demo Game
# Three abstract scenes for technical validation

# Scene definitions
init python:
    import os

    # 优先级：环境变量 > 默认值（True）
    # 开发时：AGENT_MODE=0 renpy.sh game  → 手动模式
    # 正常时：直接运行 → Agent 模式
    AGENT_MODE = os.environ.get("RENPY_AGENT_MODE", "1").strip().lower() not in ("0", "false", "no")

    def set_semantic(mood=None, emotion=None, importance=None):
        ctx = {}
        if mood:       ctx["mood"]       = mood
        if emotion:    ctx["emotion"]    = emotion
        if importance: ctx["importance"] = importance
        store._semantic_ctx = ctx if ctx else None

    def set_author_note(hint=None, player_should_feel=None):
        note = {}
        if hint:               note["hint"]               = hint
        if player_should_feel: note["player_should_feel"] = player_should_feel
        store._author_note = note if note else None

    def clear_semantic():
        store._semantic_ctx = None
        store._author_note  = None

    scenes = {
        "room": {
            "name": "The Room",
            "description": "A minimal space with one object",
            "visual_desc": "A gray room with a square object in the center",
            "audio_cues": [],
            "complexity": "low"
        },
        "crossroad": {
            "name": "The Crossroad",
            "description": "A point of divergence with three paths",
            "visual_desc": "Three corridors extending in different directions",
            "audio_cues": ["ambient echo"],
            "complexity": "medium"
        },
        "echo": {
            "name": "The Echo",
            "description": "A familiar place, but changed",
            "visual_desc": "The same room, but the object has moved",
            "audio_cues": ["faint repetition"],
            "complexity": "low"
        },
        "end": {
            "name": "The End",
            "description": "Demo conclusion",
            "visual_desc": "A final screen",
            "audio_cues": [],
            "complexity": "minimal"
        }
    }
    
    # Global state
    current_scene_id = "room"
    current_speaker = None
    current_narrative = ""
    choice_history = []
    menu_items = []

# Start
label start:
    
    # Initialize
    call a11y_reset_session
    $ current_scene_id = "room"
    $ current_speaker = None
    $ current_narrative = ""
    $ choice_history = []
    $ menu_items = []
    
    jump scene_room

# Scene 1: The Room
label scene_room:
    
    $ current_scene_id = "room"
    
    scene bg gray
    
    call agent_say(None, "You are in a room.")
    call agent_say(None, "There is an object here.")

    python:
        room_choices = [
            {"text": "Interact with object",    "semantic_label": "engage",   "cognitive_load": "low"},
            {"text": "Ignore object",           "semantic_label": "avoid",    "cognitive_load": "minimal"}
        ]
    
    if AGENT_MODE:
        call agent_choice(room_choices)
        $ choice_index = _return
        
        if choice_index == 0:
            $ choice_history.append("interact_room")
            jump room_interact
        else:
            $ choice_history.append("ignore_room")
            jump room_ignore
    else:
        # 手动模式：显示菜单
        menu:
            "Interact with object":
                $ choice_history.append("interact_room")
                jump room_interact
            
            "Ignore object":
                $ choice_history.append("ignore_room")
                jump room_ignore

label room_interact:
    $ set_semantic(mood="mysterious", emotion="surprised", importance="high")
    $ set_author_note(hint="玩家第一次触碰物体", player_should_feel="好奇与不安")

    call agent_say(None, "You touch the object.")
    call agent_say(None, "It feels cold.")

    $clear_semantic()
    jump scene_crossroad

label room_ignore:
    call agent_say(None, "You leave the object alone.")
    jump scene_crossroad

# Scene 2: The Crossroad
label scene_crossroad:
    
    $ current_scene_id = "crossroad"
    
    scene bg black
    
    call agent_say(None, "You arrive at a crossroad.")
    call agent_say(None, "Three paths lie ahead.")
    
    python:
        crossroad_choices = [
            {"text": "Go left",      "semantic_label": "explore_path_a", "cognitive_load": "low"},
            {"text": "Go right",     "semantic_label": "explore_path_b", "cognitive_load": "low"},
            {"text": "Stay here",    "semantic_label": "wait",           "cognitive_load": "minimal"}
        ]
    
    if AGENT_MODE:
        call agent_choice(crossroad_choices)
        $ choice_index = _return
        
        if choice_index == 0:
            $ choice_history.append("path_left")
            call agent_say(None, "You walk into darkness.")
            jump scene_echo
        elif choice_index == 1:
            $ choice_history.append("path_right")
            call agent_say(None, "You walk into light.")
            jump scene_echo
        else:
            $ choice_history.append("path_stay")
            call agent_say(None, "You wait.")
            jump scene_echo
    else:
        # 手动模式：显示菜单
        menu:
            "Go left":
                $ choice_history.append("path_left")
                "You walk into darkness."
                jump scene_echo
            
            "Go right":
                $ choice_history.append("path_right")
                "You walk into light."
                jump scene_echo
            
            "Stay here":
                $ choice_history.append("path_stay")
                "You wait."
                pause 2.0
                jump scene_echo

# Scene 3: The Echo
label scene_echo:
    
    $ current_scene_id = "echo"
    
    scene bg gray
    
    call agent_say(None, "You return to a familiar place.")
    
    # Reference previous choices
    if "interact_room" in choice_history:
        call agent_say(None, "The object remembers you.")
    else:
        call agent_say(None, "The object is still here.")
    
    $ path_text = "Your path: " + str(choice_history)
    call agent_say(None, path_text)
    
    python:
        finish_choices = [
            {"text": "Finish",    "semantic_label": "conclude", "cognitive_load": "minimal"}
        ]
    
    if AGENT_MODE:
        call agent_choice(finish_choices)
        $ choice_index = _return
        
        jump end
    else:
        # 手动模式：显示菜单
        menu:
            "Finish":
                jump end

label end:
    $ current_scene_id = "end"
    
    call agent_say(None, "Demo complete.")
    call agent_say(None, "Agent behavior logged.")
    call a11y_finish
    
    return
