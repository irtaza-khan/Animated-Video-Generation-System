import os
from shared.schemas.state_schema import ProjectState
from mcp.tools.video_tools.video_gen_tool import generate_video


def _build_video_prompt(scene) -> str:
    """Build a rich video prompt from scene location, characters, and dialogue visual cues."""
    character_details = []
    for char_name in scene.characters:
        if hasattr(scene, 'character_metadata') and char_name in scene.character_metadata:
            meta = scene.character_metadata[char_name]
            character_details.append(f"{char_name} ({meta.description})")
        else:
            character_details.append(char_name)
    
    first_speaker = scene.dialogue[0].speaker if scene.dialogue else "character"
    
    parts = [f"Scene at {scene.location}"]
    parts.append(f"Focus on {first_speaker} speaking dialogue")
    if character_details:
        parts.append(f"Featuring {', '.join(character_details)}")
    
    for dl in scene.dialogue:
        if dl.visual_cue:
            parts.append(dl.visual_cue)
    
    return ". ".join(parts) + ". Highly detailed, cinematic, focus on the speaker's face."


def run_video_agent(state: ProjectState) -> ProjectState:
    if not state.story or not state.story.scenes:
        return state
        
    os.makedirs("data/outputs/scenes", exist_ok=True)
    
    if "video_paths" not in state.assets:
        state.assets["video_paths"] = {}
    if "video_seeds" not in state.assets:
        state.assets["video_seeds"] = {}

    for scene in state.story.scenes:
        output_path = f"data/outputs/scenes/scene_{scene.scene_id}.mp4"
        prompt = _build_video_prompt(scene)
        print(f"Video Agent processing scene {scene.scene_id}...")
        print(f"  Prompt: {prompt[:80]}...")
        used_seed = generate_video(prompt, output_path, seed=-1)
        state.assets["video_paths"][str(scene.scene_id)] = output_path
        state.assets["video_seeds"][str(scene.scene_id)] = used_seed

    return state
