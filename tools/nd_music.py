"""Nerazzurri Daily — daily soundtrack generator (rights-free, synthesized from nothing).

Every posted video gets an original instrumental in a currently popular style. The style
rotates by date, and the key, tempo and drum pattern vary per video, so no two days sound
the same. Nothing is sampled, sung or copied: every sound is built here from sine, square,
saw and noise, so no platform can claim it.

    from nd_music import render
    meta = render(path_wav, total_seconds, cut_times, name="ND-2026-09-26-ed25-slug", override=None)

`override` (from the beats JSON "music" block) may pin {"style": ..., "key": 0-11, "bpm": ...}.
Styles: phonk, drill, afrobeats, lofi, cinematic, house.
"""
import hashlib, math, wave
from datetime import date
import numpy as np

SR = 48000
STYLES = ["phonk", "afrobeats", "cinematic", "drill", "lofi", "house"]
BPM = {"phonk": (132, 148), "drill": (138, 144), "afrobeats": (100, 110),
       "lofi": (78, 88), "cinematic": (84, 96), "house": (120, 126)}
KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
# minor-key progressions as scale degrees (0 = i), one chord per bar
PROGS = [[0, 5, 2, 6], [0, 3, 5, 4], [0, 5, 3, 4], [0, 6, 5, 6], [0, 3, 0, 4], [5, 6, 0, 0]]
MINOR = [0, 2, 3, 5, 7, 8, 10]


def _seed(name):
    return int(hashlib.sha256((name or "nd").encode()).hexdigest()[:12], 16)


def _date_from_name(name):
    try:
        y, m, d = (int(x) for x in (name or "").split("-")[1:4])
        return date(y, m, d)
    except Exception:
        return None


