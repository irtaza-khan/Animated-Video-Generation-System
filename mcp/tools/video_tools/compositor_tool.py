"""Compositor Tool — Phase 4

Stitches all scene videos into a single final_output.mp4.
By the time this runs, each video already has audio baked in
by the LipSync agent (or AudioAgent fallback), so we just concatenate.
"""
import os
from moviepy import VideoFileClip, concatenate_videoclips
from shared.schemas.state_schema import ProjectState


def compose_final_video(
    state: ProjectState,
    output_path: str = "data/outputs/final_output.mp4",
):
    video_paths = state.assets.get("video_paths", {})
    if not video_paths:
        print("[Compositor] No video paths found, aborting.")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    clips = []
    for scene in sorted(state.story.scenes, key=lambda x: x.scene_id):
        sid_str = str(scene.scene_id)
        v_path = video_paths.get(sid_str) or video_paths.get(scene.scene_id)

        if not v_path or not os.path.exists(v_path):
            print(f"[Compositor] Scene {sid_str}: video missing at {v_path!r}, skipping")
            continue

        print(f"[Compositor] Adding scene {sid_str}: {v_path}")
        try:
            clip = VideoFileClip(v_path)
            clips.append(clip)
        except Exception as e:
            print(f"[Compositor] Failed to load clip {v_path}: {e}")

    if not clips:
        print("[Compositor] No valid clips to compose.")
        return

    print(f"[Compositor] Concatenating {len(clips)} clip(s)...")
    try:
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_path, fps=24, logger=None)
        state.assets["final_video"] = output_path
        print(f"[Compositor] Final video written -> {output_path}")
    except Exception as e:
        print(f"[Compositor] Concatenation failed: {e}")
        raise
    finally:
        for c in clips:
            try:
                c.close()
            except Exception:
                pass
