from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Optional, Dict, Generator, List

from groq import Groq

from extract import extract_blog, ExtractError
from tts_audio import (
    edge_tts_save_mp3,
    load_mp3_as_segment,
    stitch_chapters,
    export_mp3,
    TTSError,
)


class PipelineError(Exception):
    pass


# =========================
# CONFIG
# =========================

GROQ_MODEL = "llama-3.1-8b-instant"   # hardcoded as requested
MAX_BLOG_CHARS = 12000

EDGE_VOICE = "en-US-JennyNeural"
EDGE_RATE = "+0%"
EDGE_VOLUME = "+0%"

WORDS_PER_MINUTE = 150


# =========================
# HELPERS
# =========================

def clean_for_tts(text: str) -> str:
    """
    Removes unwanted meta/stage directions like:
    - Here's the script...
    - [Intro music]
    - Host:
    - (Pause)
    """
    if not text:
        return ""

    # Remove meta intro lines
    text = re.sub(
        r"^here('?s| is)\s+the\s+script.*?:\s*",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )

    # Remove bracket directions
    text = re.sub(r"\[.*?\]", " ", text)
    text = re.sub(r"\(.*?\)", " ", text)

    # Remove speaker labels like Host:
    text = re.sub(r"^\s*\w+\s*:\s*", "", text, flags=re.MULTILINE)

    # Remove short stage-direction lines
    bad_keywords = [
        "intro music",
        "outro music",
        "music plays",
        "music continues",
        "pause",
        "background music",
    ]

    cleaned_lines = []
    for line in text.splitlines():
        l = line.strip()
        if not l:
            continue
        low = l.lower()
        if any(k in low for k in bad_keywords) and len(l) < 80:
            continue
        cleaned_lines.append(l)

    text = " ".join(cleaned_lines)
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text


def _groq_text(
    groq_api_key: str,
    prompt: str,
    max_tokens: int = 900,
    temperature: float = 0.35,
) -> str:
    try:
        client = Groq(api_key=groq_api_key)
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional podcast script writer."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        msg = str(e)
        if "rate_limit_exceeded" in msg:
            raise PipelineError(
                "Groq rate/token limit exceeded. Try shorter article or fewer minutes."
            ) from e
        raise PipelineError(f"Groq request failed: {e}") from e


def _get_source_content(
    url: Optional[str],
    pasted_title: Optional[str],
    pasted_text: Optional[str],
) -> Dict[str, str]:
    if pasted_text:
        return {
            "title": pasted_title or "Pasted Article",
            "text": pasted_text,
            "url": url or "",
            "input_mode": "pasted_text",
        }

    if not url:
        raise PipelineError("No URL provided and no pasted text provided.")

    try:
        blog = extract_blog(url)
        return {
            "title": blog["title"],
            "text": blog["text"],
            "url": url,
            "input_mode": "url",
        }
    except ExtractError as e:
        raise PipelineError(
            f"{e}\n\nThis site likely blocks scraping. Use 'Paste Blog Text' mode."
        ) from e


# =========================
# MAIN STREAM GENERATOR
# =========================

def generate_podcast_stream(
    *,
    url: Optional[str],
    pasted_title: Optional[str],
    pasted_text: Optional[str],
    groq_api_key: str,
    style: str,
    target_minutes: int,
    gap_ms: int,
    out_final_mp3_path: str,
    outputs_dir: str,
    run_id: str,
) -> Generator[Dict, None, None]:

    target_minutes = int(max(2, min(10, target_minutes)))
    parts = max(1, math.ceil(target_minutes / 2))

    total_words = target_minutes * WORDS_PER_MINUTE
    words_per_part = max(220, int(math.ceil(total_words / parts)))

    yield {"type": "status", "message": "Getting article content..."}

    src = _get_source_content(url, pasted_title, pasted_text)
    title = src["title"]
    text = (src["text"] or "").strip()
    source_url = src["url"]
    input_mode = src["input_mode"]

    if len(text) < 300:
        raise PipelineError("Input text too short.")

    text = text[:MAX_BLOG_CHARS]

    out_dir = Path(outputs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    temp_mp3_files: List[Path] = []

    # Generate each part
    for i in range(1, parts + 1):

        yield {"type": "status", "message": f"Generating script for Part {i}/{parts}..."}

        prompt = f"""
Write Part {i} of {parts} of a podcast episode.

Topic: {title}
Style: {style}
Target length: about {words_per_part} words.

IMPORTANT RULES:
- Write ONLY spoken narration text.
- DO NOT include stage directions like [Intro music] or (Pause).
- DO NOT include labels like Host: or Narrator:
- DO NOT say "Here's the script".
- DO NOT include markdown or JSON.
- Use ONLY information from the source text.
- Make it natural and conversational.

SOURCE TEXT:
\"\"\"{text}\"\"\"
"""
        part_text = _groq_text(groq_api_key, prompt)

        # Expand once if too short
        if len(part_text.split()) < int(words_per_part * 0.65):
            yield {"type": "status", "message": f"Expanding Part {i}..."}

            expand_prompt = f"""
Expand this to about {words_per_part} words.
No stage directions.
No speaker labels.
Only spoken narration.

TEXT:
\"\"\"{part_text}\"\"\"
"""
            expanded = _groq_text(groq_api_key, expand_prompt, temperature=0.25)
            if expanded.strip():
                part_text = expanded.strip()

        # Clean before TTS
        part_text = clean_for_tts(part_text)

        yield {"type": "status", "message": f"Generating audio for Part {i}/{parts}..."}

        part_title = f"Part {i}"  # UI label only (NOT spoken)
        temp_mp3 = out_dir / f"_tmp_{run_id}_part_{i}.mp3"

        # ✅ FIX: do NOT prepend "Part i" into the spoken audio
        edge_tts_save_mp3(
            text=part_text,
            voice=EDGE_VOICE,
            out_path=str(temp_mp3),
            rate=EDGE_RATE,
            volume=EDGE_VOLUME,
        )

        temp_mp3_files.append(temp_mp3)

        yield {
            "type": "part_ready",
            "episode_title": title,
            "part_index": i,
            "parts_total": parts,
            "part_title": part_title,  # UI only
            "script": part_text,
            "mp3_path": str(temp_mp3),
        }

    # Stitch full audio
    yield {"type": "status", "message": "Stitching full episode..."}

    try:
        segments = [load_mp3_as_segment(str(p)) for p in temp_mp3_files]
        full = stitch_chapters(segments, gap_ms=gap_ms)
        export_mp3(full, out_final_mp3_path)
    except TTSError as e:
        raise PipelineError(str(e)) from e

    # Cleanup temp files
    for p in temp_mp3_files:
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    yield {
        "type": "final_ready",
        "final_mp3_path": out_final_mp3_path,
        "_source_url": source_url,
        "_target_minutes": target_minutes,
        "_parts": parts,
        "_words_per_part_target": words_per_part,
        "_groq_model": GROQ_MODEL,
        "_tts_voice": EDGE_VOICE,
        "_input_mode": input_mode,
    }