def choose(name, override=None):
    """Pick style, key, bpm and variant for this video. Deterministic for a given name."""
    s = _seed(name)
    d = _date_from_name(name)
    style = STYLES[(d.toordinal() if d else s) % len(STYLES)]
    lo, hi = BPM[style]
    pick = {"style": style, "key": s % 12, "bpm": lo + (s // 12) % (hi - lo + 1),
            "prog": (s // 997) % len(PROGS), "variant": (s // 7919) % 4}
    override = override or {}
    if override.get("style") in BPM and "bpm" not in override:
        lo, hi = BPM[override["style"]]
        pick["bpm"] = lo + (s // 12) % (hi - lo + 1)
    for k, v in override.items():
        if k in pick and v is not None:
            pick[k] = v
    if pick["style"] not in BPM:
        pick["style"] = style
    return pick


# ---------------------------------------------------------------- building blocks
def _mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _env(n, a=0.005, d=0.2, s=0.0, r=0.05, hold=None):
    """ADSR envelope of n samples (hold = seconds at sustain before release)."""
    t = np.arange(n) / SR
    A = max(1, int(a * SR)); D = max(1, int(d * SR))
    e = np.full(n, s, dtype=float)
    e[:min(A, n)] = np.linspace(0, 1, A)[:min(A, n)]
    if A < n:
        k = min(D, n - A)
        e[A:A + k] = 1 - (1 - s) * (np.arange(k) / D)
    if hold is not None:
        rs = int((a + d + hold) * SR)
        if rs < n:
            R = max(1, int(r * SR)); k = min(R, n - rs)
            e[rs:rs + k] *= np.linspace(1, 0, k); e[rs + k:] = 0
    return e


def _lp(x, cutoff):
    """Windowed-sinc low-pass (cheap FIR)."""
    taps = 63; fc = min(cutoff / SR, 0.49)
    n = np.arange(taps) - (taps - 1) / 2
    h = np.sinc(2 * fc * n) * np.hamming(taps); h /= h.sum()
    return np.convolve(x, h, mode="same")


def _hp(x, cutoff):
    return x - _lp(x, cutoff)


def _saw(f, t):
    return 2 * ((f * t) % 1.0) - 1


def _sq(f, t, duty=0.5):
    return np.where((f * t) % 1.0 < duty, 1.0, -1.0)


class Mix:
    def __init__(self, total):
        self.n = int(total * SR); self.buf = np.zeros(self.n)

    def add(self, at, sig, gain=1.0):
        i = int(at * SR)
        if i >= self.n or i + len(sig) <= 0:
            return
        j = min(self.n, i + len(sig)); s0 = max(0, -i)
        self.buf[max(i, 0):j] += gain * sig[s0:s0 + (j - max(i, 0))]


# drums ----------------------------------------------------------------------------
def kick(punch=1.0, length=0.35, f_hi=150, f_lo=48):
    n = int(length * SR); t = np.arange(n) / SR
    f = f_lo + (f_hi - f_lo) * np.exp(-t * 35 * punch)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def snare(rng, tone=190, length=0.22, bright=5000):
    n = int(length * SR); t = np.arange(n) / SR
    noise = _hp(rng.standard_normal(n), 1200); noise = _lp(noise, bright)
    return 0.7 * noise * np.exp(-t * 18) + 0.4 * np.sin(2 * np.pi * tone * t) * np.exp(-t * 30)


def clap(rng):
    n = int(0.25 * SR); t = np.arange(n) / SR
    env = np.zeros(n)
    for off in (0, .011, .022):
        k = int(off * SR); env[k:] += np.exp(-(t[:n - k]) * 60)
    env += 0.5 * np.exp(-t * 14)
    return _lp(_hp(rng.standard_normal(n), 900), 7000) * env * 0.6


def hat(rng, open_=False):
    n = int((0.28 if open_ else 0.05) * SR); t = np.arange(n) / SR
    return _hp(rng.standard_normal(n), 7000) * np.exp(-t * (10 if open_ else 80)) * 0.5


def shaker(rng):
    n = int(0.07 * SR); t = np.arange(n) / SR
    return _hp(rng.standard_normal(n), 5000) * np.sin(np.pi * t / t[-1]) * 0.25


def rim(f=1700):
    n = int(0.05 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.48 * t)) * np.exp(-t * 90) * 0.4


def boom(length=1.4):
    n = int(length * SR); t = np.arange(n) / SR
    f = 38 + 60 * np.exp(-t * 8)
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5))


# tonal ----------------------------------------------------------------------------
def bass808(freq, length, glide_to=None, drive=2.5):
    n = int(length * SR); t = np.arange(n) / SR
    f = np.full(n, freq)
    if glide_to:
        g = min(n, int(0.09 * SR)); f[-g:] = np.linspace(freq, glide_to, g)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return np.tanh(drive * body) / np.tanh(drive) * _env(n, 0.003, length * 0.9, 0.35, 0.05, hold=length * 0.05)


def cowbell(freq, length=0.18):
    n = int(length * SR); t = np.arange(n) / SR
    x = _sq(freq, t) + _sq(freq * 1.504, t)
    return _lp(x, 4500) * np.exp(-t * 16) * 0.35


def pluck(freq, length=0.3, bright=3500):
    n = int(length * SR); t = np.arange(n) / SR
    x = _saw(freq, t) + 0.5 * _sq(freq * 2, t, 0.3)
    return _lp(x, bright) * np.exp(-t * 9) * 0.3


def keys_chord(freqs, length, trem=0.0):
    n = int(length * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3) for f in freqs)
    if trem:
        x *= 1 + trem * np.sin(2 * np.pi * 5 * t)
    return x / len(freqs) * _env(n, 0.01, 0.8, 0.55, 0.3, hold=length * 0.6) * 0.45


def pad(freqs, length, cutoff=1800, attack=0.4):
    n = int(length * SR); t = np.arange(n) / SR
    x = sum(_saw(f, t) + _saw(f * 1.006, t) + _saw(f * 0.994, t) for f in freqs)
    x = _lp(x / (3 * len(freqs)), cutoff)
    return x * _env(n, attack, 0.3, 0.8, 0.5, hold=max(0.0, length - attack - 0.8)) * 0.35


