# 🎵 Multi-Agent Semantic Music Score Generator

A multi-agent pipeline that converts a poem, phrase, or any natural-language text into a complete, printable **LilyPond music score**, with a rendered PDF preview and a synthesized audio playback (WAV), all from a single user interface.

Each stage of the pipeline is an independent **agent** that receives the output of the previous one and produces a *distinct, verifiable JSON contract*. Only the final notation agent calls the Gemini LLM, everything upstream is deterministic, and local.

---

## Features

- **End-to-end generation**: Text → semantic analysis → musical parameters → composition structure → LilyPond code → PDF + audio.
- **Explainable pipeline**: Every intermediate result is shown as structured JSON in its own tab, so you can inspect what each agent decided and why.
- **Deterministic composition**: Agents 1–3 use local NLP and algorithmic rules, so the same input always yields the same musical structure (reproducible scores).
- **LLM-optimized notation**: Agent 4 (Gemini) turns the structured JSON into clean, syntactically-valid LilyPond markup using few-shot technique.
- **Custom MIDI synthesizer**: A dependency-free Python WAV renderer (no external soundfonts required).
- **Runtime API key override**: Each user can supply their own Gemini API key from the sidebar without touching the `.env` file.
- **Preset poem library**: Start from three bundled poetry presets or paste your own text.

---

## How It Works (Pipeline Architecture)

```
   ┌─────────────────────────────────────────────────────────────────┐
   │                    Streamlit UI (app.py)                        │
   │  text + instruments + API key → tabs → files (PDF / WAV)       │
   └──────────────────────────────┬──────────────────────────────────┘
                                  │ user_text, selected_instruments
                                  ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  AGENT 1 — SemanticAgent (semantic_agent.py)                    │
   │  Local NLP: spaCy + DistilBERT sentiment                        │
   │  Input : raw text                                               │
   │  Output: { word_count, themes, emotion{valence,arousal},        │
   │            imagery, movement, atmosphere }                      │
   └──────────────────────────────┬──────────────────────────────────┘
                                  ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  AGENT 2 — MusicalInterpretationAgent (musical_agent.py)        │
   │  Rule-based translator (no LLM)                                 │
   │  Input : semantic JSON + selected instruments                   │
   │  Output: { tempo, key, mode, time_signature, dynamics,          │
   │            instrumentation, density, articulation }             │
   └──────────────────────────────┬──────────────────────────────────┘
                                  ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  AGENT 3 — CompositionAgent (composition_agent.py)              │
   │  Deterministic composer (no LLM)                                │
   │  Input : musical JSON + semantic JSON                           │
   │  Output: { key_signature, melody_motif, chords, total_measures, │
   │            measures: [{measure, harmony, voices}] }             │
   └──────────────────────────────┬──────────────────────────────────┘
                                  ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  AGENT 4 — LilypondAgent (lilypond_agent.py)                    │
   │  Gemini LLM (gemini-2.5-flash) via google-generativeai         │
   │  Input : consolidated JSON from agents 1–3                      │
   │  Output: executable LilyPond (.ly) markup                       │
   └──────────────────────────────┬──────────────────────────────────┘
                                  ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  MusicCompiler (music_compiler.py) + midi_to_wav.py             │
   │  system LilyPond → .ly → .pdf + .mid → PNG preview + .wav       │
   └─────────────────────────────────────────────────────────────────┘
```

---

## The Agents in Detail

### Agent 1 — SemanticAgent (`semantic_agent.py`)

Extracts the *emotional and imagistic content* of the text using **local NLP models only** — no network calls.

| Technique | Purpose |
|---|---|
| `spacy` (`en_core_web_md`) | Part-of-speech tagging, lemmatization, word vectors |
| `distilbert-base-uncased-finetuned-sst-2-english` (HuggingFace) | Sentiment score → valence / arousal |

Derived outputs:

