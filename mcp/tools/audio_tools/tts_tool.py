"""TTS Tool — Voice synthesis per scene.

Uses Edge-TTS (free, no API key) as primary backend,
with a local sine-wave tone fallback.
Ported from Assignment-4 VoiceSynthesisAgent.
"""
from __future__ import annotations

import asyncio
import math
import os
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from shared.schemas.story_schema import Scene

DEFAULT_SECONDS_PER_LINE = 1.8
VOICE_BACKEND = os.getenv("STUDIO_FLOOR_VOICE_BACKEND", "edge_tts").strip().lower()
EDGE_TTS_RATE = os.getenv("STUDIO_FLOOR_EDGE_TTS_RATE", "+0%")
EDGE_TTS_PITCH = os.getenv("STUDIO_FLOOR_EDGE_TTS_PITCH", "+0Hz")

# Default voice mapping
MALE_VOICES = [
    "en-US-GuyNeural",
    "en-GB-RyanNeural",
    "en-AU-WilliamNeural",
]
FEMALE_VOICES = [
    "en-US-JennyNeural",
    "en-GB-SoniaNeural",
    "en-AU-NatashaNeural",
]

def _voice_for_speaker(speaker: str, gender: str = "male") -> str:
    voices = FEMALE_VOICES if gender.lower() == "female" else MALE_VOICES
    index = sum(ord(c) for c in speaker) % len(voices)
    return voices[index]


def _slugify(text: str) -> str:
    return text.replace(" ", "_").lower()


def _speaker_frequency(name: str) -> float:
    return float(180 + sum(ord(c) for c in name) % 240)


def _tone(sample_rate: int, frequency: float, duration: float, amplitude: float) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    carrier = np.sin(2 * np.pi * frequency * t)
    envelope = np.linspace(0.08, 1.0, carrier.size)
    return (amplitude * carrier * envelope).astype(np.float32)


