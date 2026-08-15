class CompositionAgent:
    """
    Agent 3: Converts musical parameters into specific pitches, motifs, chords, and bars.
    The score length scales with the poem's word count, and each bar is filled with
    a rhythmically varied pattern (beamed eighths/sixteenths, dotted notes, rests).
    Every instrument receives its own distinct part: the lead melody, an octave or
    harmonic doubling, or a chord-tone accompaniment, so no two voices are identical.
    """

    DURATION_CODE = {0.25: "16", 0.5: "8", 1: "4", 1.5: "4.", 2: "2", 3: "2."}

    # Every cell sums to exactly 4 beats (4/4 time).
    RHYTHM_CELLS = {
        "calm": [
            [2, 2],
            [1, 1, 1, 1],
            [3, 1],
            [2, 1, 1],
            [1, 3],
        ],
        "mid": [
            [1, 1, 1, 1],
            [0.5, 0.5, 0.5, 0.5, 1, 1],
            [1, 0.5, 0.5, 1, 1],
            [1.5, 0.5, 1, 1],
            [0.5, 0.5, 1, 0.5, 0.5, 1],
        ],
        "dense": [
            [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            [0.25, 0.25, 0.25, 0.25, 1, 1, 1],
            [0.5, 0.5, 1, 0.5, 0.5, 0.5, 0.5],
            [1, 0.5, 0.5, 0.5, 0.5, 1],
            [0.5, 0.5, 0.5, 0.5, 1, 1],
        ],
    }

    def _stable_hash(self, text: str) -> int:
        """Deterministic hash so output is reproducible across runs."""
        return sum(ord(c) for c in text)

    def _pick_cell(self, seed_text: str, bar_idx: int, density: float) -> list:
        if density < 0.35:
            pool = self.RHYTHM_CELLS["calm"]
        elif density < 0.6:
            pool = self.RHYTHM_CELLS["mid"] + self.RHYTHM_CELLS["calm"][:2]
        else:
            pool = self.RHYTHM_CELLS["dense"] + self.RHYTHM_CELLS["mid"][1:]
        h = self._stable_hash(f"{seed_text}{bar_idx}")
        return pool[h % len(pool)]

    def _pitch_sequence(self, seed_words: list, scale: list, n: int):
        """Deterministically stretch a word-derived motif to n notes."""
        notes = []
        indices = []
        prev_idx = None
        i = 0
        while len(notes) < n:
            word = seed_words[i % len(seed_words)]
            idx = (sum(ord(c) for c in word) + len(word) + i * 3) % len(scale)
            if idx == prev_idx:
                idx = (idx + 2) % len(scale)
            prev_idx = idx

            offsets = (2, -3) if i % 2 == 0 else (-2, 3)
            for off in offsets:
                if len(notes) >= n:
                    break
                note_idx = (idx + off) % len(scale)
                notes.append(scale[note_idx])
                indices.append(note_idx)
            i += 1
        return notes, indices

    def _beamify(self, rhythm: list) -> list:
        """Group consecutive 8th/16th notes into explicit LilyPond beams."""
        tokens = []
        i = 0
        while i < len(rhythm):
            pitch, dur = rhythm[i]
            code = self.DURATION_CODE[dur]

            if pitch != "r" and dur in (0.5, 0.25):
                j = i
                group = []
                while j < len(rhythm) and rhythm[j][0] != "r" and rhythm[j][1] == dur:
                    group.append(f"{rhythm[j][0]}{code}")
                    j += 1
                if len(group) > 1:
                    tokens.append(" ".join([group[0] + "["] + group[1:-1] + [group[-1] + "]"]))
                else:
                    tokens.append(group[0])
                i = j
            else:
                tokens.append(f"{pitch}{code}")
                i += 1
        return tokens

    def compose(self, musical_data: dict, semantic_data: dict) -> dict:

        # Scale definitions
        key_scales = {
            "C major": ["c'", "d'", "e'", "f'", "g'", "a'", "b'"],
            "G major": ["g'", "a'", "b'", "c''", "d''", "e''", "fis''"],
            "D major": ["d'", "e'", "fis'", "g'", "a'", "b'", "cis''"],
            "F major": ["f'", "g'", "a'", "bes'", "c''", "d''", "e''"],
            "A minor": ["a", "b", "c'", "d'", "e'", "f'", "g'"],
            "D minor": ["d", "e", "f", "g", "a", "bes", "c'"],
            "E minor": ["e", "fis", "g", "a", "b", "c'", "d'"],
            "G minor": ["g", "a", "bes", "c'", "d'", "es'", "f'"]
        }

        key = musical_data["key"]
        scale = key_scales.get(key, ["c'", "d'", "e'", "f'", "g'"])

        # Build a motif from unique theme/imagery words (avoids repeats)
        seed_words = []
        for item in list(semantic_data["themes"]) + list(semantic_data["imagery"]):
            for w in item.split():
                w = w.strip("'\".,;!?-").lower()
                if w and w not in seed_words:
                    seed_words.append(w)
        if not seed_words:
            seed_words = ["echo", "night"]

        # ---- Size the score from the poem's word count (not LLM-derived data) ----
        word_count = int(semantic_data.get("word_count", 0) or 0)
        if word_count <= 0:
            word_count = len(seed_words)
        num_bars = max(4, min(round(word_count / 2), 16))

        density = float(musical_data.get("density", 0.4))
        seed_text = " ".join(seed_words)

        # ---- Rhythm plan: one cell per bar, then stretch the motif to fit ----
        cells = [self._pick_cell(seed_text, bar, density) for bar in range(num_bars)]
        total_notes = sum(len(c) for c in cells)
        melody_notes, melody_indices = self._pitch_sequence(seed_words, scale, total_notes)

        # ---- Chord candidates (scale degrees) for harmonizing each bar ----
        if musical_data["mode"] == "major":
            chord_candidates = [
                [0, 2, 4],  # I
                [3, 5, 0],  # IV
                [4, 6, 1],  # V
            ]
        else:
            chord_candidates = [
                [0, 2, 4],  # i
                [5, 0, 2],  # VI
                [6, 1, 3],  # VII
            ]

        bar_chords = []
        prev_chord_i = None
        ptr = 0
        for bar in range(num_bars):
            n = len(cells[bar])
            bar_indices = melody_indices[ptr:ptr + n]
            ptr += n

            scores = []
            for c_i, cand in enumerate(chord_candidates):
                hits = sum(1 for mi in bar_indices if mi in cand)
                if c_i == prev_chord_i:
                    hits -= 0.5
                scores.append(hits)
            best_i = max(range(len(chord_candidates)), key=lambda c: scores[c])
            prev_chord_i = best_i
            bar_chords.append([scale[i] for i in chord_candidates[best_i]])

        chords = list(dict.fromkeys(tuple(c) for c in bar_chords))
        chords = [list(c) for c in chords]

        # ---- Build measures ----
        measures = []
        instrumentation = musical_data["instrumentation"]
        ptr = 0

        for bar in range(num_bars):
            cell = cells[bar]
            n = len(cell)
            bar_melody = melody_notes[ptr:ptr + n]
            bar_indices = melody_indices[ptr:ptr + n]
            ptr += n
            chord = bar_chords[bar]

            # Breathing rest at phrase boundaries (every 4th bar), shared by all voices
            rest_this_bar = (bar + 1) % 4 == 0

            def with_breath(pairs):
                pairs = list(pairs)
                if rest_this_bar:
                    last_pitch, last_dur = pairs[-1]
                    pairs[-1] = ("r", last_dur)
                return pairs

            def harmonize(offset):
                return self._beamify(with_breath(zip(
                    [scale[(i + offset) % len(scale)] for i in bar_indices], cell)))

            melody_tokens = self._beamify(with_breath(zip(bar_melody, cell)))

            voices = {}
            for inst in instrumentation:
                inst_lower = inst.lower()

                if inst_lower in ["violin", "flute", "clarinet", "oboe"]:
                    if inst_lower == "violin":
                        # Lead voice: the melody itself
                        voices[inst] = melody_tokens

                    elif inst_lower == "flute":
                        # Octave doubling above the lead (classic colour doubling)
                        voices[inst] = self._beamify(with_breath(zip(
                            [p + "'" for p in bar_melody], cell)))

                    elif inst_lower == "clarinet":
                        # Harmonic doubling a diatonic 3rd below the lead
                        voices[inst] = harmonize(-2)

                    elif inst_lower == "oboe":
                        # Harmonic doubling a diatonic 3rd above the lead
                        voices[inst] = harmonize(2)

                elif inst_lower in ["cello", "viola", "double bass"]:
                    root = chord[0].replace("'", "") + ","
                    third = chord[1].replace("'", "") + ","
                    fifth = chord[2].replace("'", "") + ","

                    if inst_lower == "cello":
                        # Broken-chord arpeggio: root - fifth - third - root
                        voices[inst] = [f"{root}4", f"{fifth}4", f"{third}4", f"{root}4"]

                    elif inst_lower == "viola":
                        # Sustained root and fifth
                        voices[inst] = [f"{root}2", f"{fifth}2"]

                    elif inst_lower == "double bass":
                        # Long pedal on the root
                        voices[inst] = [f"{root}1"]

                elif inst_lower == "piano":
                    voices[inst] = {
                        "treble_staff": melody_tokens,
                        "bass_staff": [f"<{' '.join(chord)}>1"]
                    }

            measures.append({
                "measure": bar + 1,
                "harmony": chord,
                "voices": voices
            })

        return {
            "key_signature": key,
            "melody_motif": melody_notes,
            "chords": chords,
            "total_measures": len(measures),
            "measures": measures
        }
