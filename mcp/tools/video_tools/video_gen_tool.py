import os
import random
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Any
from gradio_client import Client
from moviepy import ColorClip

GRADIO_URL = os.getenv("GRADIO_URL", "http://127.0.0.1:42003/")
GRADIO_SAVE_INPUTS_API_NAME = os.getenv("GRADIO_SAVE_INPUTS_API_NAME", "/save_inputs_14")
MAX_WAIT_SECONDS = int(os.getenv("GRADIO_MAX_WAIT_SECONDS", "900"))
POLL_INTERVAL_SECONDS = float(os.getenv("GRADIO_POLL_INTERVAL_SECONDS", "2"))

def mock_video(output_path: str, prompt: str):
    """Fallback method to create a mock video."""
    print(f"Using mock video for prompt: {prompt}")
    clip = ColorClip(size=(640, 480), color=(50, 50, 150), duration=3)
    clip.write_videofile(output_path, fps=24, logger=None)

def _extract_mp4_path(value: Any) -> Path | None:
    def _check_path(p_str: str) -> Path | None:
        p = Path(p_str)
        if p.suffix.lower() == ".mp4":
            if p.exists(): return p
            pinokio_base = Path("c:/pinokio/api/wan.git/app")
            if (pinokio_base / p).exists(): return pinokio_base / p
            for output_dir in ["output", "outputs"]:
                if (pinokio_base / output_dir / p.name).exists():
                    return pinokio_base / output_dir / p.name
            return p
        return None

    if isinstance(value, str):
        found = _check_path(value)
        if found and found.exists(): return found
    if isinstance(value, Path):
        found = _check_path(str(value))
        if found and found.exists(): return found
    if isinstance(value, dict):
        for nested in value.values():
            found = _extract_mp4_path(nested)
            if found and found.exists(): return found
    if isinstance(value, (list, tuple)):
        for nested in value:
            found = _extract_mp4_path(nested)
            if found and found.exists(): return found

    pinokio_base = Path("c:/pinokio/api/wan.git/app")
    for outputs_dir in ["outputs", "output"]:
        output_path = pinokio_base / outputs_dir
        if output_path.exists() and output_path.is_dir():
            mp4_files = sorted(output_path.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if mp4_files:
                return mp4_files[0]
    return None

def _build_save_inputs_args(client: Client, prompt: str, api_name: str, seed: int) -> list[Any]:
    for endpoint in client.endpoints.values():
        if endpoint.api_name == api_name:
            args = []
            for param in endpoint.parameters_info:
                name = param["parameter_name"]
                if name == "prompt": args.append(prompt)
                elif name == "negative_prompt": args.append("")
                elif name == "seed": args.append(seed)
                elif param.get("parameter_has_default"): args.append(param.get("parameter_default"))
                else: args.append(None)
            return args
    return [prompt, "", seed] # Fallback naive

def generate_video(prompt: str, output_path: str, seed: int = -1) -> int:
    """Attempts to generate a video via Wan2GP Gradio; falls back if unavailable.

    Returns the seed actually used. Pass seed=-1 (default) to pick a random one;
    pass a stored seed to keep regenerations compositionally similar."""
    if seed is None or seed < 0:
        seed = random.randint(0, 2**31 - 1)
    try:
        # Fast check if server is up (socket-level, 2 second timeout)
        import socket
        host = GRADIO_URL.replace("http://", "").replace("https://", "").rstrip("/")
        host_parts = host.split(":")
        sock_host = host_parts[0]
        sock_port = int(host_parts[1]) if len(host_parts) > 1 else 80
        sock = socket.create_connection((sock_host, sock_port), timeout=2)
        sock.close()
        client = Client(GRADIO_URL)
        
        try: client.predict("wan", api_name="/change_model_family")
        except: pass
        try: client.predict("wan", "t2v_1.3B", api_name="/change_model_base_types")
        except: pass
        try: client.predict("t2v_1.3B", api_name="/change_model")
        except: pass
        
        args = _build_save_inputs_args(client, prompt, GRADIO_SAVE_INPUTS_API_NAME, seed)
        client.predict(*args, api_name=GRADIO_SAVE_INPUTS_API_NAME)
        client.predict(api_name="/init_generate")
        try:
            client.predict(0, "t2v_1.3B", api_name="/process_prompt_and_add_tasks")
        except: pass
        client.predict(api_name="/prepare_generate_video")
        try: client.predict(api_name="/process_tasks")
        except: pass
        
        deadline = time.time() + MAX_WAIT_SECONDS
        mp4_path = None
        while time.time() < deadline:
            try:
                res = client.predict(api_name="/finalize_generation")
                mp4_path = _extract_mp4_path(res)
                if mp4_path and mp4_path.exists(): break
            except Exception:
                pass
            time.sleep(POLL_INTERVAL_SECONDS)
            
        if mp4_path and mp4_path.exists():
            shutil.copy(str(mp4_path), output_path)
            print(f"Generated video via Wan2.1 (seed={seed}): {output_path}")
        else:
            raise Exception("Timeout waiting for generation")

    except Exception as e:
        print(f"Wan2GP generation failed ({e}). Falling back to mock.")
        mock_video(output_path, prompt)

    return seed
