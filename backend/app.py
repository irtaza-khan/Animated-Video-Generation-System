import uuid
import json
import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agents.orchestrator.workflow import run_full_pipeline

app = FastAPI(title="Video Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("data/outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="data/outputs"), name="outputs")


class GenerateRequest(BaseModel):
    prompt: str
    num_scenes: int = 3


class EditRequest(BaseModel):
    query: str


@app.post("/api/generate")
async def generate_video(request: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    # Write initial status
    os.makedirs("data/temp", exist_ok=True)
    with open(f"data/temp/{job_id}.json", "w") as f:
        json.dump({"status": "queued", "progress": 0}, f)

    # Trigger background task with just the prompt
    background_tasks.add_task(run_full_pipeline, job_id, request.prompt, request.num_scenes)

    return {"job_id": job_id, "status": "processing"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    try:
        with open(f"data/temp/{job_id}.json", "r") as f:
            status_data = json.load(f)
        return status_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@app.post("/api/edit")
async def edit_video(request: EditRequest, background_tasks: BackgroundTasks):
    from agents.edit_agent.intent_classifier import classify_intent

    intent = classify_intent(request.query)
    print(f"[DEBUG] EditRequest received query: '{request.query}', Intent parsed: {intent}")
    if not intent:
        raise HTTPException(status_code=400, detail="Could not understand edit intent")

    job_id = str(uuid.uuid4())
    os.makedirs("data/temp", exist_ok=True)
    with open(f"data/temp/{job_id}.json", "w") as f:
        json.dump({"status": "queued", "progress": 0}, f)

    def run_edit_task(j_id: str, parsed_intent: dict):
        try:
            from state_manager.state_manager import StateManager
            from agents.edit_agent.executor import execute_edit
            
            with open(f"data/temp/{j_id}.json", "w") as f:
                json.dump({"status": "processing_edit", "progress": 10}, f)
                
            sm = StateManager()
            state = sm.load_latest_state()
            if not state:
                raise ValueError("No active project state found")
                
            state = execute_edit(state, parsed_intent, sm)
            sm.save_state(state)
            
            with open(f"data/temp/{j_id}.json", "w") as f:
                json.dump({"status": "completed", "progress": 100}, f)
        except Exception as e:
            with open(f"data/temp/{j_id}.json", "w") as f:
                json.dump({"status": "error", "progress": 0, "error": str(e)}, f)

    background_tasks.add_task(run_edit_task, job_id, intent)
    return {"job_id": job_id, "status": "processing", "intent": intent}


@app.post("/api/undo")
async def undo_edit():
    from state_manager.state_manager import StateManager
    sm = StateManager()
    try:
        sm.revert_to_version(1)
        return {"status": "success", "message": "Reverted to previous version"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
