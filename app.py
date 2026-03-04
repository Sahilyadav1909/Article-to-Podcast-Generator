import os
import json
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from pipeline import generate_podcast_stream, PipelineError

load_dotenv()

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

PODCAST_STYLE = "Friendly explainer"
GAP_MS = 350

st.set_page_config(page_title="Article to Podcast", layout="wide")

# ✅ Force URL to be empty (this overrides Streamlit remembering old value)
if "article_url" not in st.session_state:
    st.session_state["article_url"] = ""

st.title("🎙️ Article-to-Podcast Generator")
st.write("Paste an article URL → choose duration → generate podcast audio in parts + final stitched MP3.")

if not GROQ_API_KEY:
    st.error("Missing GROQ_API_KEY in .env. Add it and restart the app.")
    st.stop()

url = st.text_input("Article URL", key="article_url")  # ✅ empty by default
target_minutes = st.slider("Podcast length (minutes)", 2, 10, 6, 1)

generate = st.button("Generate Podcast", type="primary")

if generate:
    if not url.strip():
        st.warning("Please paste an article URL first.")
        st.stop()

    run_id = str(uuid.uuid4())[:8]
    final_mp3 = OUT_DIR / f"episode_{run_id}.mp3"
    out_json = OUT_DIR / f"episode_{run_id}.json"

    collected = {
        "episode_title": "",
        "chapters": [],
        "_source_url": url.strip(),
        "_target_minutes": target_minutes,
    }

    progress_box = st.empty()
    parts_container = st.container()
    final_container = st.container()

    try:
        for event in generate_podcast_stream(
            url=url.strip(),
            pasted_title=None,
            pasted_text=None,
            groq_api_key=GROQ_API_KEY,
            style=PODCAST_STYLE,
            target_minutes=target_minutes,
            gap_ms=GAP_MS,
            out_final_mp3_path=str(final_mp3),
            outputs_dir=str(OUT_DIR),
            run_id=run_id,
        ):
            etype = event.get("type")

            if etype == "status":
                progress_box.info(event["message"])

            elif etype == "part_ready":
                part_idx = event["part_index"]
                parts_total = event["parts_total"]
                part_title = event["part_title"]
                mp3_path = event["mp3_path"]
                script = event["script"]

                with parts_container:
                    st.subheader(f"{part_title} ({part_idx}/{parts_total})")
                    st.audio(Path(mp3_path).read_bytes(), format="audio/mp3")
                    with st.expander("View script"):
                        st.write(script)

                if not collected["episode_title"]:
                    collected["episode_title"] = event.get("episode_title", "Podcast Episode")
                collected["chapters"].append({"title": part_title, "script": script})

            elif etype == "final_ready":
                progress_box.success("Done ✅ Full episode is ready.")

                with final_container:
                    st.subheader("Full Episode")
                    audio_bytes = Path(event["final_mp3_path"]).read_bytes()
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        "Download MP3",
                        data=audio_bytes,
                        file_name=Path(event["final_mp3_path"]).name,
                        mime="audio/mpeg",
                    )

                collected["_groq_model"] = event.get("_groq_model")
                collected["_tts_voice"] = event.get("_tts_voice")
                collected["_parts"] = event.get("_parts")
                collected["_words_per_part_target"] = event.get("_words_per_part_target")

                out_json.write_text(json.dumps(collected, ensure_ascii=False, indent=2), encoding="utf-8")
                st.download_button(
                    "Download Script JSON",
                    data=out_json.read_bytes(),
                    file_name=out_json.name,
                    mime="application/json",
                )

    except PipelineError as e:
        progress_box.error(str(e))
        st.info("Tip: If you get 403 Forbidden, that website blocks scraping. Try Wikipedia or a simpler static page.")
    except Exception as e:
        progress_box.error("Unexpected error (copy this and send it to me):")
        st.code(str(e))