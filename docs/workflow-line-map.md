# Complete Workflow With Agent And MCP Call Lines

## 1. Entry Flow (Frontend -> Backend -> Orchestrator)

1. Frontend generate action starts at [frontend/src/App.jsx](../frontend/src/App.jsx#L106).
2. Backend generate endpoint receives request at [backend/app.py](../backend/app.py#L33).
3. Backend schedules orchestrator pipeline at [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L33).

## 2. Orchestrator Phase Execution Order

Main orchestrator function:

- [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L33)

Phase-by-phase calls:

1. Story agent call: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L38)
2. Character portrait MCP tool call: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L60)
3. Audio agent call: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L67)
4. Video agent call: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L71)
5. LipSync agent call: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L75)
6. Compositor MCP tool call: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L79)
7. State snapshot save: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L83)

Status update function used across phases:

- [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L12)

## 3. Story Agent And Model Calling Workflow

Story agent entry:

- [agents/story_agent/agent.py](../agents/story_agent/agent.py#L17)

Model routing:

1. Groq check: [agents/story_agent/agent.py](../agents/story_agent/agent.py#L23)
2. Groq call: [agents/story_agent/agent.py](../agents/story_agent/agent.py#L25)
3. Ollama check: [agents/story_agent/agent.py](../agents/story_agent/agent.py#L31)
4. Ollama call: [agents/story_agent/agent.py](../agents/story_agent/agent.py#L33)
5. Local fallback call: [agents/story_agent/agent.py](../agents/story_agent/agent.py#L40)

Provider implementation and endpoints:

1. Groq model config: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L23)
2. Ollama model config: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L26)
3. Groq request function: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L110)
4. Groq endpoint call: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L139)
5. Ollama request function: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L158)
6. Ollama endpoint call: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L186)
7. Local deterministic script function: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L198)

Output guardrails and normalization:

