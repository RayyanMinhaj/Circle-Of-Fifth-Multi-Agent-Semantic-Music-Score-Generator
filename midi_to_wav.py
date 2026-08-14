import struct
import wave
import numpy as np


SAMPLE_RATE = 44100


def _read_vlq(data, i):
    val = 0
    while True:
        b = data[i]
        i += 1
        val = (val << 7) | (b & 0x7F)
        if not b & 0x80:
            return val, i


def _parse_midi(path):
    with open(path, "rb") as f:
        data = f.read()

    assert data[:4] == b"MThd"
    fmt, ntrks, division = struct.unpack(">HHH", data[8:14])
    if fmt not in (0, 1):
        raise ValueError(f"Unsupported MIDI format {fmt}")

    notes = []
    tempo_events = []
    pos = 14
    for _ in range(ntrks):
        assert data[pos:pos + 4] == b"MTrk"
        tlen = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        end = pos + 8 + tlen
        p = pos + 8
        tick = 0
        running = 0
        active = {}
        while p < end:
            delta, p = _read_vlq(data, p)
            tick += delta
            status = data[p]
            if status == 0xFF:
                meta = data[p + 1]
                length = data[p + 2]
                payload = data[p + 3:p + 3 + length]
                if meta == 0x51 and length >= 3:
                    tempo_events.append((tick, int.from_bytes(payload[:3], "big")))
                p += 3 + length
            elif status in (0xF0, 0xF7):
                ln, p = _read_vlq(data, p + 1)
                p += ln
            else:
                if status & 0x80:
                    running = status
                    p += 1
                kind = running >> 4
                chan = running & 0x0F
                if kind in (0x8, 0x9, 0xB, 0xE):
                    d1, d2 = data[p], data[p + 1]
                    p += 2
                elif kind in (0xC, 0xD):
                    d1, d2 = data[p], None
                    p += 1
                else:
                    continue
                if kind == 0x9 and d2 > 0:
                    active[(chan, d1)] = (tick, d2)
                elif kind == 0x8 or (kind == 0x9 and d2 == 0):
                    if (chan, d1) in active:
                        start, vel = active.pop((chan, d1))
                        notes.append((start, tick, d1, vel, chan))
        for (chan, pitch), (start, vel) in active.items():
            notes.append((start, tick, pitch, vel, chan))
        pos = end

    if not tempo_events:
        tempo_events = [(0, 500000)]
    return notes, division, tempo_events


def _ticks_to_seconds(tick, division, tempo_events):
    events = sorted(tempo_events)
    sec = 0.0
    prev_tick = 0
    prev_usec = events[0][1]
    for ev in events[1:]:
        t, usec = ev
        sec += (t - prev_tick) / division * prev_usec / 1e6
        prev_tick, prev_usec = t, usec
    sec += (tick - prev_tick) / division * prev_usec / 1e6
    return sec


def _note_wave(start_s, dur_s, freq, vel, channel):
    sr = SAMPLE_RATE
    start = int(start_s * sr)
    length = int((dur_s + 1.5) * sr)
    idx = np.arange(length, dtype=np.float64) / sr
    env = np.exp(-idx / max(0.6, dur_s * 0.6))
    attack = int(0.004 * sr)
    if attack < length:
        env[:attack] *= np.linspace(0, 1, attack)

    amp = (vel / 127.0) ** 1.5
    partials = [(1.0, 1.0), (2.0, 0.55), (3.0, 0.30),
                (4.0, 0.16), (5.0, 0.09), (6.0, 0.05)]
    wave = np.zeros(length)
    for mult, a in partials:
        wave += a * np.sin(2 * np.pi * freq * mult * idx)
    wave += 0.15 * np.sin(2 * np.pi * freq * 2.001 * idx)

    tone = wave * env * amp
    pan = 0.15 if channel % 2 == 0 else -0.15
    return start, tone * (1 - pan) / 2, tone * (1 + pan) / 2


def midi_to_wav(midi_path, wav_path):
    notes, division, tempo_events = _parse_midi(midi_path)

    if not notes:
        raise ValueError("MIDI file contains no notes.")

    total_tick = max(n[1] for n in notes)
    total_s = _ticks_to_seconds(total_tick, division, tempo_events) + 2.0
    n_samples = int(total_s * SAMPLE_RATE)
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)

    for start_tick, end_tick, pitch, vel, chan in notes:
        start_s = _ticks_to_seconds(start_tick, division, tempo_events)
        end_s = _ticks_to_seconds(end_tick, division, tempo_events)
        freq = 440.0 * (2.0 ** ((pitch - 69) / 12.0))
        s, l, r = _note_wave(start_s, end_s - start_s, freq, vel, chan)
        if s >= n_samples:
            continue
        upto = min(n_samples, s + len(l))
        left[s:upto] += l[:upto - s]
        right[s:upto] += r[:upto - s]

    peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))))
    if peak > 0:
        left /= peak
        right /= peak
    left *= 0.85
    right *= 0.85

    pcm = np.empty(n_samples * 2, dtype=np.int16)
    pcm[0::2] = np.int16(left * 32767)
    pcm[1::2] = np.int16(right * 32767)

    with wave.open(wav_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())

    return wav_path
