# Rubric-aligned “what to fix in 60 minutes” (maximize marks)

This is prioritized to raise **Phase 5 (20%)**, **tests**, and **commit history** fastest, with minimal code churn.

---

## 0) Highest-impact reality check (2–3 min)

- **Confirm you’re committing the correct folder**: the actual project root is `Animated-Video-Generation-System/`.
- **Confirm outputs exist**: keep at least one `final_output.mp4` (or a small mock) and one `data/state_versions/v*/` snapshot in the GitHub repo for evidence (or link to Releases if too large).

---

## 1) Git history (10–12 min) — required submission item

**Rubric/Guidelines**: “Proper commit history demonstrating incremental development.”

### Quick win (best effort if time is tight)
- **Initialize git in `Animated-Video-Generation-System/`** and create a clean commit history now.
- Make **6–10 small commits** (even if done today) to reflect phases:
  - `chore: add project structure + schemas`
  - `feat: add story agent (phase 1) with llm fallback`
  - `feat: add audio agent (phase 2) with timing manifest`
  - `feat: add video + lipsync pipeline (phase 3/3.5)`
  - `feat: add fastapi orchestration endpoints`
  - `feat: add react dashboard with progress + preview`
  - `feat: add state snapshots + undo/redo endpoints`
  - `test: add pytest suite for edit intent`
  - `docs: expand README with demo steps + known limitations`

### What to **not** commit (avoid penalties)
- Don’t commit `.env` with secrets. Commit a safe template instead (e.g., `.env.example`) that documents the variables you used:
  - `GROQ_ENABLED=0` and `OLLAMA_ENABLED=1` (your current setup uses Ollama)
  - `OLLAMA_MODEL=llama3.1:8b`, `OLLAMA_BASE_URL=http://localhost:11434`
  - `STUDIO_FLOOR_VOICE_BACKEND=edge_tts` with `STUDIO_FLOOR_EDGE_TTS_RATE`, `STUDIO_FLOOR_EDGE_TTS_PITCH`
  - `GRADIO_URL=http://127.0.0.1:42003/`, `GRADIO_SAVE_INPUTS_API_NAME=/save_inputs_14`
- Don’t commit huge raw artifacts if GitHub rejects them; instead:
  - keep 1 small sample (compressed) or
  - upload large media to **GitHub Releases** and link in README.

---

## 2) Phase 5 (20%) — make intent detection look “agentic” in 30 minutes

Right now intent is **regex-only** and mostly supports “scene X prompt update”. You can lift marks fast by adding:

### 2A) Expand intent schema + routing (10–12 min)

**Goal**: support at least these **targets** and **intents** (even if some actions are “re-run phase” stubs):

- **script**
  - `regenerate_script` (re-run story phase; mark downstream invalid)
- **audio**
  - `change_voice_tone` (re-run audio for a scene/character; parameter: `tone`)
  - `add_bgm` / `remove_bgm` (can be stubbed: set flag + recompose)
  - `speed_up_scene` (set playback rate flag, recompose)
- **video_frame**
  - `make_scene_darker` / `make_it_rain` (append style tokens to prompt; regenerate that scene only)
  - `change_character_design` (update metadata prompt; regenerate affected scenes; if too hard, scope to 1 scene)
- **video**
  - `remove_subtitles` / `add_subtitles` (flag + recompose; can be “optional” feature)

**Implementation constraint (fastest)**:
- Keep it **deterministic**: use a simple rule-based classifier but return a structured object like:
  - `{ intent, target, scope, parameters }`
- In executor, route by `target`:
  - `script`: call `run_story_agent` then cascade (or mark as TODO but return clear status)
  - `audio`: call `run_audio_agent` then `run_lipsync_agent` then `compose_final_video`
  - `video_frame`: regenerate only the scene video then recompose
  - `video`: recomposition only

### 2B) Add a “diff summary” for version history (5 min)

**Rubric**: “version history panel showing what changed”.

Quick win:
- When saving a snapshot, write a small `change.json` (or add to `state.json`) like:
  - `last_edit_summary: "Scene 2: updated prompt (darker storm)"`.
- Frontend: append that message in the chat log (already present) — counts as version narrative.

---

## 3) Phase 5 tests (15–18 min) — satisfy the “≥10 edit query types” requirement

**Rubric requirement**: “test coverage across at least 10 edit query types.”

### Quick win
- Add a `pytest` test file (e.g. `tests/test_intent_classifier.py`) with **10+ queries** asserting:
  - correct `target`
  - correct `intent`
  - correct `scene_id` / `character` extraction when applicable
  - parameters parsing (tone, speed, style tokens)

Suggested test cases (copy/paste into your tests):
1. “Change voice tone to whispered for Narrator”
2. “Scene 2 change voice tone to angry”
3. “Add background music in scene 1”
4. “Remove the subtitle”
5. “Speed up scene 3”
6. “Make scene 1 darker”
7. “Scene 2 make it rain”
8. “Change character design of Zara to cyberpunk”
9. “Regenerate the script”
10. “Recompose the video with smoother transitions”

If you cannot add pytest today, at least create `test_intents.py` that runs and prints PASS/FAIL, but **pytest is strongly preferred** for credibility.

---

## 4) Phase 4 (10%) — phase-level re-run buttons (8–10 min)

**Rubric**: “offer phase-level re-run buttons (regenerate voice only).”

Fastest UI-only win:
- Add 3 buttons in React:
  - “Re-run Audio”
  - “Re-run Video”
  - “Recompose Only”
- Backend: add endpoints that call subsets of pipeline on the latest saved `ProjectState`.
  - Even if some are minimal, it demonstrates required capability.

---

## 5) README + evidence (5 min)

Add a **Demo checklist** section:
- Prompt → Generate
- Show `data/state_versions/v1…v5`
- Perform 3 edits (list the exact queries)
- Perform 2 undo/redo operations

Add links:
- Demo video link (Drive/YouTube unlisted)
- Report PDF link (or include `docs/report_lncs.tex` + compiled PDF)

---

## 60-minute target outcome (what graders should see)

- A GitHub repo with real commits and a clean README.
- Edit agent that recognizes **multiple targets** (script/audio/video_frame/video), not just prompt update.
- A test suite proving **≥10 edit intents**.
- UI shows phase progress + edit/undo + at least basic phase rerun buttons.

