from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from .story_schema import StoryOutput
from .audio_schema import TimingManifest

class ProjectState(BaseModel):
    version: int = 1
    story: Optional[StoryOutput] = None
    timing: Optional[TimingManifest] = None
    assets: Dict[str, Any] = Field(default_factory=dict)
