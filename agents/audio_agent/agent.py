"""Audio Agent — Phase 2.

Takes a ProjectState with a StoryOutput and generates
per-scene audio files, populating the TimingManifest.
"""
import os
from pathlib import Path
from shared.schemas.state_schema import ProjectState
from shared.schemas.audio_schema import TimingManifest, AudioTiming, DialogueSegment
from mcp.tools.audio_tools.tts_tool import synthesize_scene_audio


def run_audio_agent(state: ProjectState) -> ProjectState:
    """Generate audio for every scene in the story."""
    if not state.story or not state.story.scenes:
        return state

    audio_dir = Path("data/outputs/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)

    scene_timings = {}
    if "audio_paths" not in state.assets:
        state.assets["audio_paths"] = {}

    for scene in state.story.scenes:
        print(f"[AudioAgent] Synthesizing audio for scene {scene.scene_id}...")
        result = synthesize_scene_audio(scene, audio_dir)

        state.assets["audio_paths"][str(scene.scene_id)] = result["audio_filepath"]

        timeline_segments = [
            DialogueSegment(
                speaker=seg["speaker"],
                line=seg["line"],
                start_seconds=seg["start_seconds"],
                end_seconds=seg["end_seconds"],
            )
            for seg in result.get("dialogue_timeline", [])
        ]

        scene_timings[scene.scene_id] = AudioTiming(
            audio_filepath=result["audio_filepath"],
            duration_ms=result["duration_ms"],
            subtitle_text=result["subtitle_text"],
            dialogue_timeline=timeline_segments,
        )

    state.timing = TimingManifest(scene_timings=scene_timings)
    return state
