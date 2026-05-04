import os
import json
import shutil
from pathlib import Path
from shared.schemas.state_schema import ProjectState

STATE_DIR = Path("data/state_versions")
ACTIVE_DIR = Path("data/outputs")

def save_version(state: ProjectState) -> int:
    version = state.version
    version_dir = STATE_DIR / f"v{version}"
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the JSON state
    state_file = version_dir / "state.json"
    with open(state_file, "w") as f:
        f.write(state.model_dump_json(indent=2))
        
    # Snapshot assets
    assets_dir = version_dir / "assets"
    if ACTIVE_DIR.exists():
        if assets_dir.exists():
            shutil.rmtree(assets_dir)
        shutil.copytree(ACTIVE_DIR, assets_dir)
        
    return version

def load_version(version: int) -> ProjectState:
    version_dir = STATE_DIR / f"v{version}"
    state_file = version_dir / "state.json"
    
    if not state_file.exists():
        raise FileNotFoundError(f"Version {version} not found.")
        
    with open(state_file, "r") as f:
        data = json.load(f)
    return ProjectState(**data)

def revert_assets(version: int):
    version_dir = STATE_DIR / f"v{version}"
    assets_dir = version_dir / "assets"
    
    if not assets_dir.exists():
        return
        
    if ACTIVE_DIR.exists():
        shutil.rmtree(ACTIVE_DIR)
    shutil.copytree(assets_dir, ACTIVE_DIR)