- **`word_count`** — controls the length of the score (more words → more measures).
- **`themes`** — lemmatized nouns / proper nouns.
- **`emotion.valence` / `emotion.arousal`** — mapped from the sentiment confidence; drive key/mode (major vs. minor) and tempo/dynamics later.
- **`imagery`** — adjective–noun phrases (e.g., *"silver lullabies"*).
- **`movement`** — `fast` / `slow` / `moderate`, decided by comparing each verb's word-vector similarity against "fast" and "slow" anchor words.
- **`atmosphere`** — the first adjective in the text (defaults to `"dreamlike"`).

*Fallback:* if `en_core_web_md` is not installed, the agent tries to download it, then falls back to the smaller `en_core_web_sm`.

---

### Agent 2 — MusicalInterpretationAgent (`musical_agent.py`)

A **rule-based music-theory translator** (pure Python, deterministic) that turns the semantic JSON into concrete musical parameters:

- **Key & mode** — high valence (≥ 0.5) → a **major** key (C/G/D/F); low valence → a **minor** key (A/D/E/G).
- **Tempo** — base tempo from movement (`fast` 120, `slow` 56, otherwise 80), adjusted by arousal and clamped to 40–208 BPM.
- **Dynamics** — arousal ≥ 0.7 → `f`, ≥ 0.4 → `mf`, else `p`.
- **Articulation** — `legato` (slow), `staccato` (fast), `tenuto` (moderate).
- **Density** — `arousal * 0.7 + 0.1`, which Agent 3 uses to choose rhythmic complexity.
- **Time signature** — fixed 4/4.

---

### Agent 3 — CompositionAgent (`composition_agent.py`)

The **deterministic composer**. It builds actual pitches, harmonies, and measure-by-measure voices from the parameters above.

- **Key scales** — diatonic scale for each supported key (C, G, D, F major; A, D, E, G minor).
- **Melody motif** — generated deterministically from the poem's theme/imagery words (a word-derived pitch sequence stretched to fit), so output is reproducible across runs.
- **Rhythm cells** — each bar is filled with a rhythm cell from `calm` / `mid` / `dense` pools (chosen by the poem density). Every cell sums to exactly **4 beats** for 4/4 time.
- **Harmony** — each bar is harmonized against a I / IV / V (major) or i / VI / VII (minor) progression, penalizing immediate repeats.
- **Voices** — per-instrument lines:
  - Melodic instruments (Violin, Flute, Clarinet, Oboe) → the melody with beamed 8ths/16ths.
  - Bass instruments (Cello, Viola, Double Bass) → chord-root/fifth whole-notes.
  - **Piano** → split `treble_staff` (melody) + `bass_staff` (block chord).
- **Score length** — `max(4, min(round(word_count / 2), 16))` measures; a breathing rest is inserted every 4th bar.

---

### Agent 4 — LilypondAgent (`lilypond_agent.py`)

The **only agent that calls an LLM**. It consolidates the JSON from agents 1–3 and asks **Gemini (`gemini-2.5-flash`)** for clean, executable LilyPond markup.

- Prompts the model with a strict ruleset: one `\new Staff` per instrument, correct clefs per instrument, PianoStaff split when piano is present, tempo/key/time/dynamics honored, exact note tokens copied verbatim, and **exactly** `total_measures` bars.
- Sanitizes the response: strips accidental markdown code fences and converts invalid `\dynamic f` syntax to proper LilyPond dynamic marks (`\f`, `\p`, `\mp`, …).
- Throws a clear `ValueError` if no API key is configured.
- Exposes **`set_api_key(key)`** so the UI can hot-swap the key at runtime without restarting the app.

---

### Supporting Modules

#### `music_compiler.py` — `MusicCompiler`
- Writes the LilyPond source to `output/output.ly`.
- Invokes the **system LilyPond binary** (`lilypond`) to produce `.pdf` and `.mid`.
- `render_pdf_to_image()` renders the first PDF page to a PNG (via PyMuPDF) for in-app preview.
- `midi_to_wav()` delegates synthesis to the custom renderer.

