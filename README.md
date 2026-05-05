# AI-Powered Animated Video Generation System

A multi-agent orchestrated pipeline that generates, composites, and iteratively edits AI-generated animated videos from a simple text prompt.

---

## 🏗️ System Architecture

```
User Prompt
    │
    ▼
┌────────────────┐
│  Story Agent   │  Phase 1 — LLM-powered screenplay generation
│  (Groq/Ollama) │  Outputs: StoryOutput (scenes, dialogue, visual cues)
└───────┬────────┘
        ▼
┌────────────────┐
│  Vision Tool   │  Phase 1.5 — Character portrait generation
│ (Pollinations) │  Outputs: Character face images (.png)
└───────┬────────┘
        ▼
┌────────────────┐
│  Audio Agent   │  Phase 2 — Per-scene voice synthesis
│  (Edge-TTS)    │  Outputs: .wav files, TimingManifest
└───────┬────────┘
        ▼
┌────────────────┐
│  Video Agent   │  Phase 3 — AI video generation per scene
│  (Wan2.1/GPU)  │  Outputs: .mp4 clips per scene
└───────┬────────┘
        ▼
┌────────────────┐
│ LipSync Agent  │  Phase 3.5 — Wav2Lip lip-syncing
│   (Wav2Lip)    │  Outputs: Synced .mp4 clips
└───────┬────────┘
        ▼
┌────────────────┐
│  Compositor    │  Phase 4 — Stitch clips + sync audio
│  (MoviePy)     │  Outputs: final_output.mp4
└───────┬────────┘
        ▼
┌────────────────┐
│  Edit Agent    │  Phase 5 — Intent-aware scene editing + Undo
│  (Regex/LLM)   │  Targeted regeneration with state snapshots
└────────────────┘
```

---

## 🔧 Technology Stack & Models

| Component | Technology | Purpose | Reason |
|-----------|-----------|---------|--------|
| **Backend API** | FastAPI + Uvicorn | Async orchestration, background tasks, status polling | High-performance async; native Pydantic support for strict data contracts |
| **Frontend** | Vite + React | Dashboard with progress bar, video player, edit chat | Blazing-fast HMR; lightweight SPA without Next.js overhead |
| **Story Generation** | Groq API (Llama 3.1) → Ollama → Local Fallback | LLM-powered screenplay generation | Free tier Groq is fast; Ollama for offline; deterministic fallback ensures the pipeline never blocks |
| **Character Casting**| Pollinations.ai API | Character portrait generation | Free, fast, no key needed; provides consistent face references |
| **Audio Synthesis** | Edge-TTS (Microsoft) | Per-scene voice synthesis with speaker differentiation | Free, no API key needed, high-quality neural voices, per-character voice mapping |
| **Video Generation** | Wan2.1 via Wan2GP (Pinokio/Gradio) | Text-to-video AI generation | Local GPU inference; avoids expensive API costs; high-quality output |
| **Lip-Syncing**     | Wav2Lip | Syncs character lips to dialogue audio | Industry-standard lip-syncing; fallback to muxing if unavailable |
| **Compositing** | MoviePy | Video stitching, audio muxing, clip looping/trimming | Programmatic video editing; robust A/V sync |
| **Schema Validation** | Pydantic v2 | Strict JSON contracts between agents | Type-safe data flow across all pipeline phases |
| **State Management** | File-based snapshots (shutil) | Versioned undo/redo for edit operations | Robustly snapshots both JSON state and media assets to `data/state_versions/` |

---

## 📂 Project Structure

```
Agentic Project/
├── agents/
│   ├── story_agent/          # Phase 1: LLM screenplay generation
│   │   ├── agent.py          # Entry point: run_story_agent()
│   │   └── llm_providers.py  # Groq, Ollama, local fallback
│   ├── audio_agent/          # Phase 2: Voice synthesis
│   │   └── agent.py          # Entry point: run_audio_agent()
│   ├── video_agent/          # Phase 3: Wan2.1 video generation
│   │   └── agent.py          # Entry point: run_video_agent()
│   ├── lipsync_agent/        # Phase 3.5: Wav2Lip lip-syncing
│   │   └── agent.py          # Entry point: run_lipsync_agent()
│   ├── edit_agent/           # Phase 5: Intent classification + execution
│   │   ├── intent_classifier.py
│   │   └── executor.py
│   └── orchestrator/
│       └── workflow.py       # Full pipeline orchestration
├── backend/
│   └── app.py                # FastAPI endpoints
├── frontend/
│   └── src/
│       ├── App.jsx           # React dashboard
│       └── index.css         # Dark-mode UI styles
├── mcp/tools/
│   ├── video_tools/
│   │   ├── video_gen_tool.py # Wan2GP Gradio integration
│   │   └── compositor_tool.py
│   └── audio_tools/
│       └── tts_tool.py       # Edge-TTS + tone fallback
├── shared/schemas/
│   ├── story_schema.py       # Scene, DialogueLine, StoryOutput
│   ├── audio_schema.py       # AudioTiming, TimingManifest
│   └── state_schema.py       # ProjectState
├── state_manager/
│   ├── state_manager.py      # Versioned save/revert
│   └── storage.py            # Snapshot I/O
├── data/
│   ├── outputs/              # Generated media files
│   ├── temp/                 # Job status JSON files
│   └── state_versions/       # Undo snapshots
├── .env                      # Configuration
└── requirements.txt
```