1. JSON extraction: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L30)
2. Payload normalization: [agents/story_agent/llm_providers.py](../agents/story_agent/llm_providers.py#L53)

## 4. MCP Calls Used In Workflow

### 4.1 Vision MCP Tool

1. Imported in orchestrator: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L8)
2. Called in orchestrator loop: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L60)
3. Tool implementation entry: [mcp/tools/vision_tools/image_gen_tool.py](../mcp/tools/vision_tools/image_gen_tool.py#L6)

### 4.2 Audio MCP Tool

1. Called by audio agent: [agents/audio_agent/agent.py](../agents/audio_agent/agent.py#L27)
2. Tool implementation entry: [mcp/tools/audio_tools/tts_tool.py](../mcp/tools/audio_tools/tts_tool.py#L112)
3. Edge-TTS branch: [mcp/tools/audio_tools/tts_tool.py](../mcp/tools/audio_tools/tts_tool.py#L122)
4. Edge-TTS synthesis function: [mcp/tools/audio_tools/tts_tool.py](../mcp/tools/audio_tools/tts_tool.py#L132)
5. Tone fallback function: [mcp/tools/audio_tools/tts_tool.py](../mcp/tools/audio_tools/tts_tool.py#L199)

### 4.3 Video MCP Tool

1. Called by video agent: [agents/video_agent/agent.py](../agents/video_agent/agent.py#L44)
2. Tool implementation entry: [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L73)
3. Gradio client init: [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L89)
4. Model family switch call: [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L91)
5. Model base-type switch call: [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L93)
6. Model selection call: [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L95)
7. Final generation poll: [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L112)
8. Mock fallback call: [mcp/tools/video_tools/video_gen_tool.py](../mcp/tools/video_tools/video_gen_tool.py#L127)

### 4.4 Compositor MCP Tool

1. Imported in orchestrator: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L9)
2. Called in orchestrator: [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L79)
3. Tool implementation entry: [mcp/tools/video_tools/compositor_tool.py](../mcp/tools/video_tools/compositor_tool.py#L12)

## 5. Video Agent Workflow

1. Prompt construction function: [agents/video_agent/agent.py](../agents/video_agent/agent.py#L6)
2. Agent entry function: [agents/video_agent/agent.py](../agents/video_agent/agent.py#L30)
3. Scene video generation call: [agents/video_agent/agent.py](../agents/video_agent/agent.py#L44)

## 6. LipSync Agent Workflow

1. Agent entry function: [agents/lipsync_agent/agent.py](../agents/lipsync_agent/agent.py#L85)
2. ffmpeg mux helper: [agents/lipsync_agent/agent.py](../agents/lipsync_agent/agent.py#L28)
3. Wav2Lip helper: [agents/lipsync_agent/agent.py](../agents/lipsync_agent/agent.py#L59)
4. Segment sync and merge branch starts: [agents/lipsync_agent/agent.py](../agents/lipsync_agent/agent.py#L122)

## 7. Edit Workflow (Intent -> Plan -> Regenerate)

Backend edit endpoints:

1. Edit endpoint: [backend/app.py](../backend/app.py#L58)
2. Undo endpoint: [backend/app.py](../backend/app.py#L98)
3. Redo endpoint: [backend/app.py](../backend/app.py#L112)

Intent parsing:

1. Classifier entry: [agents/edit_agent/intent_classifier.py](../agents/edit_agent/intent_classifier.py#L4)
2. Scene regex parse: [agents/edit_agent/intent_classifier.py](../agents/edit_agent/intent_classifier.py#L15)
3. Scene target assignment: [agents/edit_agent/intent_classifier.py](../agents/edit_agent/intent_classifier.py#L23)
4. Global fallback assignment: [agents/edit_agent/intent_classifier.py](../agents/edit_agent/intent_classifier.py#L31)

Execution and regeneration:

1. Executor entry: [agents/edit_agent/executor.py](../agents/edit_agent/executor.py#L36)
2. Save state before mutation: [agents/edit_agent/executor.py](../agents/edit_agent/executor.py#L40)
3. Scene edits memory map: [agents/edit_agent/executor.py](../agents/edit_agent/executor.py#L51)
4. Scene-target branch: [agents/edit_agent/executor.py](../agents/edit_agent/executor.py#L53)
5. Global-target branch: [agents/edit_agent/executor.py](../agents/edit_agent/executor.py#L64)
6. Recompose after edit: [agents/edit_agent/executor.py](../agents/edit_agent/executor.py#L78)

## 8. State Management Workflow

State manager API:

1. State manager class: [state_manager/state_manager.py](../state_manager/state_manager.py#L4)
2. Save state method: [state_manager/state_manager.py](../state_manager/state_manager.py#L30)
3. Revert method: [state_manager/state_manager.py](../state_manager/state_manager.py#L38)
4. Load latest state: [state_manager/state_manager.py](../state_manager/state_manager.py#L47)

Storage-level snapshot implementation:

1. Save snapshot: [state_manager/storage.py](../state_manager/storage.py#L10)
2. Load snapshot: [state_manager/storage.py](../state_manager/storage.py#L29)
3. Restore assets: [state_manager/storage.py](../state_manager/storage.py#L40)

## 9. Schema Contracts Used Across Agents And MCP Tools

Story schema:

1. DialogueLine: [shared/schemas/story_schema.py](../shared/schemas/story_schema.py#L4)
2. CharacterMetadata: [shared/schemas/story_schema.py](../shared/schemas/story_schema.py#L9)
3. Scene: [shared/schemas/story_schema.py](../shared/schemas/story_schema.py#L14)
4. StoryOutput: [shared/schemas/story_schema.py](../shared/schemas/story_schema.py#L21)

Audio schema:

1. DialogueSegment: [shared/schemas/audio_schema.py](../shared/schemas/audio_schema.py#L4)
2. AudioTiming: [shared/schemas/audio_schema.py](../shared/schemas/audio_schema.py#L10)
3. TimingManifest: [shared/schemas/audio_schema.py](../shared/schemas/audio_schema.py#L17)

Global shared state:

1. ProjectState: [shared/schemas/state_schema.py](../shared/schemas/state_schema.py#L6)

## 10. MCP Architecture Note

MCP tools are actively used via direct imports and function calls from agents and orchestrator.

- Direct MCP import examples:
  - [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L8)
  - [agents/orchestrator/workflow.py](../agents/orchestrator/workflow.py#L9)

Generic MCP runtime scaffold files currently exist but are empty:

- [mcp/base_tool.py](../mcp/base_tool.py)
- [mcp/tool_executor.py](../mcp/tool_executor.py)
- [mcp/tool_registry.py](../mcp/tool_registry.py)
