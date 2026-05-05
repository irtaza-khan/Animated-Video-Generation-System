"""Quick test: run lipsync + compositor on already-generated scenes."""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.story_agent.agent import run_story_agent
from agents.audio_agent.agent import run_audio_agent
from agents.lipsync_agent.agent import run_lipsync_agent
from mcp.tools.video_tools.compositor_tool import compose_final_video
from shared.schemas.state_schema import ProjectState

def main():
    print("=" * 60)
    print("TEST: LipSync + Compositor (using existing scene videos)")
    print("=" * 60)

    story = run_story_agent("spy thriller", num_scenes=3)
    state = ProjectState(version=1, story=story, assets={
        "video_paths": {
            "1": "data/outputs/scenes/scene_1.mp4",
            "2": "data/outputs/scenes/scene_2.mp4",
            "3": "data/outputs/scenes/scene_3.mp4",
        },
        "audio_paths": {},
    })

    print("\n[Step 1] Generating audio...")
    state = run_audio_agent(state)
    print(f"Audio paths: {state.assets['audio_paths']}")

    print("\n[Step 2] LipSync (mux audio into video)...")
    state = run_lipsync_agent(state)
    print(f"Updated video paths: {state.assets['video_paths']}")
    print(f"Synced video paths: {state.assets.get('synced_video_paths', {})}")

    print("\n[Step 3] Compositing final video...")
    compose_final_video(state, "data/outputs/final_output.mp4")

    final = "data/outputs/final_output.mp4"
    if os.path.exists(final):
        size = os.path.getsize(final)
        print(f"\n[OK] final_output.mp4 created! Size: {size / 1024:.1f} KB")
    else:
        print("\n❌ final_output.mp4 NOT found!")

if __name__ == "__main__":
    main()
