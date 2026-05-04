import os
import json
from shared.schemas.state_schema import ProjectState
from agents.story_agent.agent import run_story_agent
from agents.audio_agent.agent import run_audio_agent
from agents.video_agent.agent import run_video_agent
from agents.lipsync_agent.agent import run_lipsync_agent
from mcp.tools.vision_tools.image_gen_tool import generate_character_portrait
from mcp.tools.video_tools.compositor_tool import compose_final_video
from state_manager.state_manager import StateManager

def update_status(job_id: str, status: str, progress: int = 0, extra_data: dict = None):
    os.makedirs("data/temp", exist_ok=True)
    payload = {"status": status, "progress": progress}
    
    # Load existing data to preserve previous extra_data
    try:
        if os.path.exists(f"data/temp/{job_id}.json"):
            with open(f"data/temp/{job_id}.json", "r") as f:
                old_data = json.load(f)
                # Preserve everything except status and progress
                for k, v in old_data.items():
                    if k not in ["status", "progress"]:
                        payload[k] = v
    except: pass

    if extra_data:
        payload.update(extra_data)
        
    with open(f"data/temp/{job_id}.json", "w") as f:
        json.dump(payload, f)

def run_full_pipeline(job_id: str, prompt: str, num_scenes: int = 3):
    """Full pipeline: Story -> Portraits -> Audio -> Video -> LipSync -> Compositor -> Save State."""
    try:
        # Phase 1: Story Generation
        update_status(job_id, "generating_story", 5)
        story = run_story_agent(prompt, num_scenes)
        
        state = ProjectState(version=1, story=story, assets={"video_paths": {}, "audio_paths": {}, "character_portraits": {}})
        
        # Phase 1.5: Character Portraits
        update_status(job_id, "casting_characters", 10)
        unique_characters = {} # char_name -> description
        for scene in story.scenes:
            # Check for character_metadata
            metadata = getattr(scene, 'character_metadata', {}) if hasattr(scene, 'character_metadata') else {}
            if not metadata and hasattr(story, 'character_metadata'):
                 metadata = story.character_metadata
            
            for char in scene.characters:
                if char not in unique_characters:
                    # Get description from metadata if available
                    meta = metadata.get(char)
                    desc = meta.description if hasattr(meta, 'description') else str(meta.get('description', '')) if isinstance(meta, dict) else ""
                    unique_characters[char] = desc
        
        for char, desc in unique_characters.items():
            print(f"[Orchestrator] Generating portrait for {char}...")
            portrait_path = generate_character_portrait(char, desc)
            # Make path relative for frontend (strip 'data/')
            rel_path = portrait_path.replace("data/", "") if portrait_path else ""
            state.assets["character_portraits"][char] = rel_path
        
        # Update status with portraits
        update_status(job_id, "generating_audio", 20, {"portraits": state.assets["character_portraits"]})
        state = run_audio_agent(state)
        
        # Phase 3: Video Generation
        update_status(job_id, "generating_video", 40)
        state = run_video_agent(state)
        
        # Phase 3.5: LipSync
        update_status(job_id, "lip_syncing", 70)
        state = run_lipsync_agent(state)
        
        # Phase 4: Compositing
        update_status(job_id, "compositing", 85)
        compose_final_video(state, "data/outputs/final_output.mp4")
        
        # Save State Snapshot
        update_status(job_id, "saving_state", 95)
        sm = StateManager()
        sm.save_state(state)
        
        update_status(job_id, "completed", 100)
    except Exception as e:
        print(f"[Pipeline Error] {e}")
        import traceback
        traceback.print_exc()
        update_status(job_id, f"error: {str(e)}", 0)
