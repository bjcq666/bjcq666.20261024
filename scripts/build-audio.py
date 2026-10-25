#!/usr/bin/env python3
"""Generate every sound effect and the music loop for Neon Dash.

All audio is synthesized here from scratch (sine/square/saw/noise + envelopes),
so the repository ships no third-party audio and needs no licence review for it.
Re-run after editing: `python3 scripts/build-audio.py`.

spx plays `assets/sounds/<name>/index.json` == {"path","rate","sampleCount"}
and looks sounds up by directory name, so nothing has to be registered in
assets/index.json.
"""
import json
import math
import os
import random
import struct
import wave

SR = 22050
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "game", "assets", "sounds")

random.seed(1024)


# ---------------------------------------------------------------------------
# tiny synth
# ---------------------------------------------------------------------------
def buf(seconds):
    return [0.0] * int(SR * seconds)


def add(dst, src, at=0.0, gain=1.0):
    start = int(at * SR)
    for i, v in enumerate(src):
        j = start + i
        if 0 <= j < len(dst):
            dst[j] += v * gain


def osc(kind, freq, seconds, sweep=1.0, vib=0.0, vib_hz=6.0):
    """sweep is the frequency multiplier at the end of the sound."""
    n = int(SR * seconds)
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        t = i / max(1, n - 1)
        f = freq * (1.0 + (sweep - 1.0) * t)
        if vib:
            f *= 1.0 + vib * math.sin(2 * math.pi * vib_hz * i / SR)
        phase += 2 * math.pi * f / SR
        if kind == "sine":
            v = math.sin(phase)
        elif kind == "square":
            v = 1.0 if math.sin(phase) >= 0 else -1.0
        elif kind == "saw":
            v = 2.0 * ((phase / (2 * math.pi)) % 1.0) - 1.0
        else:  # triangle
            v = 2.0 * abs(2.0 * ((phase / (2 * math.pi)) % 1.0) - 1.0) - 1.0
        out[i] = v
    return out


def noise(seconds, smooth=0.0):
    n = int(SR * seconds)
    out = [0.0] * n
    last = 0.0
    for i in range(n):
        r = random.uniform(-1.0, 1.0)
        if smooth > 0.0:
            last = last * smooth + r * (1.0 - smooth)
            r = last
        out[i] = r
    return out


def decay(src, rate, hold=0.0):
    """Exponential decay envelope; `hold` seconds stay at full level."""
    n = len(src)
    hold_n = int(hold * SR)
    for i in range(n):
        if i < hold_n:
            k = 1.0
        else:
            k = math.exp(-rate * (i - hold_n) / SR)
        src[i] *= k
    return src


def fade_in(src, seconds):
    n = min(len(src), int(seconds * SR))
    for i in range(n):
        src[i] *= i / n
    return src


def fade_out(src, seconds):
    n = min(len(src), int(seconds * SR))
    for i in range(n):
        src[len(src) - 1 - i] *= i / n
    return src


def normalise(src, peak):
    top = max(1e-9, max(abs(v) for v in src))
    k = peak / top
    for i in range(len(src)):
        src[i] *= k
    return src


def pad(src, seconds):
    out = src + [0.0] * (int(SR * seconds) - len(src))
    return out


def save(name, src):
    src = normalise(src, 0.85 if name != "bgm" else 0.55)
    folder = os.path.join(OUT, name)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "sound.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in src
        ))
    with open(os.path.join(folder, "index.json"), "w") as f:
        json.dump({"rate": SR, "sampleCount": len(src), "path": "sound.wav"}, f)
        f.write("\n")
    print(f"{name:12s} {len(src) / SR:5.2f}s  {len(src) * 2 / 1024:7.1f} KiB")


# ---------------------------------------------------------------------------
# sound effects
# ---------------------------------------------------------------------------
def sfx_jump():
    out = buf(0.16)
    add(out, decay(osc("square", 300, 0.15, sweep=2.3), 16, hold=0.01))
    add(out, decay(noise(0.03, smooth=0.4), 90), gain=0.25)
    return fade_out(out, 0.02)


def sfx_double_jump():
    out = buf(0.18)
    add(out, decay(osc("square", 520, 0.16, sweep=2.0), 15, hold=0.01))
    add(out, decay(osc("square", 780, 0.14, sweep=1.6), 20), gain=0.4)
    return fade_out(out, 0.02)


def sfx_land():
    out = buf(0.14)
    add(out, decay(osc("sine", 160, 0.12, sweep=0.4), 28, hold=0.004))
    add(out, decay(noise(0.09, smooth=0.55), 45), gain=0.45)
    return fade_out(out, 0.02)


