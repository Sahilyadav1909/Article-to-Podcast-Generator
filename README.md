# 🎙️ Article-to-Podcast Generator

Convert any web article into a narrated podcast using Generative AI.

This project takes an article URL, extracts the readable content, uses a Large Language Model (LLM) to generate a podcast-style narration script, converts the script into audio using neural Text-to-Speech, and finally stitches all audio segments into a complete podcast episode.

The application provides a simple **Streamlit web interface** that allows users to generate podcast audio from articles within seconds.

---

# 🎯 Overview

The **Article-to-Podcast Generator** automatically transforms written content into podcast episodes.

The system performs the following steps:

1. Extracts readable article content from a URL  
2. Uses an LLM to rewrite the article into a podcast narration script  
3. Splits the script into multiple audio segments  
4. Converts each segment into speech using neural TTS  
5. Combines all segments into one final podcast episode  

This enables users to quickly convert blogs, articles, and documentation pages into audio content.

---

# 🏗️ Architecture

```
                 ┌───────────────────┐
                 │   Article URL     │
                 └─────────┬─────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Article Extraction    │
              │   (Clean text content)  │
              └─────────┬───────────────┘
                        │
                        ▼
            ┌─────────────────────────────┐
            │  LLM Script Generation      │
            │  Llama-3 via Groq API       │
            └─────────┬───────────────────┘
                      │
                      ▼
           ┌──────────────────────────────┐
           │   Script Segmentation        │
           │  Split into podcast parts    │
           └─────────┬────────────────────┘
                     │
                     ▼
          ┌───────────────────────────────┐
          │   Text-to-Speech Generation   │
          │      Microsoft Edge TTS       │
          └─────────┬─────────────────────┘
                    │
                    ▼
            ┌───────────────────────────┐
            │     Audio Stitching       │
            │   Merge segments → MP3    │
            └─────────┬─────────────────┘
                      │
                      ▼
              ┌───────────────────┐
              │  Final Podcast    │
              │  Downloadable MP3 │
              └───────────────────┘
```

---

# 🧩 Core Components

## 1. Article Extraction

The application extracts the **main readable content** from an article URL.

This step removes unnecessary elements such as:

- navigation menus  
- advertisements  
- scripts and styles  
- sidebars and page layouts  

Only the meaningful article text is passed to the AI model.

Implemented in:

```
extract.py
```

---

## 2. Large Language Model (LLM)

The extracted article text is converted into a **podcast narration script** using a Large Language Model.

### Model
```
llama-3.1-8b-instant
```

### Provider
```
Groq API
```

### Responsibilities

The LLM:

- rewrites the article into spoken narration
- removes non-spoken elements
- produces conversational explanations
- ensures the text sounds natural when spoken

Example prompt used:

```
Write a podcast narration based on the article below.

Rules:
- Only spoken narration
- No stage directions
- No speaker labels
- Keep the explanation natural and conversational
```

---

## 3. Script Segmentation

The generated script is divided into smaller segments depending on the selected podcast length.

Each segment typically produces **1.5 – 2 minutes of audio**.

Example:

| Podcast Length | Number of Parts |
|----------------|-----------------|
| 2 minutes      |     1 part      |
| 4 minutes      |     2 parts     |
| 6 minutes      |     3 parts     |
| 10 minutes     |     5 parts     |

This approach allows:

- faster generation
- progressive playback
- manageable audio segments

---

## 4. Text-to-Speech (TTS)

Each script segment is converted into speech using **Microsoft Edge TTS**.

Voice model used:

```
en-US-JennyNeural
```

Advantages:

- high-quality neural voice
- natural pronunciation
- fast generation
- free to use

Each segment is saved as an **MP3 file**.

---

## 5. Audio Stitching

All generated audio segments are combined into a single podcast episode.

The final podcast is stored inside the `outputs/` folder.

Example output:

```
outputs/episode_9a3f7c1.mp3
```

---

# 🖥️ User Interface

The application provides a **simple web interface built with Streamlit**.

Users can:

1. Paste an article URL  
2. Select podcast duration  
3. Click **Generate Podcast**

The interface then:

- generates each audio segment
- allows playback of each part
- creates the final stitched podcast
- allows downloading the final MP3

---

# 📂 Project Structure

```
article-to-podcast-generator
│
├── app.py
│   Streamlit user interface
│
├── pipeline.py
│   Main orchestration pipeline
│
├── extract.py
│   Extracts readable article content
│
├── tts_audio.py
│   Text-to-speech generation and audio merging
│
├── outputs/
│   Stores generated podcast files
│
├── .env
│   API key configuration
│
├── requirements.txt
│   Python dependencies
│
└── README.md
```

---

# ⚙️ Tech Stack

**Programming Language**

Python

**AI Model**

Llama-3.1-8B (Groq API)

**Text-to-Speech**

Microsoft Edge TTS

**Web Interface**

Streamlit

**Supporting Libraries**

- requests  
- pydub  
- python-dotenv  
- streamlit  

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Sahilyadav1909/article-to-podcast-generator.git

cd article-to-podcast-generator
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate it.

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file.

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a Groq API key from:

```
https://console.groq.com
```

---

# ▶️ Running the Application

Start the Streamlit server:

```bash
streamlit run app.py
```

Open in browser:

```
http://localhost:8501
```

---

# 🎧 Example Workflow

1. Paste an article URL  
2. Choose podcast duration (2–10 minutes)  
3. Click **Generate Podcast**

The system will:

- extract the article
- generate a podcast narration script
- convert the script into audio
- merge audio segments
- produce a final podcast episode

---

# ⚠️ Limitations

Some websites block scraping and may return errors such as:

```
403 Forbidden
```

If this happens, try using:

- technical blogs
- documentation pages
- static websites
- open articles

---

# 📈 Future Improvements

Possible enhancements:

- RSS feed support for automatic podcast generation  
- multi-speaker podcast conversations  
- background music support  
- voice selection options  
- podcast summarization  
- YouTube narration generation  
- automatic podcast titles and descriptions  

---

# 👨‍💻 Author

**Sahil Yadav**

AI / Generative AI Projects

---

# ⭐ If you like this project

Consider giving the repository a **star ⭐ on GitHub**.
