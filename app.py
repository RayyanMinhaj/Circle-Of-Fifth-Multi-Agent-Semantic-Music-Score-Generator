import streamlit as st
import os
import json
from semantic_agent import SemanticAgent
from musical_agent import MusicalInterpretationAgent
from composition_agent import CompositionAgent
from lilypond_agent import LilypondAgent, set_api_key
from music_compiler import MusicCompiler

st.set_page_config(page_title="Circle of Fifths", layout="wide")

# Initialize Pipeline Agents
semantic_agent = SemanticAgent()
musical_agent = MusicalInterpretationAgent()
composition_agent = CompositionAgent()
lilypond_agent = LilypondAgent()
compiler = MusicCompiler()

# Preloaded poetry datasets
PRESETS = {
    "Write / Paste Custom Text": "",
    "Dreamlike Night Poetry": "Drifting stars hum soft, silver lullabies through ancient paths of violet clouds where gravity yields to gentle breath.",
    "Somber Gothic Poetry": "A morgue silence shudders beyond the twisting vine of ashen oak, creeping death snares the midnight ivy.",
    "Joyous Morning Poetry": "Golden rays paint the laughing morning dew, sailing high over emerald meadows with a heart bursting with spring melodies."
}

st.title("🎵 Circle of Fifths: A Multi-Agent Semantic Music Score Generator")
st.write("Each pipeline block processes your text into a distinct, verifiable JSON format before generating the final score.")

# ----------------- SIDEBAR OPTIONS -----------------
st.sidebar.header("🎛️ Pipeline Parameters")
preset_name = st.sidebar.selectbox("Choose a Poem Preset", list(PRESETS.keys()))
default_text = PRESETS[preset_name]

st.sidebar.markdown("---")
st.sidebar.subheader("Instrument Ensemble")
selected_instruments = st.sidebar.multiselect(
    "Orchestra Voices",
    ["Violin", "Viola", "Cello", "Flute", "Oboe", "Clarinet", "Piano", "Double Bass"],
    default=["Violin", "Cello"],
    help="Every instrument gets a distinct part: Violin leads the melody, Flute doubles an octave above, Clarinet harmonizes a 3rd below, Oboe a 3rd above; Cello arpeggiates the chord, Viola sustains root/fifth, Double Bass holds a root pedal, and Piano combines the melody with block-chord bass."
    
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎚️ Emotion Override")
manual_emotion = st.sidebar.checkbox(
    "Manually set valence & arousal",
    value=False,
    help="When enabled, the sliders below overwrite the NLP-computed valence/arousal from Step 1 before they reach the musical translation."
)
valence_slider = st.sidebar.slider(
    "Valence (negative ↔ positive)",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    disabled=not manual_emotion,
    help="Lower = minor/sad key, higher = major/joyful key."
)
arousal_slider = st.sidebar.slider(
    "Arousal (calm ↔ energetic)",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    disabled=not manual_emotion,
    help="Higher = faster tempo, louder dynamics, denser rhythm."
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Gemini API Key")
env_api_key = os.getenv("GEMINI_API_KEY", "")

gemini_api_key = st.sidebar.text_input( #dont bother trying to steal the API key, its free and public lol
    "API Key (overrides .env)",
    value=env_api_key,
    type="password",
    help="Type a new key here to override it, and no point in stealing it, it's free and public.",
    )

# ----------------- MAIN PIPELINE UI -----------------
user_text = st.text_area("1. Input Semantic Text / Poem:", value=default_text, height=120)

if st.button("🚀 Execute Pipeline Step-by-Step"):
    if not user_text.strip():
        st.error("Please enter semantic text or select a poetry preset.")
    else:
        active_api_key = gemini_api_key.strip() or env_api_key
        if active_api_key:
            set_api_key(active_api_key)
        else:
            st.error("No Gemini API key found. Set GEMINI_API_KEY in your .env file or enter one in the sidebar.")
            st.stop()
        # Create visual workspace division
        tabs = st.tabs([
            "🔍 Step 1: Semantics", 
            "🎼 Step 2: Musical Translation", 
            "📐 Step 3: Composition Structure", 
            "🎹 Step 4: LilyPond & Score Output"
        ])
        
        # --- STEP 1: SEMANTIC ANALYSIS ---
        with tabs[0]:
            st.subheader("Semantic Extraction (NLP Models)")
            with st.spinner("Extracting parameters..."):
                semantic_json = semantic_agent.analyze(user_text)
                if manual_emotion:
                    semantic_json["emotion"]["valence"] = valence_slider
                    semantic_json["emotion"]["arousal"] = arousal_slider
                    st.info("Emotion values overwritten by sidebar sliders.")
                st.json(semantic_json)
                st.success("Step 1 Complete: Captured semantic values.")

        # --- STEP 2: MUSICAL ANALYSIS ---
        with tabs[1]:
            st.subheader("Musical Parameter Mapping")
            with st.spinner("Translating elements..."):
                musical_json = musical_agent.translate(semantic_json, selected_instruments)
                st.json(musical_json)
                st.success("Step 2 Complete: Translated semantics to musical attributes.")

        # --- STEP 3: COMPOSITION STRUCTURE ---
        with tabs[2]:
            st.subheader("Pitches, Chords & Structured Measures")
            with st.spinner("Arranging notation..."):
                composition_json = composition_agent.compose(musical_json, semantic_json)
                st.json(composition_json)
                st.success("Step 3 Complete: Structured all musical lines.")

        # --- STEP 4: LILYPOND GENERATION & COMPILATION ---
        with tabs[3]:
            st.subheader("Final Rendering Output")
            with st.spinner("Compiling final LilyPond code..."):
                try:
                    # Request score layout from the model
                    ly_code = lilypond_agent.generate(semantic_json, musical_json, composition_json)
                    
                    with st.expander("📄 View Compiled LilyPond Code"):
                        st.code(ly_code, language="lilypond")
                    
                    # Compile using system LilyPond
                    with st.spinner("Compiling MIDI and PDF files..."):
                        compilation = compiler.compile(ly_code)
                        
                        if compilation["success"]:
                            # Render visual PDF preview
                            score_image = compiler.render_pdf_to_image(compilation["pdf"])
                            st.image(score_image, caption="Synthesized Score Preview", use_container_width=True)
                            
                            # Handle files & downloads
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(compilation["pdf"], "rb") as f:
                                    st.download_button("📄 Download PDF Score", f, "composition.pdf", "application/pdf")
                            with col2:
                                with st.spinner("Synthesizing audio..."):
                                    wav_path = compiler.midi_to_wav(compilation["midi"])
                                with open(wav_path, "rb") as f:
                                    st.audio(f.read(), format="audio/wav")
                        else:
                            st.error("Score rendering failed. See error log below:")
                            st.code(compilation["error"])
                            
                except Exception as e:
                    st.error(f"Error executing agent task: {e}")