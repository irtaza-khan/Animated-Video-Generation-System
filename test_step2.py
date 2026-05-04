import sys
import os

# Add current dir to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.schemas.story_schema import Scene, StoryOutput
from shared.schemas.state_schema import ProjectState
from agents.video_agent.agent import run_video_agent
from mcp.tools.video_tools.compositor_tool import compose_final_video

def main():
    print("Creating a dummy project state...")
    
    # Create a simple story with 1 scene
    scene1 = Scene(
        id=1,
        visual_prompt="A beautiful sunset over the mountains, digital art",
        dialogue="Wow, look at that view.",
        characters=["Narrator"]
    )
    
    story = StoryOutput(scenes=[scene1])
    state = ProjectState(version=1, story=story)
    
    print("\n--- Running Video Agent ---")
    state = run_video_agent(state)
    
    print("\n--- Running Compositor ---")
    compose_final_video(state, "data/outputs/test_final.mp4")
    
    print(f"\nDone! Assets: {state.assets}")
    
if __name__ == "__main__":
    main()
