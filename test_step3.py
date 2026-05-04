import sys
import os
import shutil

# Add current dir to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.schemas.story_schema import Scene, StoryOutput
from shared.schemas.state_schema import ProjectState
from state_manager.state_manager import StateManager

def main():
    sm = StateManager()
    
    # 1. Setup initial state
    scene1 = Scene(id=1, visual_prompt="A beautiful sunset", dialogue="Wow")
    state = ProjectState(version=1, story=StoryOutput(scenes=[scene1]))
    
    # Create some dummy active assets
    os.makedirs("data/outputs/scenes", exist_ok=True)
    with open("data/outputs/scenes/scene_1.mp4", "w") as f:
        f.write("dummy video data v1")
        
    print(f"Original State Version: {state.version}")
    print("Saving version 1...")
    state = sm.save_state(state)
    
    print(f"State Version after save: {state.version}")
    
    # 2. Modify state and assets (simulate an edit)
    print("\nSimulating an edit (modifying scene and overwriting video)...")
    state.story.scenes[0].visual_prompt = "A dark stormy night"
    with open("data/outputs/scenes/scene_1.mp4", "w") as f:
        f.write("dummy video data v2 (EDITED)")
        
    print("Saving version 2...")
    state = sm.save_state(state)
    
    # Check active data
    with open("data/outputs/scenes/scene_1.mp4", "r") as f:
        content = f.read()
    print(f"Active video content: {content}")
    print(f"Active visual prompt: {state.story.scenes[0].visual_prompt}")
    
    # 3. Revert to version 1
    print("\nReverting to version 1...")
    state = sm.revert_to_version(1)
    
    print(f"Reverted State Version (ready for new edits): {state.version}")
    print(f"Reverted visual prompt: {state.story.scenes[0].visual_prompt}")
    
    # Check active data again
    with open("data/outputs/scenes/scene_1.mp4", "r") as f:
        content = f.read()
    print(f"Active video content after revert: {content}")
    
if __name__ == "__main__":
    main()