def sfx_death():
    out = buf(0.85)
    add(out, decay(osc("saw", 420, 0.8, sweep=0.12, vib=0.03, vib_hz=11), 4.2, hold=0.02), gain=0.7)
    add(out, decay(osc("square", 210, 0.5, sweep=0.25), 5.0), gain=0.35)
    add(out, decay(noise(0.6, smooth=0.75), 6.0), gain=0.3)
    return fade_out(out, 0.12)


def sfx_finish():
    out = buf(0.90)
    notes = [880.0, 1108.7, 1318.5, 1760.0]
    for i, f in enumerate(notes):
        seg = decay(osc("square", f, 0.16, sweep=1.0), 9, hold=0.02)
        add(out, seg, at=i * 0.11, gain=0.5)
        add(out, decay(osc("triangle", f / 2, 0.16), 9, hold=0.02), at=i * 0.11, gain=0.25)
    tail = decay(osc("triangle", 1760.0, 0.45), 6, hold=0.02)
    add(out, tail, at=0.42, gain=0.35)
    return fade_out(out, 0.1)


def sfx_hurt():
    out = buf(0.26)
    add(out, decay(osc("saw", 300, 0.24, sweep=0.45, vib=0.04, vib_hz=18), 9, hold=0.01), gain=0.8)
    add(out, decay(noise(0.12, smooth=0.5), 30), gain=0.35)
    return fade_out(out, 0.04)


def sfx_select():
    out = buf(0.10)
    add(out, decay(osc("square", 900, 0.08, sweep=1.2), 40, hold=0.002), gain=0.6)
    add(out, decay(osc("sine", 1800, 0.06), 60), gain=0.25)
    return fade_out(out, 0.015)


# ---------------------------------------------------------------------------
# music: 4 bars of soft synthwave at 120 BPM, seamless loop
# ---------------------------------------------------------------------------
def bgm():
    bpm = 120.0
    beat = 60.0 / bpm          # 0.5s
    bar = beat * 4             # 2s
    bars = 4
    total = bar * bars         # 8s
    out = buf(total)

    # Am - F - C - G, one chord per bar (roots in A1..A2 range)
    roots = [55.00, 43.65, 65.41, 49.00]
    chords = [
        [220.00, 261.63, 329.63],
        [174.61, 220.00, 261.63],
        [261.63, 329.63, 392.00],
        [196.00, 246.94, 293.66],
    ]

    for b in range(bars):
        t0 = b * bar
        root = roots[b]
        # bass: root on 1 and 3, octave on the "and" of 2 and 4
        for k, at in enumerate([0.0, beat * 1.5, beat * 2.0, beat * 3.5]):
            f = root * (2.0 if k % 2 else 1.0)
            seg = decay(osc("saw", f, beat * 0.9, sweep=1.0), 6, hold=0.03)
            add(out, seg, at=t0 + at, gain=0.5)

        # pad: slow swell over the whole bar
        for f in chords[b]:
            seg = osc("triangle", f, bar, sweep=1.0)
            fade_in(seg, 0.25)
            fade_out(seg, 0.35)
            add(out, seg, at=t0, gain=0.055)

        # arp: eight 16ths cycling up the chord
        order = [0, 1, 2, 1, 0, 1, 2, 1]
        for k in range(8):
            f = chords[b][order[k]] * 4.0
            seg = decay(osc("square", f, beat * 0.45, sweep=1.0), 22, hold=0.005)
            add(out, seg, at=t0 + k * beat * 0.5, gain=0.11)

        # kick on 1 and 3, soft noise snare on 2 and 4, closed hats on 8ths
        for at in (0.0, beat * 2.0):
            add(out, decay(osc("sine", 120, 0.16, sweep=0.35), 26, hold=0.004),
                at=t0 + at, gain=0.55)
        for at in (beat, beat * 3.0):
            add(out, decay(noise(0.12, smooth=0.5), 34), at=t0 + at, gain=0.16)
        for k in range(8):
            add(out, decay(noise(0.03, smooth=0.15), 110), at=t0 + k * beat * 0.5, gain=0.045)

    # seamless: the last note tails are cut, so fold the tail into the head
    fade_in(out, 0.01)
    fade_out(out, 0.02)
    return out


def main():
    print(f"sample rate {SR} Hz, mono, 16-bit")
    save("jump", sfx_jump())
    save("doublejump", sfx_double_jump())
    save("land", sfx_land())
    save("death", sfx_death())
    save("finish", sfx_finish())
    save("select", sfx_select())
    save("hurt", sfx_hurt())
    save("bgm", bgm())


if __name__ == "__main__":
    main()
