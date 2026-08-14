import spacy
from transformers import pipeline


# Safe load for spaCy (md preferred for word-vector similarity, sm fallback)
# NOTE: Models are installed via requirements.txt so they ship with the build.
# A runtime pip install is NOT attempted here — the Streamlit Cloud runtime
# venv is read-only and would fail with a Permission denied error.
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    nlp = spacy.load("en_core_web_sm")
    print("SemanticAgent: en_core_web_md not found, fell back to en_core_web_sm")


FAST_ANCHORS = ("quick", "rapid", "swift", "speedy", "rush", "sprint", "dash")
SLOW_ANCHORS = ("slow", "calm", "drift", "still", "sluggish", "gentle")

FAST_ANCHOR_DOCS = [nlp(a) for a in FAST_ANCHORS]
SLOW_ANCHOR_DOCS = [nlp(a) for a in SLOW_ANCHORS]








class SemanticAgent:
    """
    Agent 1: Extracts semantic features deterministically using local NLP models.
    """
    def __init__(self):
        # Local sentiment pipeline
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )







    def analyze(self, text: str) -> dict:

        doc = nlp(text)
        sentiment = self.sentiment_analyzer(text)[0]
        
        label = sentiment["label"]  # POSITIVE or NEGATIVE
        score = sentiment["score"]
        
        # Derive valence and arousal from sentiment score
        if label == "POSITIVE":
            valence = round(0.5 + (score * 0.4), 2)  # Range: 0.5 to 0.9
            arousal = round(0.3 + (score * 0.5), 2)  # Range: 0.3 to 0.8

        else:
            valence = round(0.5 - (score * 0.4), 2)  # Range: 0.1 to 0.5
            arousal = round(0.1 + (score * 0.6), 2)  # Range: 0.1 to 0.7



        # Extract themes from nouns, imagery from ADJ-NOUN phrases
        nouns = [t for t in doc if t.pos_ in ["NOUN", "PROPN"]]
        adjectives = [t.lemma_.lower() for t in doc if t.pos_ == "ADJ"]
        verbs = [t for t in doc if t.pos_ == "VERB"]

        themes = list(dict.fromkeys(t.lemma_.lower() for t in nouns[:12]))
        if not themes:
            themes = ["silence", "echo"]

        imagery = []
        for i, tok in enumerate(doc[:-1]):
            nxt = doc[i + 1]
            if tok.pos_ == "ADJ" and nxt.pos_ in ["NOUN", "PROPN"]:
                phrase = f"{tok.lemma_.lower()} {nxt.lemma_.lower()}"
                if phrase not in imagery:
                    imagery.append(phrase)

        for tok in nouns:
            candidate = tok.lemma_.lower()
            if candidate not in imagery and not any(candidate in p for p in imagery):
                imagery.append(candidate)

        imagery = imagery[:8]
        if not imagery:
            imagery = ["shadow", "light"]

        # Classify movement via semantic similarity to concept anchors (no verb lists)
        def similarity_to(token, anchor_docs):
            if not token.has_vector:
                return 0.0
            return sum(token.similarity(a) for a in anchor_docs) / len(anchor_docs)

        fast_votes = slow_votes = 0
        for v in verbs:
            fast_avg = similarity_to(v, FAST_ANCHOR_DOCS)
            slow_avg = similarity_to(v, SLOW_ANCHOR_DOCS)
            if fast_avg > slow_avg + 0.02:
                fast_votes += 1
            elif slow_avg > fast_avg + 0.02:
                slow_votes += 1

        if fast_votes > slow_votes:
            movement = "fast"

        elif slow_votes > fast_votes:
            movement = "slow"

        else:
            movement = "moderate"



        atmosphere = adjectives[0] if adjectives else "dreamlike"

        word_count = len([t for t in doc if not t.is_punct and not t.is_space])




        return {
            "word_count": word_count,
            "themes": themes,
            "emotion": {
                "valence": valence,
                "arousal": arousal
            },
            "imagery": imagery,
            "movement": movement,
            "atmosphere": atmosphere
        }