"""LipSync Agent — Phase 3.5

Merges the video clips with their per-scene audio.
Uses a Split-Sync-Merge strategy: it cuts the scene video into segments 
based on the dialogue timeline, applies Wav2Lip (if installed) or ffmpeg 
to each segment with the specific character's voice, and merges them back.
"""
import os
import subprocess
import shutil
from pathlib import Path
from moviepy import VideoFileClip, concatenate_videoclips
from shared.schemas.state_schema import ProjectState


def _ffmpeg() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except Exception:
        pass
    return None


def _mux(v_path: str, a_path: str, out_path: str) -> bool:
    """Mux video + audio with ffmpeg. Returns True on success."""
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        print("[LipSync] ffmpeg not found, skipping mux")
        return False
    try:
        subprocess.run(
            [
                ffmpeg, "-y",
                "-i", v_path,
                "-i", a_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                out_path,
            ],
            check=True,
            capture_output=True,
        )
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0
    except subprocess.CalledProcessError as e:
        print(f"[LipSync] ffmpeg error: {e.stderr.decode(errors='replace')[:300]}")
        return False
    except Exception as e:
        print(f"[LipSync] mux failed: {e}")
        return False


def _wav2lip(v_path: str, a_path: str, out_path: str) -> bool:
    """Attempt Wav2Lip lip-sync. Returns True if successful."""
    wav2lip_dir = os.path.join(os.getcwd(), "Wav2Lip")
    checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
    if not (os.path.exists(wav2lip_dir) and os.path.exists(checkpoint)):
        return False
    try:
        subprocess.run(
            [
                "python",
                os.path.join(wav2lip_dir, "inference.py"),
                "--checkpoint_path", checkpoint,
                "--face", v_path,
                "--audio", a_path,
                "--outfile", out_path,
                "--nosmooth"  # Prevents overly smooth transitions between short segments
            ],
            check=True,
            capture_output=True,
        )
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0
    except Exception as e:
        print(f"[LipSync] Wav2Lip failed: {e}")
        return False


def run_lipsync_agent(state: ProjectState) -> ProjectState:
    if not state.story or not state.story.scenes:
        return state

    video_paths = state.assets.get("video_paths", {})
    audio_paths = state.assets.get("audio_paths", {})

    os.makedirs("data/outputs/synced", exist_ok=True)
    if "synced_video_paths" not in state.assets:
        state.assets["synced_video_paths"] = {}

    for scene in state.story.scenes:
        sid_int = scene.scene_id
        sid_str = str(sid_int)

        v_path = video_paths.get(sid_str) or video_paths.get(sid_int)
        a_path = audio_paths.get(sid_str) or audio_paths.get(sid_int)

        if not v_path or not os.path.exists(v_path):
            print(f"[LipSync] Scene {sid_str}: video not found, skipping")
            continue
        if not a_path or not os.path.exists(a_path):
            print(f"[LipSync] Scene {sid_str}: audio not found, skipping")
            continue

        out_path = f"data/outputs/synced/scene_{sid_str}_synced.mp4"
        timing = None
        if state.timing and state.timing.scene_timings:
            timing = state.timing.scene_timings.get(sid_int) or state.timing.scene_timings.get(sid_str)

        if not timing or not timing.dialogue_timeline:
            print(f"[LipSync] Scene {sid_str}: no timing timeline found, falling back to simple full-scene mux.")
            success = _wav2lip(v_path, a_path, out_path) or _mux(v_path, a_path, out_path)
            if success:
                state.assets["video_paths"][sid_str] = out_path
                state.assets["synced_video_paths"][sid_str] = out_path
            continue

        print(f"[LipSync] Scene {sid_str}: applying Split-Sync-Merge on {len(timing.dialogue_timeline)} segments...")
        synced_segments = []
        try:
            full_video = VideoFileClip(v_path)
            for i, seg in enumerate(timing.dialogue_timeline):
                seg_v_path = f"data/outputs/synced/scene_{sid_str}_seg_{i}_v.mp4"
                seg_out_path = f"data/outputs/synced/scene_{sid_str}_seg_{i}_synced.mp4"
                
                start = seg.start_seconds
                end = min(seg.end_seconds, full_video.duration)
                
                # If segment starts after video ends, skip it
                if start >= full_video.duration:
                    print(f"  -> Skipping segment {i} (starts at {start}s, video duration is {full_video.duration}s)")
                    continue
                    
                # 1. Extract video subclip
                sub_clip = full_video.subclipped(start, end)
                sub_clip.write_videofile(seg_v_path, codec="libx264", audio=False, logger=None)
                
                # 2. Get specific character audio segment
                seg_a_path = f"data/outputs/audio/scene_{sid_int:02d}/segment_{i:04d}_{seg.speaker.lower().replace(' ', '_')}.wav"
                
                if not os.path.exists(seg_a_path):
                    # Fallback if specific audio file is missing: slice the mixed audio
                    seg_a_path = f"data/outputs/synced/scene_{sid_str}_seg_{i}_a.wav"
                    ffmpeg = _ffmpeg()
                    if ffmpeg:
                        subprocess.run([
                            ffmpeg, "-y", "-i", a_path, "-ss", str(start), "-to", str(end),
                            "-c", "copy", seg_a_path
                        ], capture_output=True)
                
                # 3. Sync this specific segment
                if os.path.exists(seg_a_path):
                    success = _wav2lip(seg_v_path, seg_a_path, seg_out_path) or _mux(seg_v_path, seg_a_path, seg_out_path)
                    if success:
                        synced_segments.append(VideoFileClip(seg_out_path))
                    else:
                        print(f"  -> Failed to sync segment {i}, using silent video segment.")
                        synced_segments.append(VideoFileClip(seg_v_path))
                else:
                    print(f"  -> Audio segment missing for {i}, using silent video segment.")
                    synced_segments.append(VideoFileClip(seg_v_path))
                    
            # 4. Merge the synced segments
            if synced_segments:
                final_synced = concatenate_videoclips(synced_segments, method="compose")
                final_synced.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=24, logger=None)
                state.assets["video_paths"][sid_str] = out_path
                state.assets["synced_video_paths"][sid_str] = out_path
                print(f"[LipSync] Scene {sid_str}: Split-Sync-Merge complete -> {out_path}")
            else:
                print(f"[LipSync] Scene {sid_str}: No valid segments merged, keeping original video.")
                
            full_video.close()
            for s in synced_segments: 
                try: s.close()
                except Exception: pass

        except Exception as e:
            print(f"[LipSync] Split-Sync-Merge failed for scene {sid_str}: {e}. Falling back to simple full-scene mux.")
            success = _wav2lip(v_path, a_path, out_path) or _mux(v_path, a_path, out_path)
            if success:
                state.assets["video_paths"][sid_str] = out_path
                state.assets["synced_video_paths"][sid_str] = out_path

    return state
