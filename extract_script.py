import json
import os

state_file = 'data/state_versions/v1/state.json'
if os.path.exists(state_file):
    with open(state_file, 'r') as f:
        data = json.load(f)
    
    story = data.get('story', {})
    scenes = story.get('scenes', [])
    
    with open('data/outputs/script.md', 'w', encoding='utf-8') as f:
        f.write('# Generated Script\n\n')
        
        metadata = story.get('character_metadata', {})
        if metadata:
            f.write('## Characters\n')
            for name, meta in metadata.items():
                gender = meta.get("gender", "unknown")
                desc = meta.get("description", "")
                f.write(f'- **{name}** ({gender}): {desc}\n')
            f.write('\n')
            
        for scene in scenes:
            scene_id = scene.get("scene_id")
            location = scene.get("location")
            f.write(f'## Scene {scene_id}: {location}\n')
            for dl in scene.get('dialogue', []):
                speaker = dl.get("speaker")
                line = dl.get("line")
                visual = dl.get("visual_cue")
                f.write(f'**{speaker}**: {line}\n')
                if visual:
                    f.write(f'  *(Visual: {visual})*\n')
            f.write('\n')
    print('Script extracted to data/outputs/script.md')
else:
    print('No state file found.')
