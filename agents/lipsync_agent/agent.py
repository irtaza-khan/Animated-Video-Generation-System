import os
import subprocess
import shutil
from pathlib import Path
from moviepy import VideoFileClip, concatenate_videoclips
from shared.schemas.state_schema import ProjectState

def run_lipsync_agent(state: ProjectState) -> ProjectState:
    """
    Attempts to lip-sync the generated videos with their dialogue audio.
    Uses a split-sync-merge strategy to ensure lips only move for the correct speaker.
    """
    if not state.story or not state.story.scenes:
        return state
        
    video_paths = state.assets.get("video_paths", {})
    audio_paths = state.assets.get("audio_paths", {})
    
    os.makedirs("data/outputs/synced", exist_ok=True)
    if "synced_video_paths" not in state.assets:
        state.assets["synced_video_paths"] = {}

    for scene in state.story.scenes:
        sid = str(scene.scene_id)
        v_path = video_paths.get(sid)
        # The main mixed audio
        a_path = audio_paths.get(sid)
        
        if not v_path or not a_path or not os.path.exists(v_path):
            continue
            
        output_path = f"data/outputs/synced/scene_{sid}_synced.mp4"
        
        # Get timeline for splitting
        timing = state.timing.scene_timings.get(sid) if state.timing else None
        if not timing or not timing.dialogue_timeline:
            # No timeline, fallback to simple mux
            _simple_mux(v_path, a_path, output_path)
            state.assets["video_paths"][sid] = output_path
            continue

        print(f"[LipSync] Processing scene {sid} with {len(timing.dialogue_timeline)} segments...")
        
        synced_segments = []
        try:
            full_video = VideoFileClip(v_path)
            
            for i, seg in enumerate(timing.dialogue_timeline):
                seg_v_path = f"data/outputs/synced/scene_{sid}_seg_{i}_v.mp4"
                seg_out_path = f"data/outputs/synced/scene_{sid}_seg_{i}_synced.mp4"
                
                # 1. Extract video part
                start = seg.start_seconds
                end = min(seg.end_seconds, full_video.duration)
                if start >= full_video.duration:
                    continue
                
                sub_clip = full_video.subclip(start, end)
                sub_clip.write_videofile(seg_v_path, codec="libx264", audio=False, logger=None)
                
                # 2. Get the specific audio segment file (created by AudioAgent)
                # Convention: data/outputs/audio/scene_01/segment_0000_speaker.wav
                seg_a_path = f"data/outputs/audio/scene_{int(sid):02d}/segment_{i:04d}_{seg.speaker.lower().replace(' ', '_')}.wav"
                
                if not os.path.exists(seg_a_path):
                    # Fallback to extracting from main audio if segment file missing
                    seg_a_path = f"data/outputs/synced/scene_{sid}_seg_{i}_a.wav"
                    ffmpeg = shutil.which("ffmpeg")
                    subprocess.run([
                        ffmpeg, "-y", "-i", a_path, "-ss", str(start), "-to", str(end),
                        "-c", "copy", seg_a_path
                    ], capture_output=True)

                # 3. Try Wav2Lip on this segment
                wav2lip_dir = os.path.join(os.getcwd(), "Wav2Lip")
                checkpoint = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
                
                if os.path.exists(wav2lip_dir) and os.path.exists(checkpoint):
                    try:
                        subprocess.run([
                            "python", os.path.join(wav2lip_dir, "inference.py"),
                            "--checkpoint_path", checkpoint,
                            "--face", seg_v_path,
                            "--audio", seg_a_path,
                            "--outfile", seg_out_path,
                            "--nosmooth" # Often better for short segments
                        ], check=True, capture_output=True)
                        synced_segments.append(VideoFileClip(seg_out_path))
                        continue
                    except Exception as e:
                        print(f"[LipSync] Wav2Lip failed for segment {i}: {e}")
                
                # Fallback for segment: just mux
                _simple_mux(seg_v_path, seg_a_path, seg_out_path)
                synced_segments.append(VideoFileClip(seg_out_path))

            # 4. Merge all segments
            if synced_segments:
                final_synced = concatenate_videoclips(synced_segments)
                final_synced.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
                state.assets["video_paths"][sid] = output_path
                state.assets["synced_video_paths"][sid] = output_path
            
            full_video.close()
            for s in synced_segments: s.close()

        except Exception as e:
            print(f"[LipSync] Split-sync-merge failed for scene {sid}: {e}. Falling back to simple mux.")
            _simple_mux(v_path, a_path, output_path)
            state.assets["video_paths"][sid] = output_path

    return state

def _simple_mux(v_path, a_path, out_path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg: return
    subprocess.run([
        ffmpeg, "-y", "-i", v_path, "-i", a_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest",
        out_path
    ], check=True, capture_output=True)
