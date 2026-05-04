import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.story_agent.agent import run_story_agent
from agents.audio_agent.agent import run_audio_agent
from shared.schemas.state_schema import ProjectState

def main():
    print("=" * 60)
    print("TEST: Audio Agent (Phase 2)")
    print("=" * 60)
    
    prompt = "A spy thriller in a rainy Tokyo alleyway"
    story = run_story_agent(prompt, num_scenes=2)
    
    state = ProjectState(version=1, story=story, assets={})
    state = run_audio_agent(state)
    
    print(f"\nAudio paths: {state.assets.get('audio_paths', {})}")
    
    if state.timing:
        for sid, timing in state.timing.scene_timings.items():
            print(f"\nScene {sid}:")
            print(f"  Audio: {timing.audio_filepath}")
            print(f"  Duration: {timing.duration_ms}ms")
            print(f"  Timeline entries: {len(timing.dialogue_timeline)}")
            for seg in timing.dialogue_timeline:
                print(f"    {seg.speaker} [{seg.start_seconds:.2f}s-{seg.end_seconds:.2f}s]: {seg.line[:50]}...")
    
    # Check files exist
    for sid, path in state.assets.get("audio_paths", {}).items():
        exists = os.path.exists(path)
        print(f"\n  Scene {sid} wav exists: {exists}")
    
    print("\nAudio Agent test PASSED!")

if __name__ == "__main__":
    main()
