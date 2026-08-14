# Semantic Music Generation

Multi-agent pipeline that converts a poem or text into a LilyPond music score.

## Setup

1. Install Python dependencies:

   pip install -r requirements.txt

2. Download the spaCy model (requires the `en_core_web_md` model for
   word-vector based movement classification; falls back to `en_core_web_sm`
   if unavailable):

   python -m spacy download en_core_web_md

3. Create a `.env` file with your Gemini API key:

   GEMINI_API_KEY=your_key_here

4. Run the app:

   streamlit run app.py
