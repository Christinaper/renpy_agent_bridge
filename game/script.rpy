# A11y-RenPy-Bridge Demo Game
# Three abstract scenes for technical validation

define AGENT_MODE = True  # 设为False恢复手动模式

# Scene definitions
init python:
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
    current_narrative = ""
    choice_history = []
    menu_items = []

# Start
label start:
    
    # Initialize
    $ current_scene_id = "room"
    $ current_narrative = ""
    $ choice_history = []
    $ menu_items = []
    
    jump scene_room

# Scene 1: The Room
label scene_room:
    
    $ current_scene_id = "room"
    
    scene bg gray
    
    "You are in a room."
    "There is an object here."

    # Prepare menu items for export
    python:
        current_narrative = "You are in a room. There is an object here."
        menu_items = [
            {
                "caption": "Interact with object",
                "semantic": "engage",
                "cognitive_load": "low"
            },
            {
                "caption": "Ignore object",
                "semantic": "avoid",
                "cognitive_load": "minimal"
            }
        ]
    
    # Export state with choices
    call a11y_export
    
    if AGENT_MODE:
        # Agent模式：等待AI决策
        call a11y_wait_for_agent
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
    "You touch the object."
    "It feels cold."
    jump scene_crossroad

label room_ignore:
    "You leave the object alone."
    jump scene_crossroad

# Scene 2: The Crossroad
label scene_crossroad:
    
    $ current_scene_id = "crossroad"
    
    scene bg black
    
    "You arrive at a crossroad."
    "Three paths lie ahead."
    
    python:
        current_narrative = "You arrive at a crossroad. Three paths lie ahead."
        menu_items = [
            {"caption": "Go left", "semantic": "explore_path_a", "cognitive_load": "low"},
            {"caption": "Go right", "semantic": "explore_path_b", "cognitive_load": "low"},
            {"caption": "Stay here", "semantic": "wait", "cognitive_load": "minimal"}
        ]
    
    call a11y_export
    
    if AGENT_MODE:
        # Agent模式：等待AI决策
        call a11y_wait_for_agent
        $ choice_index = _return
        
        if choice_index == 0:
            $ choice_history.append("path_left")
            "You walk into darkness."
            jump scene_echo
        elif choice_index == 1:
            $ choice_history.append("path_right")
            "You walk into light."
            jump scene_echo
        else:
            $ choice_history.append("path_stay")
            "You wait."
            pause 2.0
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
    $ current_narrative = "You return to a familiar place."
    
    scene bg gray
    
    "You return to a familiar place."
    
    # Reference previous choices
    if "interact_room" in choice_history:
        "The object remembers you."
    else:
        "The object is still here."
    
    "Your path: [choice_history]"
    
    python:
        menu_items = [
            {"caption": "Finish", "semantic": "conclude", "cognitive_load": "minimal"}
        ]
    
    call a11y_export
    
    if AGENT_MODE:
        # Agent模式：等待AI决策
        call a11y_wait_for_agent
        $ choice_index = _return
        
        jump end
    else:
        # 手动模式：显示菜单
        menu:
            "Finish":
                jump end

label end:
    $ current_scene_id = "end"
    $ current_narrative = "Demo complete. Agent behavior logged."
    $ menu_items = []
    call a11y_export
    
    "Demo complete."
    "Agent behavior logged."
    
    return