#### `midi_to_wav.py`
A **dependency-free MIDI → WAV synthesizer**:
- Parses standard MIDI format 0/1 files (variable-length quantities, running status, tempo meta events).
- Converts ticks to seconds using the tempo map.
- Renders each note with a partial-rich tone (fundamental + 6 harmonics), exponential decay envelope, short attack, velocity-based amplitude, and slight stereo panning.
- Normalizes and writes a 44.1 kHz stereo 16-bit WAV, usable directly with `st.audio()`.

---

## Requirements

- **Python 3.8+**
- **System dependencies:**
  - **LilyPond** — the actual notation compiler (required for PDF/MIDI output). Install from <https://lilypond.org> and ensure `lilypond` is on your `PATH`.
- **Python packages** (see `requirements.txt`):
  - streamlit>=1.30.0
  - google-generativeai>=0.3.0
  - python-dotenv>=1.0.0
  - spacy>=3.7.0
  - transformers>=4.35.0
  - torch>=2.0.0
  - abjad>=3.19
  - pymupdf>=1.23.0

---

## Installation

### 1. Clone / open the project

```bash
cd PROJECT
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Download the spaCy model

The pipeline uses word-vector similarity for movement classification, so the medium model is recommended:

```bash
python -m spacy download en_core_web_md
```

*(If missing, the code attempts an automatic download and otherwise falls back to `en_core_web_sm`.)*

### 4. Install LilyPond

- Windows / macOS / Linux: download the installer from <https://lilypond.org/download.html>.
- Make sure `lilypond` resolves from a terminal (`lilypond --version`).

### 5. Create your `.env` file

Create a file named `.env` in the project root:

```
GEMINI_API_KEY=your_key_here
```

---

## Getting a Free Gemini API Key (Google AI Studio)

The Gemini API key is **free** and requires **only a Google account — no credit card, no billing setup**.

1. **Go to Google AI Studio**  
   Open <https://aistudio.google.com/> in your browser.  
   *(Tip: go straight to <https://aistudio.google.com/app/apikey> to skip the landing page.)*

2. **Sign in** with any Google account (Gmail / Workspace / personal). If it's your first visit, accept the Terms of Service when prompted.

3. **Open the API keys page**  
   Click **"Get API key"** in the left-hand menu (or use the direct link above).

4. **Click "Create API key"**  
   A dialog will appear asking about a Google Cloud project.

5. **Pick or create a Google Cloud project**  
   - If you have no project, AI Studio creates one for you automatically, or you can click **Create API key** and follow the dialog to create a new project.  
   - **No billing account is required** for the free tier — leave billing alone.  
   - Give the project a recognizable name (e.g., `music-generator`).

6. **Copy the key**  
   A string starting with `AIza…` (~39 characters) is shown. Copy it immediately — keys created in AI Studio today are **auth keys** that work right away on the free tier.

7. **Paste it in the UI or in your `.env` file** (this project) so the app picks it up:

   ```
   GEMINI_API_KEY=AIzaSy...your-copied-key
   ```

### Free tier notes

- The free tier is genuinely free: rate-limited (roughly ~10–15 requests/min, a few hundred/day for flash-class models) but no payment needed to start.
- If you ever hit the limit, you'll see a `429` error — wait a bit and retry, or upgrade via **Set up billing** in AI Studio for higher quotas.
- **Treat your key like a password.** Never commit it to git or share it; if it leaks, revoke it on the AI Studio API keys page and create a new one.

---

## Running the App

```bash
streamlit run app.py
```
The app opens in your browser (`http://localhost:8501`).


---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GEMINI_API_KEY not found in environmental context.` | Create a `.env` file with the key, or enter a key in the sidebar. |
| `LilyPond is not installed or was not found in the system PATH` | Install LilyPond and add it to `PATH`, then restart the terminal. |
| `Score rendering failed` with a LilyPond error | Usually a model output quirk; click Execute again — the sanitizer handles most cases. |
| HTTP `429` / quota errors from Gemini | Free-tier rate limit hit; wait and retry, or set up billing for higher limits. |
| Slow first run | Downloads of the spaCy model and DistilBERT pipeline happen once on first launch. |
| `en_core_web_md` fallback warning | Run `python -m spacy download en_core_web_md` for better movement classification. |


