import urllib.parse
import os
import requests
from pathlib import Path

def generate_character_portrait(character_name: str, description: str = "", output_dir: str = "data/outputs/characters") -> str:
    """
    Generates a character portrait using Pollinations.ai.
    Returns the path to the saved image.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Build a descriptive prompt
    prompt = f"Cinematic character portrait of {character_name}. {description}. High quality, detailed face, photorealistic, 8k."
    safe_prompt = urllib.parse.quote(prompt)
    
    image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&nologo=true"
    
    file_path = os.path.join(output_dir, f"{character_name.lower().replace(' ', '_')}.png")
    
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return file_path
    except Exception as e:
        print(f"Error generating image for {character_name}: {e}")
        
    return ""
