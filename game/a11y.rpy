# A11y-RenPy-Bridge: Accessibility Export Module
# Version: 0.1
# Purpose: Export game state as semantic JSON for AI agents

init python:
    import json
    import os
    from datetime import datetime
    
    class A11yExporter:
        """
        Export Ren'Py game state to structured JSON.
        Enables AI agents to play games without pixel-level vision.
        """
        
        def __init__(self):
            self.version = "0.1"
            self.export_dir = os.path.join(renpy.config.gamedir, "exports")
            self.ensure_export_dir()
        
        def ensure_export_dir(self):
            """Create export directory if not exists"""
            if not os.path.exists(self.export_dir):
                os.makedirs(self.export_dir)
        
        def export_state(self):
            """
            Export current game state.
            Returns dict following a11y-renpy-bridge schema.
            """
            state = {
                "schema_version": self.version,
                "timestamp": datetime.now().isoformat(),
                
                "scene": self._export_scene(),
                "narrative": self._export_narrative(),
                "choices": self._export_choices(),
                "player_state": self._export_player_state()
            }
            
            return state
        
        def _export_scene(self):
            """Export current scene information"""
            # Get current scene from store
            scene_id = getattr(store, "current_scene_id", "unknown")
            scene_data = getattr(store, "scenes", {}).get(scene_id, {})
            
            return {
                "id": scene_id,
                "name": scene_data.get("name", "Unnamed Scene"),
                "description": scene_data.get("description", ""),
                "accessibility": {
                    "visual_description": scene_data.get("visual_desc", ""),
                    "audio_cues": scene_data.get("audio_cues", []),
                    "complexity": scene_data.get("complexity", "low")
                }
            }
        
        def _export_narrative(self):
            """Export current dialogue/text"""
            return {
                "current_text": getattr(store, "current_narrative", ""),
                "speaker": getattr(store, "_last_say_who", None)
            }
        
        def _export_choices(self):
            """Export available choices"""
            menu_items = getattr(store, "menu_items", [])
            
            choices = []
            for idx, item in enumerate(menu_items):
                choice = {
                    "id": f"choice_{idx:03d}",
                    "text": item.get("caption", ""),
                    "accessibility": {
                        "semantic_label": item.get("semantic", ""),
                        "cognitive_load": item.get("cognitive_load", "medium")
                    }
                }
                choices.append(choice)
            
            return choices
        
        def _export_player_state(self):
            """Export player progress and state"""
            return {
                "history": getattr(store, "choice_history", []),
                # "current_label": renpy.get_return_stack()[-1] if renpy.get_return_stack() else "start"
                "current_label": getattr(store, "current_scene_id", "unknown")
            }
        
        def save_to_file(self, filename="state.json"):
            """Save current state to JSON file"""
            state = self.export_state()
            filepath = os.path.join(self.export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            return filepath
    
    # Global instance
    a11y = A11yExporter()


# Auto-export hooks
label a11y_export:
    """Call this label to trigger export"""
    python:
        a11y.save_to_file()
    return