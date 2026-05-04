from typing import Dict, Any
from shared.schemas.state_schema import ProjectState
from state_manager.state_manager import StateManager
from mcp.tools.video_tools.video_gen_tool import generate_video
from mcp.tools.video_tools.compositor_tool import compose_final_video

def execute_edit(state: ProjectState, intent: Dict[str, Any], state_manager: StateManager) -> ProjectState:
    """Executes the parsed intent, updating the state and regenerating assets."""
    
    # 1. Save current state as an undo point BEFORE modifying
    state = state_manager.save_state(state)
    
    target = intent.get("target")
    scene_id = intent.get("scene_id")
    action = intent.get("action")
    value = intent.get("value")
    
    if target == "video_frame" and action == "update_prompt":
        # Find the scene
        target_scene = next((s for s in state.story.scenes if s.scene_id == scene_id), None)
        if target_scene:
            print(f"Applying edit: Updating Scene {scene_id} prompt to '{value}'")
            target_scene.location = value
            
            # Regenerate ONLY this scene's video
            output_path = f"data/outputs/scenes/scene_{scene_id}.mp4"
            generate_video(value, output_path)
            
            if "video_paths" not in state.assets:
                state.assets["video_paths"] = {}
            state.assets["video_paths"][str(scene_id)] = output_path
            
            # Recomposite the final video
            print("Recompositing final video with new scene...")
            compose_final_video(state, "data/outputs/final_output.mp4")
        else:
            print(f"Error: Scene {scene_id} not found.")
            
    return state
