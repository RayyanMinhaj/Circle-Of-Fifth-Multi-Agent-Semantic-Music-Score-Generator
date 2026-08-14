import os
import subprocess
import fitz  # PyMuPDF
import abjad
from midi_to_wav import midi_to_wav

class MusicCompiler:
    """
    Compiles raw LilyPond files into MIDI and PDF outputs, and handles file rendering.
    """

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)




    def compile(self, ly_content: str, filename="output.ly") -> dict:
        ly_path = os.path.join(self.output_dir, filename)
        base_path, _ = os.path.splitext(ly_path)
        pdf_path = f"{base_path}.pdf"
        midi_path = f"{base_path}.mid"

        # Cleanup existing outputs
        for path in [ly_path, pdf_path, midi_path]:
            if os.path.exists(path):
                os.remove(path)



        with open(ly_path, "w", encoding="utf-8") as f:
            f.write(ly_content)




        try:
            # Invoke system LilyPond compiler [1]
            result = subprocess.run(
                ["lilypond", "-o", base_path, ly_path],
                check=True,
                capture_output=True,
                text=True
            )

            return {
                "success": True,
                "pdf": pdf_path if os.path.exists(pdf_path) else None,
                "midi": midi_path if os.path.exists(midi_path) else None,
                "log": result.stdout
            }




        except FileNotFoundError:
            return {
                "success": False,
                "error": "LilyPond is not installed or was not found in the system PATH."
            }



        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"LilyPond Compilation Error:\n{e.stderr or e.stdout}"
            }


    
    
    


    def render_pdf_to_image(self, pdf_path: str) -> str:
        """
        Converts the first page of the generated PDF into a PNG image for web rendering [1].
        """
        png_path = pdf_path.replace(".pdf", ".png")
        if os.path.exists(png_path):
            os.remove(png_path)
            

        doc = fitz.open(pdf_path)


        if len(doc) > 0:
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            pix.save(png_path)
        doc.close()


        return png_path


    def midi_to_wav(self, midi_path: str) -> str:
        """
        Synthesizes the MIDI file into a browser-playable WAV file.
        """
        wav_path = midi_path.replace(".mid", ".wav")
        midi_to_wav(midi_path, wav_path)
        return wav_path