import re
from typing import Dict, Any, Optional

def classify_intent(query: str) -> Optional[Dict[str, Any]]:
    """
    Parses a user query to determine the edit intent.
    If it specifies a scene (e.g. 'scene 2 make it rain'), it targets that scene.
    Otherwise, it assumes a global prompt update.
    """
    query = query.strip()
    if not query:
        return None

    # Try to catch "scene X <anything>"
    match = re.search(r'scene\s+(\d+)\s*(.*)', query, re.IGNORECASE)
    
    if match:
        scene_id = int(match.group(1))
        new_prompt = match.group(2).strip()
        # If they just say "scene 2", we need more info, but we'll accept whatever they typed
        if new_prompt:
            return {
                "target": "video_frame",
                "scene_id": scene_id,
                "action": "update_prompt",
                "value": new_prompt
            }
            
    # Fallback: assume it's a general prompt update request or instructions
    return {
        "target": "global",
        "scene_id": None,
        "action": "update_prompt",
        "value": query
    }
