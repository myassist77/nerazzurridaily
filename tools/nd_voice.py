"""Nerazzurri Daily — voiceover for the motion shorts (owner's decisions, Sept 26, 2026).

Every beat in beats.json carries a "vo" line: plain spoken American English. Italian names and words
are wrapped in square brackets — "[Corriere dello Sport] says [Parma] is the target." — and are spoken
with Italian pronunciation while the rest stays American (voice approved Sept 26, 2026: the "AFTER" test).
There is NO music: the video is voice only (the generated soundtrack was rejected on Sept 26, 2026).

Two steps, so the local copy and the sandbox copy of a video share one timing:

  python3 tools/nd_voice.py plan --json beats.json --out beats.voiced.json --wavdir ./vo
      speaks every "vo" line, sets each beat's duration to its line + 0.45 s, writes beats.voiced.json.
      Render the motion engine from beats.voiced.json (with --silent).
  python3 tools/nd_voice.py plan --json beats.voiced.json --out beats.voiced.json --wavdir ./vo --keep-durations
      the second copy: speaks the lines again but keeps the durations already in the file
      (fails if a line no longer fits its beat).
  python3 tools/nd_voice.py mix --json beats.voiced.json --wavdir ./vo --video pack/NAME.mp4 --out pack/NAME-voiced.mp4
      lays each line at its beat's start + 0.15 s, masters speech to -16 LUFS / -1.5 dBTP at 48 kHz stereo AAC,
      copies the video stream untouched and checks the result with ffprobe.
      Add --cover pack/NAME-thumb-9x16.png to open the video on the designed cover for 0.2 s: Postiz has no
      TikTok cover setting, and TikTok uses the opening frame, so this makes the thumbnail the TikTok cover.
      (The video stream is then re-encoded once, at the engine's own settings.)

Voice: Kokoro v1.0 (open source, Apache-2.0), int8 model (the full model runs out of memory on the
985 MB sandbox), voice am_michael, speed 1.08. Model files are fetched once from the kokoro-onnx GitHub
release into --model-dir (default ~/.cache/nd-voice). Needs: pip install kokoro-onnx soundfile numpy.
A line that runs long is rewritten shorter, never sped up. The build stops, with the reason, on any problem.
"""
import argparse, json, os, re, subprocess, sys, urllib.request

LEAD, TAIL = 0.15, 0.30          # silence before each line, and after it before the cut
VOICE, SPEED, SR = "am_michael", 1.08, 24000
COVER_SEC = 0.2                  # --cover: the 9:16 thumbnail holds the first 0.2 s, so it is the post's cover frame
REL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = {"kokoro-v1.0.int8.onnx": 92361271, "voices-v1.0.bin": 28214398}
# Names the Italian pronunciation tool gets wrong or that are not Italian. Add new ones here as they come up.
FIX = {
    "Nerazzurri": "nˌeraddzˈurri", "Nerazzurro": "nˌeraddzˈurro",
    "Inter": "ˈinter",
    "Hakan Çalhanoğlu": "hˈakan tʃalhanˈoːlu", "Çalhanoğlu": "tʃalhanˈoːlu", "Calhanoglu": "tʃalhanˈoːlu",
    "Chivu": "kˈivu", "Cristian Chivu": "krˈistjan kˈivu",
    "Lautaro": "lautˈaro", "Lautaro Martínez": "lautˈaro martˈines",
}

def die(msg): sys.exit(f"VOICE FAILED: {msg}")

def models(d):
    os.makedirs(d, exist_ok=True)
    for f, size in FILES.items():
        p = os.path.join(d, f)
        if not (os.path.exists(p) and os.path.getsize(p) == size):
            print(f"fetching {f} …", flush=True)
            urllib.request.urlretrieve(REL + f, p + ".part"); os.replace(p + ".part", p)
            if os.path.getsize(p) != size: die(f"{f} is {os.path.getsize(p)} bytes, expected {size}")
    return os.path.join(d, "kokoro-v1.0.int8.onnx"), os.path.join(d, "voices-v1.0.bin")

class Speaker:
    def __init__(self, model_dir):
        import kokoro_onnx
        from kokoro_onnx import Kokoro
        from kokoro_onnx.tokenizer import Tokenizer
        m, v = models(model_dir)
        self.k, self.tok = Kokoro(m, v), Tokenizer()
        self.vocab = set(json.load(open(os.path.join(os.path.dirname(kokoro_onnx.__file__), "config.json")))["vocab"])
    def it(self, w):
        p = FIX.get(w) or self.tok.phonemize(w, "it")
        p = p.replace("ɪ", "i").replace("ʊ", "u")          # Italian has no lax vowels
        return "".join(c for c in p if c in self.vocab)
    def phonemes(self, text):
        if text.count("[") != text.count("]"): die(f"unbalanced [ ] in: {text!r}")
        out = []
        for seg in re.split(r"(\[[^\]]+\])", text):
            if not seg.strip(): continue
            out.append(self.it(seg[1:-1].strip()) if seg.startswith("[") else self.tok.phonemize(seg, "en-us"))
        return " ".join(o.strip() for o in out if o.strip())
    def say(self, text):
        import numpy as np
        a, sr = self.k.create(self.phonemes(text), voice=VOICE, speed=SPEED, is_phonemes=True)
        if sr != SR or len(a) == 0: die(f"bad audio for {text!r}")
        return np.asarray(a, dtype="float32")

