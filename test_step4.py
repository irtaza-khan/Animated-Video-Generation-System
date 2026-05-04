import sys
import os

# Add current dir to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.schemas.story_schema import Scene, StoryOutput
from shared.schemas.state_schema import ProjectState
from state_manager.state_manager import StateManager
from agents.edit_agent.intent_classifier import classify_intent
from agents.edit_agent.executor import execute_edit

def main():
    sm = StateManager()
    
    # 1. Setup initial state
    scene1 = Scene(id=1, visual_prompt="A beautiful sunset", dialogue="Wow")
    scene2 = Scene(id=2, visual_prompt="A calm ocean", dialogue="Peaceful")
    story = StoryOutput(scenes=[scene1, scene2])
    state = ProjectState(version=1, story=story, assets={"video_paths": {}})
    
    # 2. Emulate user request
    user_query = "Update scene 2 prompt to: a stormy raging ocean"
    print(f"User Query: '{user_query}'")
    
    intent = classify_intent(user_query)
    print(f"Parsed Intent: {intent}")
    
    if intent:
        # 3. Execute the edit
        state = execute_edit(state, intent, sm)
        
    print(f"\nFinal State Version: {state.version}")
    print(f"Final Scene 2 Prompt: '{state.story.scenes[1].visual_prompt}'")
    print(f"Generated Assets: {state.assets}")
    
if __name__ == "__main__":
    main()
