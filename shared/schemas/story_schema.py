from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class DialogueLine(BaseModel):
    speaker: str
    line: str
    visual_cue: str = ""

class CharacterMetadata(BaseModel):
    name: str
    gender: str = "male"  # "male" or "female"
    description: str = ""

class Scene(BaseModel):
    scene_id: int
    location: str
    characters: List[str] = Field(default_factory=list)
    character_metadata: Dict[str, CharacterMetadata] = Field(default_factory=dict)
    dialogue: List[DialogueLine] = Field(default_factory=list)

class StoryOutput(BaseModel):
    scenes: List[Scene]
    character_metadata: Dict[str, CharacterMetadata] = Field(default_factory=dict)
