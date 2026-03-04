from __future__ import annotations

import asyncio
from typing import List

import edge_tts
from pydub import AudioSegment


class TTSError(Exception):
    """Raised when TTS or audio handling fails."""


def _run_async(coro):
    """Run async code safely from sync context (Streamlit friendly)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _edge_save_mp3_async(
    text: str,
    voice: str,
    out_path: str,
    rate: str = "+0%",
    volume: str = "+0%",
) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(out_path)


def edge_tts_save_mp3(
    text: str,
    voice: str,
    out_path: str,
    rate: str = "+0%",
    volume: str = "+0%",
) -> None:
    """
    Generate TTS directly to an MP3 file (most reliable on Windows).
    """
    if not text or len(text.strip()) < 5:
        raise TTSError("TTS text is empty.")
    if not voice:
        raise TTSError("Edge TTS voice is missing.")
    if not out_path:
        raise TTSError("Missing output path for MP3.")

    try:
        _run_async(_edge_save_mp3_async(text=text, voice=voice, out_path=out_path, rate=rate, volume=volume))
    except Exception as e:
        raise TTSError(f"Edge TTS failed: {e}") from e


def load_mp3_as_segment(path: str) -> AudioSegment:
    try:
        return AudioSegment.from_file(path, format="mp3")
    except Exception as e:
        raise TTSError(
            "Could not decode MP3 audio using FFmpeg. "
            "FFmpeg is installed, so this usually means the MP3 file is corrupted/empty."
        ) from e


def stitch_chapters(chapter_segments: List[AudioSegment], gap_ms: int = 350) -> AudioSegment:
    out = AudioSegment.silent(duration=0)
    gap = AudioSegment.silent(duration=max(0, int(gap_ms)))
    for seg in chapter_segments:
        out += seg + gap
    return out


def export_mp3(seg: AudioSegment, path: str, bitrate: str = "192k") -> None:
    try:
        seg.export(path, format="mp3", bitrate=bitrate)
    except Exception as e:
        raise TTSError("Failed to export MP3. Ensure FFmpeg is installed properly.") from e