---

## 🚀 How to Run the Complete Project

### Prerequisites
- Python 3.10+ with pip
- Node.js 18+ with npm
- (Optional) Pinokio with Wan2GP for real AI video generation

### 1. Install Python Dependencies
```bash
# Activate your virtual environment
Agentic-project\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` in the project root:
```env
# Enable Groq for LLM-powered scripts (optional, free tier)
GROQ_ENABLED=1
GROQ_API_KEY=your_groq_api_key_here

# Audio backend (edge_tts is default, no key needed)
STUDIO_FLOOR_VOICE_BACKEND=edge_tts

# Video generation (Wan2GP via Pinokio)
GRADIO_URL=http://127.0.0.1:42003/
```

### 3. Start the Backend (FastAPI)
```bash
# From the Agentic Project root directory
uvicorn backend.app:app --reload
```
The API runs at `http://localhost:8000`

### 4. Start the Frontend (Vite + React)
```bash
# In a new terminal
cd frontend
npm install
npm run dev
```
The UI runs at `http://localhost:5173`

### 5. (Optional) Start Wan2GP via Pinokio
1. Open Pinokio → Launch Wan2GP
2. Verify the Gradio UI loads at `http://127.0.0.1:42003/`
3. If Wan2GP is not running, the system automatically falls back to mock video clips

### 6. Use the Dashboard
- **Generate**: Type a story prompt (e.g., "A spy thriller in a rainy Tokyo alleyway") and click **Generate Video**
- **Watch**: The progress bar tracks each phase: `GENERATING_STORY → GENERATING_AUDIO → GENERATING_VIDEO → COMPOSITING → COMPLETED`
- **Edit**: Use the sidebar chat: "Update scene 1 prompt to: a dark cinematic storm"
- **Undo**: Click the **Undo** button to revert to the previous version

---

## 🧪 Testing

```bash
# Test Story Agent only
python test_story.py

# Test Audio Agent only
python test_audio.py

# Test full pipeline (Story → Audio → Video → Compositor)
python test_full_pipeline.py
```

---

## 📝 Implementation Details

### Story Agent (Phase 1)
The story agent accepts a text prompt and generates a structured `StoryOutput` containing scenes with locations, characters, **character metadata (gender, description)**, and dialogue lines with visual cues. It uses a cascading LLM strategy: **Groq API** (free, fast cloud inference with Llama 3.1) → **Ollama** (local LLM) → **deterministic local generator** (always works, features a 3-act story progression). The explicit extraction of character metadata ensures that downstream agents (Vision & Audio) can properly cast and voice the characters.

### Audio Agent (Phase 2)
The audio agent uses **Edge-TTS** (Microsoft's free neural TTS) to synthesize per-character voice tracks for each scene. It leverages the generated `character_metadata` to dynamically assign distinct, gender-appropriate neural voices (e.g., `en-US-GuyNeural` for male, `en-US-JennyNeural` for female). It generates individual `.mp3` segments, transcodes them to `.wav`, and mixes them into a timeline-aligned audio file.

### Video Agent (Phase 3)
The video agent interfaces with **Wan2.1** running locally via **Wan2GP on Pinokio**. It uses the `gradio_client` library to drive the multi-step Gradio state machine (model selection → queue → prepare → process → finalize polling). Each scene's prompt is built from the `location` and `visual_cue` fields for rich, contextual video generation. If the Gradio server is unreachable, it falls back to generating color clip placeholders via MoviePy.

> [!NOTE]
> **Performance:** On an RTX 3060, video generation takes approximately **10-12 minutes per scene**. The pipeline is designed to be asynchronous so the UI remains responsive during this time, immediately displaying the "Cast Gallery" as soon as character portraits are ready.

### LipSync Agent (Phase 3.5)
The lipsync agent uses a highly robust **Split-Sync-Merge** strategy. Rather than feeding an entire mixed audio track to Wav2Lip (which causes the first detected face to continuously animate regardless of who is speaking), the agent:
1. Slices the generated scene video into precise micro-segments based on the dialogue timeline.
2. Isolates the specific audio track for the currently speaking character.
3. Feeds only the active segment to Wav2Lip to ensure perfectly matched lip movements.
4. Seamlessly concatenates the synced segments back into a fluid scene video.

### State Manager & Edit Agent (Phase 5)
The state manager takes physical snapshots of both the `ProjectState` JSON and the entire `data/outputs/` directory to `data/state_versions/vX/`. The edit agent features a **highly permissive NLP Intent Classifier** that parses natural language commands (e.g., "Update scene 2 prompt to: a dark stormy night", or general "make it rain" commands). It saves an undo point, regenerates **only** the affected scene's video, and seamlessly recomposites the final output in the background.