def stab(freqs, length=0.22):
    n = int(length * SR); t = np.arange(n) / SR
    x = sum(_saw(f, t) + _sq(f * 1.003, t) for f in freqs) / (2 * len(freqs))
    return _lp(x, 2600) * np.exp(-t * 12) * 0.4


def logdrum(freq, length=0.4):
    n = int(length * SR); t = np.arange(n) / SR
    f = freq * (1 + 0.35 * np.exp(-t * 40))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.6


def whoosh(rng, length=0.45):
    n = int(length * SR); tt = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * (300 + 2500 * tt / length) * tt)
    return (tt / length) ** 2 * (_hp(rng.standard_normal(n), 800) * 0.4 + sweep * 0.3)


# ---------------------------------------------------------------- arrangements
def _chords(root_midi, prog):
    """Minor triads (plus 7th) for each scale degree, as MIDI numbers."""
    out = []
    for deg in prog:
        tri = [MINOR[(deg + k) % 7] + 12 * ((deg + k) // 7) for k in (0, 2, 4, 6)]
        out.append([root_midi + x for x in tri])
    return out


def render(path, total, cut_times=(), name=None, override=None):
    p = choose(name, override)
    style, bpm = p["style"], float(p["bpm"])
    rng = np.random.default_rng(_seed(name) % (2 ** 32))
    beat = 60.0 / bpm; bar = 4 * beat
    root = 36 + p["key"]                      # bass root (C2..B2)
    chords = _chords(root + 24, PROGS[p["prog"]])
    v = p["variant"]
    drums, music = Mix(total), Mix(total)
    nbars = int(math.ceil(total / bar)) + 1
    scale = [root + 24 + x for x in MINOR] + [root + 36 + x for x in MINOR]

    for b in range(nbars):
        t0 = b * bar; ch = chords[b % len(chords)]; broot = ch[0] - 24
        intro = b == 0                         # first bar lighter: the hook is on screen
        if style == "phonk":
            for s in range(8):                 # cowbell riff on 8ths from the pentatonic
                if (s + v) % 3 != 2:
                    note = scale[[0, 2, 4, 5, 2, 4, 6, 4][(s + b) % 8] % len(scale)] + 12
                    music.add(t0 + s * beat / 2, cowbell(_mtof(note)), 0.9)
            if not intro:
                drums.add(t0, kick(1.3), 1.0); drums.add(t0 + 2.5 * beat, kick(1.3), 0.8)
                drums.add(t0 + 2 * beat, clap(rng), 0.9)
                for s in range(8):
                    drums.add(t0 + s * beat / 2, hat(rng), 0.5)
                music.add(t0, bass808(_mtof(broot), bar * 0.95, drive=4), 0.9)
        elif style == "drill":
            if not intro:
                drums.add(t0, kick(1.1), 0.9); drums.add(t0 + 1.75 * beat, kick(1.1), 0.7)
                drums.add(t0 + 2 * beat, snare(rng, 200), 0.9)
                s = 0.0
                while s < 4:                   # hats with triplet rolls
                    roll = (int(s * 2) + v) % 5 == 4
                    step = beat / 6 if roll else beat / 2
                    drums.add(t0 + s * beat, hat(rng), 0.45); s += step / beat
                nxt = chords[(b + 1) % len(chords)][0] - 24
                music.add(t0, bass808(_mtof(broot), bar * 0.6), 0.9)
                music.add(t0 + 2.5 * beat, bass808(_mtof(broot + 3), bar * 0.37, glide_to=_mtof(nxt)), 0.8)
            music.add(t0, pad([_mtof(x) for x in ch[:3]], bar, cutoff=1200, attack=0.6), 0.6)
        elif style == "afrobeats":
            for s in range(16):
                drums.add(t0 + s * beat / 4, shaker(rng), 0.6 if s % 2 else 0.9)
            for s in (0, 3, 6, 10, 12):        # 3-2 clave-ish rim pattern
                drums.add(t0 + s * beat / 4, rim(1500 + 100 * v), 0.8)
            if not intro:
                drums.add(t0, kick(), 1.0); drums.add(t0 + 1.5 * beat, kick(), 0.7); drums.add(t0 + 2 * beat, kick(), 0.9)
                drums.add(t0 + beat, snare(rng, 220, 0.15), 0.5); drums.add(t0 + 3 * beat, snare(rng, 220, 0.15), 0.6)
                for s, d in ((0, 0), (1.5, 7), (2.5, 5), (3.5, 3)):
                    music.add(t0 + s * beat, logdrum(_mtof(broot + 12 + d)), 0.8)
            for s in (0.5, 1.5, 2.5, 3.0):
                music.add(t0 + s * beat, sum(pluck(_mtof(x), 0.25, 4200) for x in ch[:3]) / 2, 0.8)
        elif style == "lofi":
            swing = beat / 6
            for s in range(8):
                drums.add(t0 + s * beat / 2 + (swing if s % 2 else 0), hat(rng), 0.25)
            if not intro:
                drums.add(t0, kick(0.8, f_hi=110), 0.8); drums.add(t0 + 2.5 * beat, kick(0.8, f_hi=110), 0.6)
                drums.add(t0 + beat, snare(rng, 180, 0.2, 3500), 0.55); drums.add(t0 + 3 * beat, snare(rng, 180, 0.2, 3500), 0.55)
                music.add(t0, bass808(_mtof(broot + 12), bar * 0.5, drive=1.2), 0.5)
            music.add(t0, keys_chord([_mtof(x) for x in ch], bar, trem=0.15), 0.9)
        elif style == "cinematic":
            if b % 2 == 0 or not intro:
                drums.add(t0, boom(), 0.9)
            if not intro:
                drums.add(t0 + 2 * beat, snare(rng, 150, 0.4, 3000), 0.6)
                for s in (3, 3.5):
                    drums.add(t0 + s * beat, kick(0.7, 0.3, 120, 60), 0.5)
            music.add(t0, pad([_mtof(x) for x in ch[:3]] + [_mtof(ch[0] - 12)], bar * 1.05, cutoff=2400, attack=0.8), 0.9)
            for s in range(8):                 # string-style ostinato
                note = [ch[0], ch[1], ch[2], ch[1]][(s + v) % 4] + 12
                music.add(t0 + s * beat / 2, pluck(_mtof(note), 0.22, 2800), 0.6)
        else:  # house
            for s in range(4):
                drums.add(t0 + s * beat, kick(1.0), 1.0 if not intro else 0.0)
                drums.add(t0 + s * beat + beat / 2, hat(rng, open_=True), 0.4)
            if not intro:
                drums.add(t0 + beat, clap(rng), 0.8); drums.add(t0 + 3 * beat, clap(rng), 0.8)
                for s in (0.5, 1.5, 2.5, 3.5):
                    music.add(t0 + s * beat, bass808(_mtof(broot + 12), beat * 0.4, drive=1.5), 0.6)
            for s in ([0.75, 2.75] if v % 2 else [0.5, 1.75, 3.0]):
                music.add(t0 + s * beat, stab([_mtof(x) for x in ch[:3]]), 0.8)

    fx = Mix(total)
    for c in cut_times:                        # whoosh riser into every cut
        fx.add(max(0.0, c - 0.4), whoosh(rng), 0.35)

    mix = 0.8 * drums.buf + 0.75 * music.buf + fx.buf
    fade = min(len(mix) // 3, int(1.2 * SR))
    mix[-fade:] *= np.linspace(1, 0, fade)
    a = int(0.03 * SR); mix[:a] *= np.linspace(0, 1, a)
    peak = np.max(np.abs(mix)) or 1.0
    mix = np.tanh(1.3 * mix / peak) * 0.89
    pcm = (mix * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
    p["key_name"] = KEYS[p["key"]] + " minor"
    return p