def _write_wavefile(path: Path, waveform: np.ndarray, sample_rate: int) -> None:
    clipped = np.clip(waveform, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def _read_wav_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def _get_ffmpeg_executable() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except Exception as error:
        raise RuntimeError("ffmpeg is required for audio transcoding") from error


def _transcode_to_wav(source: Path, target: Path, sample_rate: int) -> None:
    ffmpeg = _get_ffmpeg_executable()
    subprocess.run(
        [ffmpeg, "-y", "-i", str(source), "-ac", "1", "-ar", str(sample_rate), str(target)],
        check=True, capture_output=True,
    )


def estimate_dialogue_timeline(scene: Scene) -> Tuple[List[dict], float]:
    """Estimate a dialogue timeline from scene dialogue lines."""
    timeline = []
    cursor = 0.0
    for dl in scene.dialogue:
        word_count = max(1, len(dl.line.split()))
        duration = max(DEFAULT_SECONDS_PER_LINE, word_count * 0.25)
        timeline.append({
            "speaker": dl.speaker,
            "line": dl.line,
            "start_seconds": cursor,
            "end_seconds": cursor + duration,
        })
        cursor += duration + 0.18  # pause between lines
    total_duration = cursor if cursor > 0 else 2.0
    return timeline, total_duration


def synthesize_scene_audio(scene: Scene, output_dir: Path, sample_rate: int = 22050) -> dict:
    """Synthesize audio for a scene. Returns dict with path, duration_ms, timeline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    scene_audio_dir = output_dir / f"scene_{scene.scene_id:02d}"
    scene_audio_dir.mkdir(parents=True, exist_ok=True)
    wav_path = scene_audio_dir / "mix.wav"

    timeline, total_duration = estimate_dialogue_timeline(scene)

    # Try Edge-TTS first
    if VOICE_BACKEND in {"edge_tts", "edge-tts", "edge"}:
        try:
            return _synthesize_with_edge_tts(scene, scene_audio_dir, wav_path, output_dir, sample_rate, timeline)
        except Exception as e:
            print(f"[TTS] Edge-TTS failed for scene {scene.scene_id}: {e}. Falling back to tone.")

    # Fallback: deterministic sine-wave tones
    return _synthesize_with_tones(scene, scene_audio_dir, wav_path, output_dir, sample_rate, timeline, total_duration)


def _synthesize_with_edge_tts(
    scene: Scene, scene_audio_dir: Path, wav_path: Path, output_dir: Path,
    sample_rate: int, timeline: List[dict],
) -> dict:
    import edge_tts

    pause_seconds = 0.18
    segments = []
    for index, dl in enumerate(scene.dialogue):
        # Get gender from metadata if available
        gender = "male"
        if hasattr(scene, 'character_metadata') and dl.speaker in scene.character_metadata:
            gender = scene.character_metadata[dl.speaker].gender
        
        voice_name = _voice_for_speaker(dl.speaker, gender)
        mp3_file = scene_audio_dir / f"segment_{index:04d}_{_slugify(dl.speaker)}.mp3"
        comm = edge_tts.Communicate(text=dl.line, voice=voice_name, rate=EDGE_TTS_RATE, pitch=EDGE_TTS_PITCH)
        asyncio.run(comm.save(str(mp3_file)))

        wav_segment = scene_audio_dir / f"segment_{index:04d}_{_slugify(dl.speaker)}.wav"
        _transcode_to_wav(mp3_file, wav_segment, sample_rate)

        with wave.open(str(wav_segment), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
        segments.append((dl.speaker, dl.line, samples))

    if not segments:
        fallback = _tone(sample_rate, 220.0, 1.5, 0.25)
        segments = [("narrator", "", fallback)]

    # Build timeline from actual durations
    actual_timeline = []
    cursor = 0.0
    durations = [len(s[2]) / sample_rate for s in segments]
    total_duration = sum(durations) + max(0, len(segments) - 1) * pause_seconds
    total_samples = max(1, int(math.ceil(total_duration * sample_rate)))
    mix = np.zeros(total_samples, dtype=np.float32)

    for (speaker, line_text, samples), seg_dur in zip(segments, durations):
        start_sample = int(cursor * sample_rate)
        end_sample = min(total_samples, start_sample + samples.size)
        chunk = samples[: end_sample - start_sample]
        mix[start_sample : start_sample + chunk.size] += chunk
        actual_timeline.append({
            "speaker": speaker, "line": line_text,
            "start_seconds": cursor, "end_seconds": cursor + seg_dur,
        })
        cursor += seg_dur + pause_seconds

    mix = np.clip(mix, -1.0, 1.0)
    _write_wavefile(wav_path, mix, sample_rate)

    # Copy to legacy location
    legacy = output_dir / f"scene_{scene.scene_id:02d}.wav"
    shutil.copyfile(wav_path, legacy)

    duration_ms = int(total_duration * 1000)
    subtitle = " | ".join(f"{s}: {l}" for s, l, _ in segments)
    return {
        "audio_filepath": str(wav_path),
        "duration_ms": duration_ms,
        "subtitle_text": subtitle,
        "dialogue_timeline": actual_timeline,
    }


def _synthesize_with_tones(
    scene: Scene, scene_audio_dir: Path, wav_path: Path, output_dir: Path,
    sample_rate: int, timeline: List[dict], total_duration: float,
) -> dict:
    total_samples = max(1, int(math.ceil(total_duration * sample_rate)))
    mix = np.zeros(total_samples, dtype=np.float32)

    for seg in timeline:
        start = int(seg["start_seconds"] * sample_rate)
        end = int(seg["end_seconds"] * sample_rate)
        if end <= start:
            continue
        t = _tone(sample_rate, _speaker_frequency(seg["speaker"]), (end - start) / sample_rate, 0.35)
        chunk = t[: end - start]
        mix[start : start + chunk.size] += chunk

    mix = np.clip(mix, -1.0, 1.0)
    _write_wavefile(wav_path, mix, sample_rate)

    legacy = output_dir / f"scene_{scene.scene_id:02d}.wav"
    shutil.copyfile(wav_path, legacy)

    duration_ms = int(total_duration * 1000)
    subtitle = " | ".join(f"{s['speaker']}: {s['line']}" for s in timeline)
    return {
        "audio_filepath": str(wav_path),
        "duration_ms": duration_ms,
        "subtitle_text": subtitle,
        "dialogue_timeline": timeline,
    }
