class MusicalInterpretationAgent:
    """
    Agent 2: Algorithmic translator mapping semantic JSON features into key music parameters.
    """


    def translate(self, semantic_data: dict, selected_instruments: list) -> dict:
        emotion = semantic_data["emotion"]
        valence = emotion["valence"]
        arousal = emotion["arousal"]
        movement = semantic_data["movement"]

        # Map valence to Keys and Modes
        if valence >= 0.5:
            mode = "major"
            keys = ["C major", "G major", "D major", "F major"]
            key = keys[int(valence * 10) % len(keys)]


        else:
            mode = "minor"
            keys = ["A minor", "D minor", "E minor", "G minor"]
            key = keys[int(valence * 10) % len(keys)]




        # Map movement & arousal to Tempo
        base_tempo = 80

        if movement == "fast":
            base_tempo = 120

        elif movement == "slow":
            base_tempo = 56
            


        tempo = int(base_tempo + (arousal * 50) - 25)
        tempo = max(40, min(208, tempo))  # Safe boundaries



        # Map arousal to Dynamics
        if arousal >= 0.7:
            dynamics = "f"

        elif arousal >= 0.4:
            dynamics = "mf"

        else:
            dynamics = "p"




        # Articulation mappings
        if movement == "slow":
            articulation = "legato"

        elif movement == "fast":
            articulation = "staccato"

        else:
            articulation = "tenuto"




        density = round(arousal * 0.7 + 0.1, 2)




        return {
            "tempo": tempo,
            "key": key,
            "mode": mode,
            "time_signature": "4/4",
            "dynamics": dynamics,
            "instrumentation": selected_instruments if selected_instruments else ["piano"],
            "density": density,
            "articulation": articulation
        }