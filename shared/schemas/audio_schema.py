from pydantic import BaseModel, Field
from typing import Dict, List

class DialogueSegment(BaseModel):
    speaker: str
    line: str
    start_seconds: float
    end_seconds: float

class AudioTiming(BaseModel):
    audio_filepath: str
    duration_ms: int
    subtitle_text: str
    speaker_tracks: Dict[str, str] = Field(default_factory=dict)
    dialogue_timeline: List[DialogueSegment] = Field(default_factory=list)

class TimingManifest(BaseModel):
    # Mapping from scene_id to AudioTiming
    scene_timings: Dict[int, AudioTiming]
