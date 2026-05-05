from shared.schemas.state_schema import ProjectState
from state_manager.storage import save_version, load_version, revert_assets

class StateManager:
    def __init__(self):
        pass
        
    def _get_current_ver_path(self):
        import os
        os.makedirs("data", exist_ok=True)
        return "data/current_version.txt"

    def get_current_version(self) -> int:
        path = self._get_current_ver_path()
        import os
        if not os.path.exists(path):
            # Try to infer from state_versions
            latest = self.load_latest_state()
            if latest:
                return latest.version - 1
            return 1
        with open(path, "r") as f:
            return int(f.read().strip())

    def _set_current_version(self, version: int):
        path = self._get_current_ver_path()
        with open(path, "w") as f:
            f.write(str(version))

    def save_state(self, state: ProjectState) -> ProjectState:
        """Saves the current state and increments the version for the NEXT operation."""
        save_version(state)
        self._set_current_version(state.version)
        # Increment version for the active state
        state.version += 1
        return state
        
    def revert_to_version(self, version: int) -> ProjectState:
        """Restores a previous version's state JSON and assets."""
        state = load_version(version)
        revert_assets(version)
        self._set_current_version(version)
        # Prepare the state for new edits by incrementing version
        state.version = version + 1
        return state

    def load_latest_state(self) -> ProjectState | None:
        """Loads the most recently saved state version."""
        from pathlib import Path
        import os
        state_dir = Path("data/state_versions")
        if not state_dir.exists():
            return None
        versions = []
        for d in state_dir.iterdir():
            if d.is_dir() and d.name.startswith("v"):
                try:
                    versions.append(int(d.name[1:]))
                except ValueError:
                    pass
        if not versions:
            return None
        latest = max(versions)
        return load_version(latest)

