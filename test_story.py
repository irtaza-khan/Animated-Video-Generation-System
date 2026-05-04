import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.story_agent.agent import run_story_agent

def main():
    print("=" * 60)
    print("TEST: Story Agent (Phase 1)")
    print("=" * 60)
    
    prompt = "A spy thriller in a rainy Tokyo alleyway"
    print(f"\nPrompt: '{prompt}'")
    
    story = run_story_agent(prompt, num_scenes=2)
    
    print(f"\nGenerated {len(story.scenes)} scenes:\n")
    for scene in story.scenes:
        print(f"Scene {scene.scene_id}: {scene.location}")
        print(f"  Characters: {scene.characters}")
        for dl in scene.dialogue:
            print(f"    {dl.speaker}: \"{dl.line}\" [{dl.visual_cue}]")
        print()
    
    print("Story Agent test PASSED!")

if __name__ == "__main__":
    main()
