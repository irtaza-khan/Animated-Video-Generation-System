"""LLM provider functions for script generation.

Fallback chain: Groq -> Ollama -> Local deterministic generator.
Ported from Assignment-3 src/main.py.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GROQ_ENABLED = os.getenv("GROQ_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip().rstrip("/")
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty model output")
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate, flags=re.IGNORECASE).strip()
        if candidate.endswith("```"):
            candidate = candidate[:-3].strip()
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(candidate[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Could not parse JSON object from model output")


def _normalize_script_payload(raw_payload: Dict[str, Any], fallback_prompt: str) -> Dict[str, Any]:
    scenes = raw_payload.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Model output missing non-empty 'scenes' array")
    normalized_scenes: List[Dict[str, Any]] = []
    for idx, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            continue
        location = str(scene.get("location", "")).strip() or f"{fallback_prompt} - Scene {idx}"
        dialogue_raw = scene.get("dialogue", [])
        dialogue: List[Dict[str, str]] = []
        if isinstance(dialogue_raw, list):
            for item in dialogue_raw:
                if not isinstance(item, dict):
                    continue
                speaker = str(item.get("speaker", "Narrator")).strip() or "Narrator"
                line = str(item.get("line", "...")).strip() or "..."
                visual_cue = str(item.get("visual_cue", "Cinematic framing")).strip() or "Cinematic framing"
                dialogue.append({"speaker": speaker, "line": line, "visual_cue": visual_cue})
        if not dialogue:
            dialogue = [
                {"speaker": "Narrator", "line": "The scene begins.", "visual_cue": "Wide establishing shot"},
            ]
        characters_raw = scene.get("characters", [])
        characters: List[str] = []
        if isinstance(characters_raw, list):
            characters = [str(name).strip() for name in characters_raw if str(name).strip()]
        if not characters:
            seen = set()
            for dl in dialogue:
                s = dl.get("speaker", "").strip()
                if s and s not in seen:
                    seen.add(s)
                    characters.append(s)
        normalized_scenes.append({
            "scene_id": idx,
            "location": location,
            "characters": characters,
            "dialogue": dialogue,
        })
    if not normalized_scenes:
        raise ValueError("No valid scenes found in model output")
    return {"scenes": normalized_scenes}


def make_script_via_groq(payload: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(payload.get("prompt", "Story")).strip() or "Story"
    num_scenes = int(payload.get("num_scenes", 3))
    revision_feedback = str(payload.get("revision_feedback", "")).strip()

    system_instruction = (
        "You are a screenplay planner. Return ONLY valid JSON with this shape: "
        "{\"scenes\": [{\"scene_id\": int, \"location\": str, \"characters\": [str], "
        "\"dialogue\": [{\"speaker\": str, \"line\": str, \"visual_cue\": str}]}]}."
    )
    user_prompt = (
        f"Generate exactly {num_scenes} scenes for this story prompt: {prompt}. "
        "Keep dialogue concise, cinematic, and different across scenes. "
        "Include strong visual cues."
    )
    if revision_feedback:
        user_prompt += f" Apply this revision feedback: {revision_feedback}."

    request_body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1200,
    }
    req = urllib.request.Request(
        url=f"{GROQ_BASE_URL}/chat/completions",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        response_payload = json.loads(resp.read().decode("utf-8"))
    content = (
        response_payload.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    parsed = _extract_json_from_text(str(content))
    return _normalize_script_payload(parsed, prompt)


def make_script_via_ollama(payload: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(payload.get("prompt", "Story")).strip() or "Story"
    num_scenes = int(payload.get("num_scenes", 3))
    revision_feedback = str(payload.get("revision_feedback", "")).strip()

    system_instruction = (
        "You are a screenplay planner. Return ONLY valid JSON with this shape: "
        "{\"scenes\": [{\"scene_id\": int, \"location\": str, \"characters\": [str], "
        "\"dialogue\": [{\"speaker\": str, \"line\": str, \"visual_cue\": str}]}]}."
    )
    user_prompt = (
        f"Generate exactly {num_scenes} scenes for this story prompt: {prompt}. "
        "Keep dialogue concise, cinematic, and different across scenes. "
        "Include strong visual cues."
    )
    if revision_feedback:
        user_prompt += f" Apply this revision feedback: {revision_feedback}."

    request_body = {
        "model": OLLAMA_MODEL,
        "system": system_instruction,
        "prompt": user_prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.7},
    }
    req = urllib.request.Request(
        url=f"{OLLAMA_BASE_URL}/api/generate",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        response_payload = json.loads(resp.read().decode("utf-8"))
    content = response_payload.get("response", "")
    parsed = _extract_json_from_text(str(content))
    return _normalize_script_payload(parsed, prompt)


def make_script_local(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic local script generator — no external API needed.
    Provides a 3-act structure to avoid repetitive dialogue.
    """
    prompt = payload.get("prompt", "Story")
    num_scenes = int(payload.get("num_scenes", 3))
    
    # Simple progression templates to avoid repetition
    progression = {
        1: [
            "This is the place. Keep your eyes open.",
            "I'm scanning the area now. Looks clear."
        ],
        2: [
            "We have a problem. They know we're here.",
            "Stand your ground. We aren't leaving without it."
        ],
        3: [
            "We got it. Let's move before backup arrives.",
            "Copy that. I'm right behind you."
        ]
    }

    scenes: List[Dict[str, Any]] = []
    character_metadata = {
        "Agent A": {"name": "Agent A", "gender": "male", "description": "A sharp-looking man in a black suit"},
        "Agent B": {"name": "Agent B", "gender": "female", "description": "A mysterious woman in a trench coat"},
    }
    
    for idx in range(1, num_scenes + 1):
        lines = progression.get(idx if idx <= 3 else 3)
        cue_a = "Close-up, tense lighting" if idx % 2 else "Wide shot, cinematic framing"
        cue_b = "Tracking shot, low contrast" if idx % 2 else "Side light, controlled motion"
        
        dialogue = [
            {"speaker": "Agent A", "line": lines[0], "visual_cue": cue_a},
            {"speaker": "Agent B", "line": lines[1], "visual_cue": cue_b},
        ]
        
        scenes.append({
            "scene_id": idx,
            "location": f"{prompt} - Scene {idx}",
            "characters": ["Agent A", "Agent B"],
            "character_metadata": character_metadata,
            "dialogue": dialogue,
        })
    return {"scenes": scenes, "character_metadata": character_metadata}

