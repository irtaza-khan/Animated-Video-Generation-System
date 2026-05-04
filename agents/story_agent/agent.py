"""Story Agent — Phase 1.

Takes a user prompt and generates a structured StoryOutput
using the LLM fallback chain (Groq -> Ollama -> local).
"""
from shared.schemas.story_schema import StoryOutput, Scene, DialogueLine
from agents.story_agent.llm_providers import (
    make_script_via_groq,
    make_script_via_ollama,
    make_script_local,
    GROQ_ENABLED,
    GROQ_API_KEY,
    OLLAMA_ENABLED,
)


def run_story_agent(prompt: str, num_scenes: int = 3) -> StoryOutput:
    """Generate a structured story from a text prompt."""
    payload = {"prompt": prompt, "num_scenes": num_scenes}
    raw_script = None

    # 1. Try Groq (fast, free tier)
    if GROQ_ENABLED and GROQ_API_KEY:
        try:
            raw_script = make_script_via_groq(payload)
            print(f"[StoryAgent] Script generated via Groq ({num_scenes} scenes)")
        except Exception as e:
            print(f"[StoryAgent] Groq unavailable: {e}")

    # 2. Try Ollama (local LLM)
    if raw_script is None and OLLAMA_ENABLED:
        try:
            raw_script = make_script_via_ollama(payload)
            print(f"[StoryAgent] Script generated via Ollama ({num_scenes} scenes)")
        except Exception as e:
            print(f"[StoryAgent] Ollama unavailable: {e}")

    # 3. Local deterministic fallback
    if raw_script is None:
        raw_script = make_script_local(payload)
        print(f"[StoryAgent] Script generated via local fallback ({num_scenes} scenes)")

    # Convert raw dict to Pydantic StoryOutput
    scenes = []
    for s in raw_script.get("scenes", []):
        dialogue_lines = [
            DialogueLine(speaker=d["speaker"], line=d["line"], visual_cue=d.get("visual_cue", ""))
            for d in s.get("dialogue", [])
        ]
        scenes.append(Scene(
            scene_id=s["scene_id"],
            location=s.get("location", f"Scene {s['scene_id']}"),
            characters=s.get("characters", []),
            character_metadata=s.get("character_metadata", {}),
            dialogue=dialogue_lines,
        ))
    
    return StoryOutput(
        scenes=scenes,
        character_metadata=raw_script.get("character_metadata", {})
    )
