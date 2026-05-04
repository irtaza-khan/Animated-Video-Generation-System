import os
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx import Loop
from shared.schemas.state_schema import ProjectState

def compose_final_video(state: ProjectState, output_path: str = "data/outputs/final_output.mp4"):
    clips = []
    video_paths = state.assets.get("video_paths", {})
    if not video_paths:
        return
        
    timing = state.timing.scene_timings if state.timing else {}

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    for scene in sorted(state.story.scenes, key=lambda x: x.scene_id):
        v_path = video_paths.get(str(scene.scene_id))
        if not v_path or not os.path.exists(v_path):
            continue
            
        clip = VideoFileClip(v_path)
        
        if scene.scene_id in timing:
            scene_timing = timing[scene.scene_id]
            target_duration = scene_timing.duration_ms / 1000.0
            
            if clip.duration < target_duration:
                clip = clip.with_effects([Loop(duration=target_duration)])
            else:
                clip = clip.subclip(0, target_duration)
                
            a_path = scene_timing.audio_filepath
            if a_path and os.path.exists(a_path):
                audio = AudioFileClip(a_path)
                clip = clip.with_audio(audio)
                
        clips.append(clip)
        
    if clips:
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, fps=24)
        state.assets["final_video"] = output_path