def plan(A):
    import soundfile as sf
    spec = json.load(open(A.json)); beats = spec["beats"]
    missing = [b["id"] for b in beats if not (b.get("vo") or "").strip()]
    if missing: die(f"every beat needs a \"vo\" line; missing on {missing}")
    os.makedirs(A.wavdir, exist_ok=True); sp = Speaker(A.model_dir); report = []
    for b in beats:
        a = sp.say(b["vo"]); sec = len(a) / SR
        sf.write(os.path.join(A.wavdir, f"{b['id']}.wav"), a, SR)
        need = round(LEAD + sec + TAIL, 2)
        if A.keep_durations:
            # the second machine's voice can run a few hundredths longer; it only needs 0.1 s of air before the cut
            if LEAD + sec + 0.10 > b["duration"]: die(f"beat {b['id']}: line is {sec:.2f}s, beat is {b['duration']}s — shorten the line")
        else:
            b["duration"] = need
        report.append((b["id"], round(sec, 2), b["duration"])); print(f"{b['id']}: voice {sec:.2f}s → beat {b['duration']}s", flush=True)
    total = round(sum(b["duration"] for b in beats), 2)
    if not (20.0 <= total <= 40.0 - COVER_SEC): die(f"voiced total is {total}s, outside 20–{40 - COVER_SEC:g} s (the cover frame adds {COVER_SEC}s) — shorten the lines (never speed up)")
    spec["voice"] = {"engine": "kokoro-v1.0-int8", "voice": VOICE, "speed": SPEED, "lead": LEAD, "tail": TAIL, "total": total}
    json.dump(spec, open(A.out, "w"), indent=1, ensure_ascii=False)
    print(f"PLAN OK {A.out} — {len(beats)} beats, {total}s")

def mix(A):
    import numpy as np, soundfile as sf
    beats = json.load(open(A.json))["beats"]; t, starts = 0.0, []
    for b in beats: starts.append(t); t += b["duration"]
    total = round(t, 3); track = np.zeros(int(total * SR) + SR, dtype="float32")
    for b, t0 in zip(beats, starts):
        a, sr = sf.read(os.path.join(A.wavdir, f"{b['id']}.wav"), dtype="float32")
        if sr != SR: die(f"{b['id']}.wav is {sr} Hz")
        if LEAD + len(a) / SR > b["duration"]: die(f"beat {b['id']}: its line overruns the beat")
        i = int((t0 + LEAD) * SR); track[i:i + len(a)] += a
    lead_in = 0.0
    if A.cover:   # TikTok (and the Shorts feed) show the opening frame: open on the designed 9:16 cover for 0.2 s
        lead_in = COVER_SEC; track = np.concatenate([np.zeros(int(lead_in * SR), dtype="float32"), track]); total = round(total + lead_in, 3)
    wav = os.path.splitext(A.out)[0] + "-vo.wav"; sf.write(wav, track[:int(total * SR)], SR)
    af = "highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000"
    if A.cover:
        vin = ["-loop", "1", "-framerate", "30", "-t", f"{lead_in}", "-i", A.cover, "-i", A.video, "-i", wav]
        vmap = ["-filter_complex", "[0:v]scale=1080:1920,setsar=1,format=yuv420p,fps=30[c];[1:v]fps=30,format=yuv420p,setsar=1[m];[c][m]concat=n=2:v=1:a=0[v]",
                "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", "30"]
    else:
        vin = ["-i", A.video, "-i", wav]; vmap = ["-map", "0:v", "-map", "1:a", "-c:v", "copy"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *vin, *vmap, "-af", af, "-ar", "48000", "-ac", "2",
                    "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.3f}", "-movflags", "+faststart", A.out], check=True)
    os.remove(wav)
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
          "format=duration:stream=codec_type,codec_name,sample_rate,channels,duration", "-of", "json", A.out],
          capture_output=True, text=True).stdout)
    v = [s for s in info["streams"] if s["codec_type"] == "video"]; au = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if len(v) != 1 or len(au) != 1: die(f"expected one video and one audio stream, got {info['streams']}")
    if au[0]["codec_name"] != "aac" or au[0]["sample_rate"] != "48000" or au[0]["channels"] != 2: die(f"audio is {au[0]}, expected AAC 48 kHz stereo")
    if abs(float(au[0]["duration"]) - float(v[0]["duration"])) > 0.2: die(f"audio {au[0]['duration']}s vs video {v[0]['duration']}s")
    lufs = subprocess.run(f"ffmpeg -nostats -i '{A.out}' -af ebur128=peak=true -f null - 2>&1 | grep -E '^ +I:|^ +Peak:'",
                          shell=True, capture_output=True, text=True).stdout.split()
    print(f"MIX OK {A.out} — {float(info['format']['duration']):.2f}s, AAC 48 kHz stereo, {' '.join(lufs)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--json", required=True); p.add_argument("--out", required=True)
    p.add_argument("--wavdir", required=True); p.add_argument("--keep-durations", action="store_true")
    p.add_argument("--model-dir", default=os.path.expanduser("~/.cache/nd-voice"))
    m = sub.add_parser("mix"); m.add_argument("--json", required=True); m.add_argument("--wavdir", required=True)
    m.add_argument("--video", required=True); m.add_argument("--out", required=True)
    m.add_argument("--cover", default=None, help="the 9:16 thumbnail PNG; it becomes the opening frame (the TikTok cover)")
    A = ap.parse_args(); plan(A) if A.cmd == "plan" else mix(A)
