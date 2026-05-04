import re
from typing import Dict, Any, Optional

def classify_intent(query: str) -> Optional[Dict[str, Any]]:
    """
    Parses a query like 'Update scene 2 prompt to: a dark stormy night'.
    Returns a structured intent dict.
    (In production, replace this with an LLM call like Langchain/OpenAI).
    """
    # Simple regex to catch "scene X ... to: Y"
    match = re.search(r'scene\s+(\d+).*?(?:to:|prompt:|to\s|prompt\s)(.*)', query, re.IGNORECASE)
    
    if match:
        scene_id = int(match.group(1))
        new_prompt = match.group(2).strip()
        
        return {
            "target": "video_frame",
            "scene_id": scene_id,
            "action": "update_prompt",
            "value": new_prompt
        }
        
    return None
