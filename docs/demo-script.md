# Demo Script - Animated Video Generation System

Use this as a spoken demo script. It is written so you can present the system from end to end, while also pointing to the implementation files if asked.

## Opening

Today I’m going to demonstrate an AI-powered animated video generation system. The goal of the project is simple: a user gives a text prompt, and the system turns that prompt into a structured story, character portraits, voice tracks, generated scene videos, lip-synced clips, and a final composed video.

The important idea is that this is not a single script that does everything. It is built as a multi-agent pipeline, and each part of the pipeline has a clear responsibility. The orchestration starts in [backend/app.py](../backend/app.py#L33) and the main workflow is implemented in [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L33).

## Step 1: Prompt Input

I’ll start from the frontend. The user types a prompt into the React dashboard in [frontend/src/App.jsx](../frontend/src/App.jsx#L34). When I click Generate, the `handleGenerate` function sends the prompt to the backend at [frontend/src/App.jsx](../frontend/src/App.jsx#L106).

At this point, the UI is not doing the actual media generation. It is only acting as a control panel and a live monitor. It keeps the interface responsive by polling job status instead of waiting for the whole pipeline to finish on the main thread.

## Step 2: Backend Job Setup

When the backend receives the request, it creates a unique job ID and writes a status file in `data/temp`. That logic is in [backend/app.py](../backend/app.py#L33). The backend then launches the full pipeline in the background, so the request returns immediately and the frontend can keep polling for updates.

This is important for the demo because it shows that the system is asynchronous and event-driven rather than blocking the UI.

## Step 3: Story Generation

The first real AI phase is story generation. The orchestrator calls `run_story_agent` in [agents/story_agent/agent.py](../agents/story_agent/agent.py#L17). That agent is backed by a fallback strategy in [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L23).

The model strategy is:

1. Groq first, if enabled.
2. Ollama second, if enabled.
3. A deterministic local fallback if neither is available.

The Groq model defaults to `llama-3.1-8b-instant`, and the Ollama model defaults to `llama3.1:8b`. The request builders are implemented in [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L110) and [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L158), while the local fallback is at [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L198).

What this gives us is structured output, not just raw text. The story contains scenes, dialogue, locations, character lists, and character metadata.

## Step 4: Character Portraits

Once the story is ready, the orchestrator extracts the unique characters and generates portraits for them. That happens inside [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L33), and the portrait generation function is [mcp/tools/vision_tools/image_gen_tool.py](../mcp/tools/vision_tools/image_gen_tool.py#L6).

The system uses Pollinations.ai to generate character portrait images from the character name and description. These portraits are then shown in the frontend as the cast sheet, which is useful for the demo because it makes the characters feel concrete before the video is even finished.

## Step 5: Audio Generation

The next phase is audio synthesis. The orchestrator calls the audio agent in [agents/audio_agent/agent.py](../agents/audio_agent/agent.py#L13). That agent uses `synthesize_scene_audio` from [mcp/tools/audio_tools/tts_tool.py](../mcp/tools/audio_tools/tts_tool.py#L112).

The audio strategy is gender-aware voice selection. The story output includes character metadata, and the TTS tool uses that metadata to map each character to a suitable Edge-TTS voice. The primary backend is Edge-TTS, and if that fails, the tool falls back to deterministic tone generation so the pipeline still completes.

This is a strong part of the demo because it shows that the system is designed to degrade gracefully instead of failing when a dependency is missing.

## Step 6: Scene Video Generation

After audio is ready, the system generates video scene by scene. The agent for that phase is [agents/video_agent/agent.py](../agents/video_agent/agent.py#L30).

The key idea here is that the video prompt is not just the original user prompt. The agent builds a richer prompt using the scene location, the character list, the character descriptions, and the dialogue visual cues. The prompt builder is at [agents/video_agent/agent.py](../agents/video_agent/agent.py#L6).

The actual generation backend is Wan2GP through Gradio, implemented in [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L73). The tool tries to connect to a local Wan2GP server, switches model family and base type through the Gradio API, submits the prompt, and polls for the generated MP4 file.

If the local video server is unavailable, the system falls back to a mock clip. That means the rest of the pipeline can still be demonstrated even if the GPU service is not online.

## Step 7: Lip Sync

After the scene videos are generated, the lip-sync stage aligns the spoken audio with the scene footage. That phase is implemented in [agents/lipsync_agent/agent.py](../agents/lipsync_agent/agent.py#L85).

The strategy here is Split-Sync-Merge. The agent can divide the scene video into dialogue segments, pair each segment with the corresponding audio, and then recombine the synced segments into a single scene file. The code first tries Wav2Lip in [agents/lipsync_agent/agent.py](../agents/lipsync_agent/agent.py#L59), and if that is unavailable, it falls back to ffmpeg muxing in [agents/lipsync_agent/agent.py](../agents/lipsync_agent/agent.py#L28).

This is important because it prevents a weak lip-sync result from breaking the demo. The system always has a fallback path.

## Step 8: Final Composition

When all scene clips are ready, the system composes the final video in [mcp/tools/video_tools/compositor_tool.py](../mcp/tools/video_tools/compositor_tool.py#L12). That tool stitches the scene clips together into `data/outputs/final_output.mp4` using MoviePy.

At this stage, the system has already generated the content, synced the audio, and prepared the final output. The compositor just assembles the finished sequence.

## Step 9: State Saving, Undo, and Redo

The project also supports editing and version rollback. Versioning is implemented in [state_manager/state_manager.py](../state_manager/state_manager.py#L4) and [state_manager/storage.py](../state_manager/storage.py#L10).

Every time the state is saved, the JSON state and the output assets are copied into `data/state_versions`. That gives the system an undo point. Undo and redo work by restoring a previous version and copying its assets back into the active output folder.

This matters for the demo because it shows the project is not just a one-shot generator. It is a workflow with continuity management and revision support.

## Step 10: Editing a Generated Video

If I type an edit like “scene 2 make it darker” or “make the whole video stormy,” the backend parses that through [agents/edit_agent/intent_classifier.py](../agents/edit_agent/intent_classifier.py#L4).

The edit executor in [agents/edit_agent/executor.py](../agents/edit_agent/executor.py#L36) then saves a snapshot, rebuilds only the affected scene prompt, regenerates the scene video, and recomposites the final output. This avoids rerunning the entire pipeline for a small change.

That is the core edit strategy of the project: preserve continuity, make local changes, and keep the original scene context instead of replacing everything from scratch.

## What The Frontend Shows During The Demo

While the backend is working, the frontend in [frontend/src/App.jsx](../frontend/src/App.jsx#L34) displays the current phase, progress bar, cast portraits, and the final video player.

The phase list is defined at [frontend/src/App.jsx](../frontend/src/App.jsx#L9). The polling loop is at [frontend/src/App.jsx](../frontend/src/App.jsx#L83). The edit submission is at [frontend/src/App.jsx](../frontend/src/App.jsx#L126). Undo and redo are at [frontend/src/App.jsx](../frontend/src/App.jsx#L151) and [frontend/src/App.jsx](../frontend/src/App.jsx#L165).

The styling is handled in [frontend/src/index.css](../frontend/src/index.css#L9), which gives the app its cinematic studio look.

## Short Explanation Of The Architecture

If someone asks for the overall architecture, I would summarize it like this:

The system uses a multi-agent pipeline with a shared state object. The story agent generates structured scenes, the portrait generator creates character references, the audio agent produces speech and timing data, the video agent creates scene footage, the lip-sync agent aligns the audio and video, and the compositor produces the final output. The frontend only coordinates the workflow and displays progress.

## Questions You May Be Asked

### Which models are used?

The story generation path uses Groq with `llama-3.1-8b-instant` by default, Ollama with `llama3.1:8b` as the local LLM fallback, Edge-TTS for voice synthesis, Wan2GP for video generation, and Wav2Lip for lip sync when available.

### What happens if a service is unavailable?

The system is built with fallback behavior. If Groq fails, it tries Ollama. If Ollama is unavailable, it uses a deterministic local story generator. If Edge-TTS fails, it falls back to tone generation. If Wan2GP is offline, it generates a mock video. If Wav2Lip is missing, it uses ffmpeg muxing instead.

### How does editing work without regenerating everything?

The edit flow preserves the original scene context, adds the user’s change as a visual modification, regenerates only the targeted scene when possible, and then recomposites the final output.

### How do undo and redo work?

The state manager stores versioned snapshots of both the structured JSON state and the output assets. Undo and redo restore those saved versions from disk.

## Closing

To close the demo, I would say that this project shows a practical agentic workflow for media generation. It is modular, stateful, fault-tolerant, and designed to keep working even when some dependencies are missing. That makes it useful not just as a prototype, but as a demonstration of how a real multi-stage AI production pipeline can be organized.
