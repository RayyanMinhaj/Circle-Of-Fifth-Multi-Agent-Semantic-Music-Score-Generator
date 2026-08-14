import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def set_api_key(key: str) -> None:
    """Override the Gemini API key used by the agents at runtime."""
    global api_key
    api_key = key
    genai.configure(api_key=key)




SKELETON = """
\\version "2.24.4"

\\header {
  title = "Semantic Music Composition"
  composer = "AI Multi-Agent Pipeline"
  tagline = ""
}

\\score {
  <<
    % Nest individual Staff contexts inside these double angles
  >>
  \\layout { }
  \\midi { }
}
"""






EXAMPLE = """
\\version "2.24.4"

\\header {
  title = "Echoes of the Night Ivy"
  composer = "AI Pipeline"
}

\\score {
  <<
    \\new Staff \\with { instrumentName = #"Violin" } {
      \\clef treble
      \\tempo 4 = 58
      \\key d \\major
      \\time 4/4
      d'2\\p fis'2 | a'8[ g' fis' g'] a'1 |
    }
    \\new Staff \\with { instrumentName = #"Cello" } {
      \\clef bass
      \\tempo 4 = 58
      \\key d \\major
      \\time 4/4
      d,2\\p a,2 | d,1 |
    }
  >>
  \\layout { }
  \\midi { }
}
"""





class LilypondAgent:
    """
    Agent 4: Takes all compiled JSON results and requests syntax-valid LilyPond markup from Gemini.
    """
    def generate(self, semantic: dict, musical: dict, composition: dict) -> str:
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environmental context.")
            


        consolidated_payload = {
            "semantic_analysis": semantic,
            "musical_interpretation": musical,
            "composition_structure": composition
        }

        total_measures = composition.get("total_measures", len(composition.get("measures", [])))
        



        prompt = f"""
        You are an expert LilyPond Music Notation Agent. Your goal is to convert the following consolidated musical schema into clean, syntactically-valid LilyPond (.ly) markup and nothing else.

        ### Consolidated Musical Schema:
        {json.dumps(consolidated_payload, indent=2)}

        ### Rules & Formatting Requirements:
        1. Create a dedicated `\\new Staff` structure for each instrument listed under `musical_interpretation.instrumentation`.
        2. Apply matching clefs to each instrument (e.g., Violin/Flute gets treble clef, Cello/Double Bass gets bass clef).
        3. If Piano is present, render it as a standard `\\new PianoStaff` split into two distinct staff voices.
        4. Incorporate the tempo, key, time signature, and initial dynamics provided. Dynamics MUST use LilyPond dynamic marks such as `\\f`, `\\p`, `\\mp`, `\\mf`, or `\\ff` written directly after a note (e.g., `c''2\\f`). NEVER write `\\dynamic f` or any `\\dynamic` command — that syntax is invalid.
        5. Ensure every bar contains the correct total duration for the time signature so bar checks pass.
        6. Render the EXACT note tokens provided in `composition_structure.measures` for every instrument (melody, chord, and bass lines). Each token already contains a LilyPond pitch AND duration (e.g., `c'4`, `d'8[ fis'8]`, `a'2.`, `r8`). Copy them verbatim — do NOT change, normalize, or invent durations, and do NOT transpose pitches.
        7. The score MUST contain exactly `{total_measures}` bars (`composition_structure.total_measures`). Do not expand, repeat, double, or add extra measures under any circumstance — render every bar from `measures` once, in order.
        8. Return ONLY executable LilyPond markup. Do not wrap the response in markdown blocks (e.g., do not use ```lilypond tags).

        ### Structural LilyPond Skeleton:
        {SKELETON}

        ### Correct Reference Sample:
        {EXAMPLE}
        """


        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        output = response.text.strip()
        


        # Strip code blocks if returned
        if output.startswith("```"):
            lines = output.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            output = "\n".join(lines).strip()
            

        # Sanitize dynamics: `\dynamic f` is invalid; convert to `\f` marks
        dynamic_marks = {"ppp": "\\ppp", "pp": "\\pp", "p": "\\p", "mp": "\\mp",
                         "mf": "\\mf", "f": "\\f", "ff": "\\ff", "fff": "\\fff"}
        import re
        output = re.sub(r"\\dynamic[ \t]+([a-z]{1,3})\b",
                        lambda m: dynamic_marks.get(m.group(1), "\\mf"),
                        output)
        output = re.sub(r"\\dynamic", lambda m: "\\mf", output)
            
        return output