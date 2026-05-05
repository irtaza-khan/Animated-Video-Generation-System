from typing import Dict, Any, List
from shared.schemas.state_schema import ProjectState
from state_manager.state_manager import StateManager
from mcp.tools.video_tools.video_gen_tool import generate_video
from mcp.tools.video_tools.compositor_tool import compose_final_video
from agents.video_agent.agent import _build_video_prompt


def _build_edited_prompt(scene, edit_history: List[str]) -> str:
    """Build a prompt that preserves the original scene context AND layers
    every edit on top as a visual-modification directive.

    Without this, regenerating a scene loses location/character/cinematography
    and the model invents a new scene from the bare edit instruction."""
    base = _build_video_prompt(scene)
    if not edit_history:
        return base
    deltas = ". ".join(f"Visual modification: {e.rstrip('.')}" for e in edit_history)
    return f"{base} {deltas}."


def _regenerate_scene(state: ProjectState, scene, full_prompt: str) -> None:
    """Regenerate a single scene's video, reusing the original seed if known
    so the new clip stays compositionally similar."""
    scene_id = scene.scene_id
    seed = state.assets.get("video_seeds", {}).get(str(scene_id), -1)
    output_path = f"data/outputs/scenes/scene_{scene_id}.mp4"
    print(f"  Regenerating scene {scene_id} (seed={seed if seed != -1 else 'random'})")
    print(f"  Prompt[:120]: {full_prompt[:120]}...")
    used_seed = generate_video(full_prompt, output_path, seed=seed)
    if used_seed is not None:
        state.assets.setdefault("video_seeds", {})[str(scene_id)] = used_seed
    state.assets.setdefault("video_paths", {})[str(scene_id)] = output_path


def execute_edit(state: ProjectState, intent: Dict[str, Any], state_manager: StateManager) -> ProjectState:
    """Apply a parsed edit intent to the project state and regenerate the
    affected scene(s). Edits are layered as deltas on top of the original
    scene description — the original `location` field is never overwritten."""
    state = state_manager.save_state(state)

    target = intent.get("target")
    scene_id = intent.get("scene_id")
    action = intent.get("action")
    value = (intent.get("value") or "").strip()

    if not value or action != "update_prompt":
        print(f"Edit skipped: empty value or unsupported action ({action})")
        return state

    edits_by_scene = state.assets.setdefault("scene_edits", {})

    if target == "video_frame":
        target_scene = next((s for s in state.story.scenes if s.scene_id == scene_id), None)
        if not target_scene:
            print(f"Error: Scene {scene_id} not found.")
            return state

        print(f"Applying edit to Scene {scene_id}: '{value}'")
        edits_by_scene.setdefault(str(scene_id), []).append(value)
        full_prompt = _build_edited_prompt(target_scene, edits_by_scene[str(scene_id)])
        _regenerate_scene(state, target_scene, full_prompt)

    elif target == "global":
        # Apply edit to every scene so the user can say "make it darker" without
        # specifying a scene and expect a uniform global change.
        print(f"Applying global edit across {len(state.story.scenes)} scenes: '{value}'")
        for scene in state.story.scenes:
            sid = str(scene.scene_id)
            edits_by_scene.setdefault(sid, []).append(value)
            full_prompt = _build_edited_prompt(scene, edits_by_scene[sid])
            _regenerate_scene(state, scene, full_prompt)
    else:
        print(f"Edit skipped: unknown target '{target}'")
        return state

    print("Recompositing final video...")
    compose_final_video(state, "data/outputs/final_output.mp4")
    return state
