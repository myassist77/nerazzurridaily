#!/usr/bin/env python3
"""Nerazzurri Daily — motion short renderer (1080x1920, 30 fps; silent by design — always pass --silent).

    python3 social_motion.py --json beats.json --out ./pack --workdir <dir with node_modules> --silent
    options: --fps 30  --silent (always, per the SOP)  --keep-frames  --name ND-2026-09-14-calha-benched

Every beat is an HTML frame with a deterministic seek(t) function; frames are captured
one by one with Playwright (no wall-clock timing, so output is reproducible), assembled
with ffmpeg, and muxed with a rights-free synthesized bed (kick/hat/drone + a whoosh on
every cut) unless --silent. Fails the build on register/colour disagreement, layout
problems (clipped text, wrapped kicker, anything in the bottom 15%), or a duration
outside 20-40 s. Never work around a failure - shorten the text and rebuild.

Needs: node + playwright + @fontsource/{anton,oswald,ibm-plex-mono,gelasio} in <workdir>,
Chromium under /opt/pw-browsers (found by glob), ffmpeg, python3 + numpy.
"""
import argparse, glob, html, json, math, os, shutil, subprocess, sys, wave

AP = argparse.ArgumentParser()
AP.add_argument("--json", required=True)
AP.add_argument("--out", default="./pack")
AP.add_argument("--workdir", default=".")
AP.add_argument("--fps", type=int, default=30)
AP.add_argument("--name", default=None, help="basename of the MP4 (default from json)")
AP.add_argument("--silent", action="store_true")
AP.add_argument("--keep-frames", action="store_true")
AP.add_argument("--thumb-only", action="store_true", help="render only the thumbnails from the json's \"thumbnail\" block")
A = AP.parse_args()

W, H = 1080, 1920
SAFE_BOTTOM = int(H * 0.85)
wd, out = os.path.abspath(A.workdir), os.path.abspath(A.out)
os.makedirs(out, exist_ok=True)
frames = os.path.join(out, "_frames")
shutil.rmtree(frames, ignore_errors=True); os.makedirs(frames)

_CHROME_PATS = ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium-*/chrome-linux64/chrome",
                os.path.expanduser("~/pw-browsers/chromium-*/chrome-linux*/chrome"),
                os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome"))
CHROME = os.environ.get("ND_CHROME") or next(
    (c for pat in _CHROME_PATS for c in sorted(glob.glob(pat))), "/opt/pw-browsers/chromium")
F = lambda p: "file://" + os.path.join(wd, "node_modules/@fontsource", p)
FONTS = {"Anton": F("anton/files/anton-latin-400-normal.woff2"),
         "IBM Plex Mono": F("ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2"),
         "Oswald": F("oswald/files/oswald-latin-600-normal.woff2"),
         "Gelasio": F("gelasio/files/gelasio-latin-400-normal.woff2")}
GROUNDS = {
    "nero":    {"bg": "#06080F", "fg": "#FFFFFF", "kick": "#8A94AE", "sub": "#AEB7CC", "acc": "#4A7BE0",
                "url": "#8FB2F0", "bar": "rgba(143,178,240,.55)", "line": "rgba(255,255,255,.28)"},
    "azzurro": {"bg": "#2B5BB8", "fg": "#FFFFFF", "kick": "rgba(255,255,255,.82)", "sub": "rgba(255,255,255,.92)",
                "acc": "#FFFFFF", "url": "rgba(255,255,255,.88)", "bar": "rgba(255,255,255,.45)", "line": "rgba(255,255,255,.35)"},
    "pink":    {"bg": "#FBEAE7", "fg": "#8C4034", "kick": "rgba(140,64,52,.80)", "sub": "rgba(140,64,52,.92)",
                "acc": "#8C4034", "url": "rgba(140,64,52,.80)", "bar": "rgba(140,64,52,.40)", "line": "rgba(140,64,52,.35)"},
}
REGISTER_GROUND = {"CONFIRMED": "azzurro", "REPORTED": "pink", "NEUTRAL": "nero"}
SITE = "nerazzurridaily.com"
FORMATIONS = {  # x (0-100 across), y (0-100, 0 = own goal) — GK first, then lines back to front
    "3-5-2":   [(50, 8), (22, 28), (50, 24), (78, 28), (10, 52), (32, 46), (50, 42), (68, 46), (90, 52), (36, 74), (64, 74)],
    "4-3-3":   [(50, 8), (14, 28), (38, 24), (62, 24), (86, 28), (28, 48), (50, 42), (72, 48), (18, 74), (50, 78), (82, 74)],
    "4-2-3-1": [(50, 8), (14, 28), (38, 24), (62, 24), (86, 28), (36, 44), (64, 44), (18, 62), (50, 60), (82, 62), (50, 80)],
    "3-4-2-1": [(50, 8), (22, 28), (50, 24), (78, 28), (12, 50), (36, 46), (64, 46), (88, 50), (32, 66), (68, 66), (50, 82)],
    "4-4-2":   [(50, 8), (14, 28), (38, 24), (62, 24), (86, 28), (14, 50), (38, 46), (62, 46), (86, 50), (36, 74), (64, 74)],
}

spec = json.load(open(A.json))
beats = spec["beats"]

# ---- REGISTER CONTROL: colour is derived from the declared register, never hand-picked ----
for b in beats:
    if b["kind"] in ("cover", "end"):
        b["ground"] = "nero"; continue
    reg = b.get("register")
    if reg not in REGISTER_GROUND:
        sys.exit(f"BUILD FAILED: beat {b['id']} must declare register CONFIRMED / REPORTED / NEUTRAL (got {reg!r})")
    want = REGISTER_GROUND[reg]
    if b.get("ground") not in (None, want):
        sys.exit(f"BUILD FAILED: beat {b['id']} declares {reg} (ground {want}) but sets ground {b['ground']!r}")
    b["ground"] = want
    kick = (b.get("kicker") or "").strip().upper()
    if reg in ("CONFIRMED", "REPORTED") and not kick.startswith(reg):
        sys.exit(f"BUILD FAILED: beat {b['id']} is {reg} but its kicker does not name that register first: {b.get('kicker')!r}")
total = round(sum(b["duration"] for b in beats), 3)
if not (20.0 <= total <= 40.0):
    sys.exit(f"BUILD FAILED: total duration {total}s is outside 20-40s")
if not (5 <= len(beats) <= 10):
    sys.exit(f"BUILD FAILED: {len(beats)} beats, must be 5-10")
if beats[0]["kind"] != "cover" or beats[-1]["kind"] != "end":
    sys.exit("BUILD FAILED: first beat must be 'cover' and last beat 'end'")

esc = lambda s: html.escape(str(s)).replace(" · ", " &nbsp;·&nbsp; ")
CSS = "".join(f'@font-face{{font-family:"{k}";src:url({v}) format("woff2")}}' for k, v in FONTS.items()) + f"""
*{{box-sizing:border-box;margin:0}} body{{background:#000}}
#f{{width:{W}px;height:{H}px;position:relative;overflow:hidden;display:flex;flex-direction:column;
   justify-content:center;align-items:center;padding:200px 96px 340px;text-align:center}}
#f.has-sleeve{{padding-right:186px}}
.sleeve{{position:absolute;right:0;top:0;bottom:0;width:110px;display:grid;grid-template-rows:3fr 2fr 4fr 2fr 3fr 2fr 4fr 3fr}}
.sleeve i{{display:block}} .sleeve i:nth-child(odd){{background:#0F1526}} .sleeve i:nth-child(even){{background:#4A7BE0}}
.mono{{font-family:"IBM Plex Mono",monospace;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap}}
.kicker{{font-size:26px;margin-bottom:46px;display:inline-flex;align-items:center;gap:18px}}
.kicker .kb{{width:14px;height:14px;border-radius:50%;flex:none}}
.kicker .kt{{overflow:hidden;white-space:nowrap}}
.wm{{font-family:Anton;font-size:74px;line-height:.95;text-transform:uppercase;color:#fff;margin-bottom:74px;letter-spacing:.01em;white-space:nowrap}}
.wm b{{color:#8FB2F0;font-weight:400}}
.big{{font-family:Anton;font-size:120px;line-height:1.12;text-transform:uppercase}}
.big.tight{{font-size:104px}} .big.xtight{{font-size:90px}}
.mask{{overflow:hidden;padding:0 .04em}} .mask>span{{display:inline-block;will-change:transform;white-space:nowrap}}
.sub{{font-size:27px;letter-spacing:.11em;margin-top:44px;line-height:1.7}}
.quote{{font-family:Gelasio,Georgia,serif;font-size:74px;line-height:1.22;font-style:italic;text-transform:none}}
.quote .w{{display:inline-block;margin-right:.26em}} .quote .w:last-of-type{{margin-right:0}}
.stat{{font-family:Anton;font-size:420px;line-height:.95}}
.statlbl{{font-family:Oswald;font-size:72px;line-height:1.1;text-transform:uppercase;margin-top:6px}}
.teamline{{font-family:Anton;font-size:86px;line-height:1.05;text-transform:uppercase;white-space:nowrap}}
.score{{font-family:Anton;font-size:250px;line-height:1;margin:14px 0;white-space:nowrap}} .score .dim{{opacity:.5}}
.kickoff{{font-family:Anton;font-size:150px;line-height:1;margin-top:30px;white-space:nowrap}}
.tl{{width:100%;text-align:left;font-family:Oswald;font-size:54px;line-height:1.15;text-transform:uppercase}}
.tl .row{{display:flex;gap:34px;align-items:flex-start;padding:22px 0;position:relative}}
.tl .dot{{width:22px;height:22px;border-radius:50%;flex:none;margin-top:18px}}
.tl .when{{font-family:"IBM Plex Mono",monospace;font-size:24px;letter-spacing:.12em;margin-top:6px}}
.tl .rule{{position:absolute;left:10px;top:0;width:2px;height:100%}}
.pitch{{width:700px;height:900px;position:relative}}
.pitch svg{{position:absolute;inset:0;width:100%;height:100%}}
.pl{{position:absolute;transform:translate(-50%,-50%);display:flex;flex-direction:column;align-items:center;gap:8px;white-space:nowrap}}
.pl i{{width:44px;height:44px;border-radius:50%;display:block}}
.pl span{{font-family:Oswald;font-size:30px;text-transform:uppercase;letter-spacing:.02em;line-height:1}}
.outline{{font-family:Oswald;font-size:46px;text-transform:uppercase;margin-top:40px;white-space:nowrap;position:relative;display:inline-block}}
.outline .strike{{position:absolute;left:0;top:50%;height:6px;width:100%;transform-origin:left center}}
.footer{{position:absolute;left:96px;right:96px;bottom:300px;display:flex;flex-direction:column;align-items:center;gap:16px}}
#f.has-sleeve .footer{{right:186px}} .footer .bar{{width:56px;height:4px;border-radius:2px}} .footer .url{{font-size:25px;letter-spacing:.16em}}
.cta{{font-family:Anton;font-size:96px;line-height:1.08;text-transform:uppercase;margin-top:8px;white-space:nowrap}}
.prog{{position:absolute;left:0;top:0;height:10px;transform-origin:left center}}
.wipe{{position:absolute;inset:0;transform-origin:left center}}
"""

def mask(lines, cls="big"):
    return "".join(f'<div class="mask"><span data-line="{i}">{esc(l)}</span></div>' for i, l in enumerate(lines))

def build_html(idx, b):
    g = GROUNDS[b["ground"]]; kind = b["kind"]
    prev = GROUNDS[beats[idx - 1]["ground"]]["bg"] if idx else None
    p = []
    sleeve = '<div class="sleeve"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>'
    kicker = (f'<div class="mono kicker" style="color:{g["kick"]}"><i class="kb" style="background:{g["acc"]}"></i>'
              f'<span class="kt">{esc(b.get("kicker", ""))}</span></div>') if b.get("kicker") else ""
    sub = (f'<div class="mono sub" style="color:{g["sub"]}">' + "".join(f'<div class="s">{esc(s)}</div>' for s in b["sub"]) + "</div>") if b.get("sub") else ""
    sizecls = lambda ls: "big " + ("xtight" if max(map(len, ls)) > 24 else "tight" if max(map(len, ls)) > 19 else "")

    if kind == "cover":
        p += [sleeve, f'<div class="mono kicker" style="color:{g["kick"]}"><span class="kt">{esc(b["eyebrow"])}</span></div>',
              '<div class="wm">Nerazzurri <b>Daily</b></div>', f'<div class="{sizecls(b["lines"])}" style="color:{g["fg"]}">{mask(b["lines"])}</div>']
    elif kind == "item":
        p += [kicker, f'<div class="{sizecls(b["lines"])}" style="color:{g["fg"]}">{mask(b["lines"])}</div>', sub]
    elif kind == "quote":
        words = " ".join(b["lines"]).split()
        p += [kicker, f'<div class="quote" style="color:{g["fg"]}">&ldquo;' + "".join(f'<span class="w">{esc(w)}</span>' for w in words) + "&rdquo;</div>", sub]
    elif kind == "stat":
        p += [kicker, f'<div class="stat" style="color:{g["fg"]}"><span class="num" data-n="{b["number"]}">{b["number"]}</span>{esc(b.get("suffix", ""))}</div>',
              f'<div class="statlbl" style="color:{g["fg"]}">{mask(b["lines"], "statlbl")}</div>', sub]
    elif kind == "result":
        p += [kicker, f'<div class="teamline" style="color:{g["fg"]}"><div class="mask"><span data-side="l">{esc(b["home"])}</span></div></div>',
              f'<div class="score" style="color:{g["fg"]}"><span class="num{" dim" if b.get("inter","away")!="home" else ""}" data-n="{b["score_home"]}">{b["score_home"]}</span><span class="dim">&#8211;</span><span class="num{" dim" if b.get("inter","away")=="home" else ""}" data-n="{b["score_away"]}">{b["score_away"]}</span></div>',
              f'<div class="teamline" style="color:{g["fg"]}"><div class="mask"><span data-side="r">{esc(b["away"])}</span></div></div>', sub]
    elif kind == "fixture":
        p += [sleeve, kicker, f'<div class="{sizecls(b["lines"])}" style="color:{g["fg"]}">{mask(b["lines"])}</div>',
              f'<div class="mono sub" style="color:{g["sub"]};margin-top:22px"><div class="s">{esc(b["sub_top"])}</div></div>',
              f'<div class="kickoff" style="color:#8FB2F0"><div class="mask"><span>{esc(b["big"])}</span></div></div>', sub]
    elif kind == "timeline":
        rows = "".join(f'<div class="row"><i class="dot" style="background:{g["acc"]}"></i><div><div>{esc(e["text"])}</div>'
                       f'<div class="when" style="color:{g["kick"]}">{esc(e["when"])}</div></div></div>' for e in b["events"])
        p += [kicker, f'<div class="tl" style="color:{g["fg"]}"><div style="position:relative"><i class="rule" style="background:{g["line"]}"></i>{rows}</div></div>', sub]
    elif kind == "pitch":
        pos = FORMATIONS[b["formation"]]
        if len(b["players"]) != 11: sys.exit(f"BUILD FAILED: beat {b['id']} needs exactly 11 players")
        dots = "".join(f'<div class="pl" style="left:{x}%;top:{100-y}%"><i style="background:{g["acc"]}"></i><span style="color:{g["fg"]}">{esc(n)}</span></div>'
                       for (x, y), n in zip(pos, b["players"]))
        svg = (f'<svg viewBox="0 0 700 900" fill="none" stroke="{g["line"]}" stroke-width="4">'
               '<path class="pp" d="M10 10H690V890H10Z M10 450H690 M250 890V830H450V890 M180 890V740H520V890 M250 10V70H450V10 M180 10V160H520V10"/>'
               '<circle class="pp" cx="350" cy="450" r="100"/></svg>')
        outl = ""
        if b.get("out"):
            outl = (f'<div class="outline" style="color:{g["fg"]}"><span class="mono" style="font-size:26px;letter-spacing:.14em;opacity:.8">{esc(b.get("out_label","OUT"))} </span>'
                    f'{esc(" · ".join(b["out"]))}<i class="strike" style="background:{g["acc"]}"></i></div>')
        p += [kicker, f'<div class="pitch">{svg}{dots}</div>', outl, sub]
    elif kind == "end":
        p += [sleeve, '<div class="wm">Nerazzurri <b>Daily</b></div>',
              f'<div class="mono sub" style="color:{g["sub"]};margin-top:6px">' + "".join(f'<div class="s">{esc(s)}</div>' for s in b["sub"]) + "</div>",
              f'<div class="cta" style="color:{g["url"]}">{esc(SITE)}</div>']
    else:
        sys.exit(f"BUILD FAILED: unknown beat kind {kind!r}")

    if kind != "end":
        p.append(f'<div class="footer"><div class="bar" style="background:{g["bar"]}"></div><div class="mono url" style="color:{g["url"]}">{esc(SITE)}</div></div>')
    p.append(f'<div class="prog" style="background:{g["acc"]};opacity:.9"></div>')
    if prev:
        p.append(f'<div class="wipe" style="background:{prev}"></div>')
    body = "".join(p)
    sleeve_cls = "has-sleeve" if sleeve in body else ""
    js = r"""
<script>
const D=%DUR%, KIND=%KIND%, T0=%T0%, TOTAL=%TOTAL%, FPS=%FPS%;
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const oExpo=x=>x>=1?1:1-Math.pow(2,-10*x), oCubic=x=>1-Math.pow(1-x,3), ioCubic=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
const seg=(t,s,d)=>clamp((t-s)/d);
const $=s=>Array.from(document.querySelectorAll(s));
function fit(){
  const f=document.getElementById('f'), cs=getComputedStyle(f);
  const avail=f.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
  $('.big,.teamline,.kickoff,.score,.wm,.cta,.kicker,.outline,.stat').forEach(el=>{
    const widest=()=>Math.max(...(el.querySelectorAll('span').length?Array.from(el.querySelectorAll('span')):[el]).map(k=>k.scrollWidth), el.scrollWidth);
    let size=parseFloat(getComputedStyle(el).fontSize), g=0;
    while(widest()>avail && size>22 && g<400){size-=2; el.style.fontSize=size+'px'; g++;}
  });
}
window.seek=function(t){
  // progress bar (global) + entry wipe
  $('.prog').forEach(e=>{e.style.width=(100*clamp((T0+t)/TOTAL))+'%';});
  $('.wipe').forEach(e=>{const p=ioCubic(seg(t,0,.42)); e.style.transform=`translateX(${p*125}%) skewX(-10deg) scale(1.3)`; e.style.display=p>=1?'none':'block';});
  // kicker: dot pops, text reveals left->right
  $('.kicker').forEach(k=>{const kb=k.querySelector('.kb'), kt=k.querySelector('.kt');
    if(kb) kb.style.transform=`scale(${oCubic(seg(t,.25,.3))})`;
    if(kt){const w=kt.dataset.w||(kt.dataset.w=kt.scrollWidth); kt.style.width=(w*oExpo(seg(t,.35,.7)))+'px';}});
  // masked lines rise in, staggered
  $('.mask>span').forEach((s,i)=>{const p=oExpo(seg(t,.45+i*.13,.7)); s.style.transform=`translateY(${(1-p)*115}%)`;});
  $('.mask>span[data-side]').forEach(s=>{const p=oExpo(seg(t,.45,.7)); s.style.transform=`translateX(${(1-p)*(s.dataset.side==='l'?-60:60)}%)`; s.style.opacity=p;});
  // sub lines fade up
  $('.sub .s').forEach((s,i)=>{const p=oCubic(seg(t,1.15+i*.15,.5)); s.style.opacity=p; s.style.transform=`translateY(${(1-p)*24}px)`;});
  // quote words
  $('.quote .w').forEach((w,i)=>{const p=oCubic(seg(t,.5+i*.07,.35)); w.style.opacity=.18+.82*p; w.style.transform=`translateY(${(1-p)*10}px)`;});
  // counters
  $('.num').forEach(n=>{const target=parseFloat(n.dataset.n); if(isNaN(target)){return;} const p=oCubic(seg(t,.5,1.3)); n.textContent=String(Math.round(target*p));});
  // stat scale pop
  $('.stat').forEach(s=>{const p=seg(t,.45,.9); s.style.transform=`scale(${.7+.3*oExpo(p)})`; s.style.opacity=oCubic(seg(t,.45,.4));});
  // timeline rows + rule
  $('.tl .row').forEach((r,i)=>{const p=oExpo(seg(t,.7+i*.45,.6)); r.style.opacity=p; r.style.transform=`translateX(${(1-p)*80}px)`;});
  $('.tl .rule').forEach(r=>{r.style.transform=`scaleY(${oCubic(seg(t,.6,1.6))})`; r.style.transformOrigin='top';});
  // pitch: lines draw, players pop
  $('.pp').forEach(pp=>{const L=pp.getTotalLength(); pp.style.strokeDasharray=L; pp.style.strokeDashoffset=L*(1-oCubic(seg(t,.3,1.1)));});
  $('.pl').forEach((pl,i)=>{const p=oExpo(seg(t,1.0+i*.14,.5)); pl.style.opacity=p; pl.style.transform=`translate(-50%,-50%) scale(${.4+.6*p})`;});
  $('.outline').forEach(o=>{const p=oCubic(seg(t,2.7,.4)); o.style.opacity=p; const st=o.querySelector('.strike'); if(st) st.style.transform=`scaleX(${oExpo(seg(t,3.1,.5))})`;});
  // cover: sleeve stripes slide in, wordmark drops
  $('.sleeve i').forEach((s,i)=>{const p=oExpo(seg(t,.05+i*.06,.6)); s.style.transform=`translateX(${(1-p)*120}%)`;});
  $('.wm').forEach(w=>{const p=oExpo(seg(t,.25,.7)); w.style.opacity=p; w.style.transform=`translateY(${(1-p)*-40}px)`;});
  // footer lockup, end-card url pulse
  $('.footer').forEach(f=>{const p=oCubic(seg(t,1.0,.6)); f.style.opacity=p;});
  $('.cta').forEach(c=>{const p=oExpo(seg(t,.9,.8)); const pulse=1+.025*Math.sin(Math.max(0,t-1.7)*4.2); c.style.opacity=p; c.style.transform=`scale(${(.85+.15*p)*pulse})`;});
  document.body.dataset.t=t;
};
document.fonts.ready.then(()=>{fit(); window.seek(0); document.body.dataset.fitted='1';});
</script>"""
    js = (js.replace("%DUR%", str(b["duration"])).replace("%KIND%", json.dumps(kind))
            .replace("%T0%", str(b["_t0"])).replace("%TOTAL%", str(total)).replace("%FPS%", str(A.fps)))
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div id="f" class="{sleeve_cls}" style="background:{g["bg"]}">{body}</div>{js}</body></html>')

# ---- THUMBNAILS: designed 9:16 (Shorts custom thumbnail / TikTok cover) + 16:9 ------------------
THUMB_CSS = "".join(f'@font-face{{font-family:"{k}";src:url({v}) format("woff2")}}' for k, v in FONTS.items()) + """
*{box-sizing:border-box;margin:0} body{background:#000}
.mono{font-family:"IBM Plex Mono",monospace;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap}
.anton{font-family:Anton;text-transform:uppercase;line-height:.92;white-space:nowrap}
.pill{display:inline-block;padding:.45em .9em;border-radius:999px;font-weight:600}
.wm{font-family:Anton;text-transform:uppercase;white-space:nowrap;color:#fff}
.wm b{color:#8FB2F0;font-weight:400}
"""
def _reg(block):
    reg = block.get("register")
    if reg not in REGISTER_GROUND: sys.exit(f"BUILD FAILED: thumbnail block must declare register (got {reg!r})")
    k = (block.get("kicker") or "").strip().upper()
    if reg in ("CONFIRMED", "REPORTED") and not k.startswith(reg):
        sys.exit(f"BUILD FAILED: thumbnail kicker must name its register first: {block.get('kicker')!r}")
    return GROUNDS[REGISTER_GROUND[reg]]

def thumb_html(T, W_, H_):
    style = T.get("style", "auto")
    if style == "auto": style = "number" if T.get("number") else "split"
    land = W_ > H_
    lines = lambda ls, size, color: "".join(f'<div class="anton fit" style="font-size:{size}px;color:{color}">{esc(l)}</div>' for l in ls)
    if style == "split":
        a, b = T["top"], T["bottom"]; ga, gb = _reg(a), _reg(b)
        big = 190 if not land else 150
        if land:
            body = (f'<div style="position:absolute;inset:0;background:{ga["bg"]}"></div>'
                    f'<div style="position:absolute;left:52%;top:0;right:0;bottom:0;background:{gb["bg"]};clip-path:polygon(12% 0,100% 0,100% 100%,0 100%)"></div>'
                    f'<div style="position:absolute;left:60px;top:80px;width:560px"><div class="mono" style="font-size:24px;margin-bottom:22px;color:{ga["kick"]}">● {esc(a["kicker"])}</div>{lines(a["lines"], big, ga["fg"])}</div>'
                    f'<div style="position:absolute;left:720px;top:80px;width:520px"><div class="mono" style="font-size:24px;margin-bottom:22px;color:{gb["kick"]}">● {esc(b["kicker"])}</div>{lines(b["lines"], big, gb["fg"])}'
                    + (f'<div class="mono" style="font-size:22px;margin-top:26px;color:{gb["sub"]};white-space:normal;line-height:1.5">{esc(b["sub"])}</div>' if b.get("sub") else "") + '</div>'
                    f'<div class="wm" style="position:absolute;right:50px;bottom:36px;font-size:40px">Nerazzurri <b>Daily</b></div>')
        else:
            body = (f'<div style="position:absolute;inset:0;background:{gb["bg"]}"></div>'
                    f'<div style="position:absolute;left:0;top:0;width:1080px;height:980px;background:{ga["bg"]};clip-path:polygon(0 0,100% 0,100% 82%,0 100%)"></div>'
                    f'<div style="position:absolute;left:90px;top:150px;width:900px"><div class="mono" style="font-size:34px;margin-bottom:26px;color:{ga["kick"]}">● {esc(a["kicker"])}</div>{lines(a["lines"], big, ga["fg"])}</div>'
                    f'<div style="position:absolute;left:90px;top:1080px;width:900px"><div class="mono" style="font-size:34px;margin-bottom:26px;color:{gb["kick"]}">● {esc(b["kicker"])}</div>{lines(b["lines"], big, gb["fg"])}'
                    + (f'<div class="mono" style="font-size:34px;margin-top:40px;color:{gb["sub"]};white-space:normal;line-height:1.5">{esc(b["sub"])}</div>' if b.get("sub") else "") + '</div>'
                    f'<div class="wm" style="position:absolute;right:80px;bottom:70px;font-size:56px">Nerazzurri <b>Daily</b></div>')
    elif style == "number":
        n = T["number"]; g = _reg(n)
        pill_g = GROUNDS[REGISTER_GROUND[n.get("pill_register", "REPORTED")]] if n.get("pill") else None
        sleeve = "".join(f'<i style="display:block;background:{c}"></i>' for c in ["#0F1526", "#4A7BE0"] * 4)
        pill = (f'<span class="mono pill" style="background:{pill_g["bg"]};color:{pill_g["fg"]};font-size:{30 if not land else 22}px">{esc(n["pill"])}</span>' if pill_g else "")
        if land:
            body = (f'<div style="position:absolute;inset:0;background:#06080F"></div>'
                    f'<div style="position:absolute;right:0;top:0;bottom:0;width:90px;display:grid;grid-template-rows:3fr 2fr 4fr 2fr 3fr 2fr 4fr 3fr">{sleeve}</div>'
                    f'<div style="position:absolute;left:60px;top:56px"><span class="mono pill" style="background:{g["bg"]};color:{g["fg"]};font-size:22px">{esc(n["kicker"])}</span></div>'
                    f'<div class="anton fit" style="position:absolute;left:50px;top:110px;font-size:560px;line-height:.85;color:#4A7BE0">{esc(n["big"])}</div>'
                    f'<div style="position:absolute;left:{560 if len(str(n["big"]))<3 else 700}px;top:150px;width:560px">{lines(n["lines_a"], 118, "#fff")}{lines(n.get("lines_b", []), 118, "#E7B4AE")}</div>'
                    f'<div style="position:absolute;left:60px;bottom:40px">{pill}</div>'
                    f'<div class="wm" style="position:absolute;right:130px;bottom:40px;font-size:40px">Nerazzurri <b>Daily</b></div>')
        else:
            body = (f'<div style="position:absolute;inset:0;background:#06080F"></div>'
                    f'<div style="position:absolute;right:0;top:0;bottom:0;width:150px;display:grid;grid-template-rows:3fr 2fr 4fr 2fr 3fr 2fr 4fr 3fr">{sleeve}</div>'
                    f'<div style="position:absolute;left:90px;top:150px"><span class="mono pill" style="background:{g["bg"]};color:{g["fg"]};font-size:30px">{esc(n["kicker"])}</span></div>'
                    f'<div class="anton fit" style="position:absolute;left:70px;top:280px;font-size:760px;line-height:.85;color:#4A7BE0;max-width:840px">{esc(n["big"])}</div>'
                    f'<div style="position:absolute;left:90px;top:1010px;width:840px">{lines(n["lines_a"], 150, "#fff")}{lines(n.get("lines_b", []), 150, "#E7B4AE")}</div>'
                    f'<div style="position:absolute;left:90px;bottom:180px">{pill}</div>'
                    f'<div class="wm" style="position:absolute;left:90px;bottom:80px;font-size:56px">Nerazzurri <b>Daily</b></div>')
    else:
        sys.exit(f"BUILD FAILED: unknown thumbnail style {style!r}")
    fit = """<script>document.fonts.ready.then(()=>{const F=document.getElementById('f');
document.querySelectorAll('.fit').forEach(el=>{const box=el.parentElement===F?F:el.parentElement;const avail=(box===F?F.clientWidth-el.offsetLeft-60:box.clientWidth);
let s=parseFloat(getComputedStyle(el).fontSize),g=0;while(el.scrollWidth>avail&&s>30&&g<300){s-=2;el.style.fontSize=s+'px';g++;}});
const bad=[];document.querySelectorAll('#f div,#f span').forEach(el=>{if(!el.innerText||!el.innerText.trim()||el.querySelector('div'))return;const r=el.getBoundingClientRect();
if(r.left<30||r.right>F.clientWidth-30||r.top<0||r.bottom>F.clientHeight-20)bad.push(el.innerText.slice(0,40)+' @'+Math.round(r.right)+','+Math.round(r.bottom));});
document.body.dataset.bad=JSON.stringify(bad);document.body.dataset.fitted='1';});</script>"""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{THUMB_CSS}</style></head><body>'
            f'<div id="f" style="width:{W_}px;height:{H_}px;position:relative;overflow:hidden">{body}</div>{fit}</body></html>')

def render_thumbnails(name):
    T = spec.get("thumbnail")
    if not T: return []
    jobs = []
    for tag, (w_, h_) in {"9x16": (1080, 1920), "16x9": (1280, 720)}.items():
        hp = os.path.join(wd, f"_thumb_{tag}.html"); open(hp, "w").write(thumb_html(T, w_, h_))
        jobs.append({"html": hp, "png": os.path.join(out, f"{name}-thumb-{tag}.png"), "w": w_, "h": h_})
    js = r"""const {chromium}=require('playwright');const fs=require('fs');const jobs=JSON.parse(fs.readFileSync(process.argv[2]));
(async()=>{const b=await chromium.launch({executablePath:process.argv[3]});const rep=[];
for(const j of jobs){const p=await b.newPage({viewport:{width:j.w,height:j.h}});await p.goto('file://'+j.html);
await p.waitForFunction(()=>document.body.dataset.fitted==='1');await p.waitForTimeout(250);
rep.push({png:j.png,bad:JSON.parse(await p.evaluate(()=>document.body.dataset.bad))});await p.locator('#f').screenshot({path:j.png});await p.close();}
await b.close();fs.writeFileSync(process.argv[4],JSON.stringify(rep));})().catch(e=>{console.error(e);process.exit(2);});"""
    open(os.path.join(wd, "_thumb.js"), "w").write(js); jp = os.path.join(wd, "_thumb_jobs.json"); open(jp, "w").write(json.dumps(jobs))
    rp = os.path.join(wd, "_thumb_report.json")
    subprocess.run(["node", "_thumb.js", jp, CHROME, rp], cwd=wd, check=True)
    rep = json.load(open(rp)); bad = [r for r in rep if r["bad"]]
    if bad:
        print("BUILD FAILED — thumbnail layout problems:")
        for r in bad: print("  ", os.path.basename(r["png"]), r["bad"])
        sys.exit(1)
    return [j["png"] for j in jobs]

NAME = A.name or f"ND-{spec.get('date_iso', 'video')}-{spec.get('slug', 'short')}"
if A.thumb_only:
    for p_ in render_thumbnails(NAME): print("OK", p_)
    sys.exit(0)

t0 = 0.0
for b in beats:
    b["_t0"] = round(t0, 3); t0 += b["duration"]

jobs = []
for i, b in enumerate(beats):
    hp = os.path.join(wd, f"_m_{b['id']}.html"); open(hp, "w").write(build_html(i, b))
    nf = int(round(b["duration"] * A.fps))
    jobs.append({"id": b["id"], "html": hp, "dur": b["duration"], "frames": nf, "first": sum(j["frames"] for j in jobs)})

shot_js = r"""
const { chromium } = require('playwright'); const fs = require('fs');
const [,, jobsPath, framesDir, reportPath, fpsS, chrome, safeS] = process.argv;
const jobs = JSON.parse(fs.readFileSync(jobsPath)); const FPS = +fpsS, SAFE = +safeS;
(async () => {
  const b = await chromium.launch({ executablePath: chrome });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const report = [];
  for (const j of jobs) {
    await p.goto('file://' + j.html);
    await p.waitForFunction(() => document.body.dataset.fitted === '1', null, { timeout: 15000 });
    // layout check at the beat's settled state (everything landed)
    await p.evaluate(t => window.seek(t), j.dur - 0.05);
    const issues = await p.evaluate((safeBottom) => {
      const out = []; const frame = document.getElementById('f'); const GUTTER = 40;
      const RIGHT = frame.classList.contains('has-sleeve') ? 1080 - 110 - 16 : 1080 - GUTTER;
      document.querySelectorAll('#f div, #f span').forEach((el) => {
        if (el.closest('.sleeve') || el.closest('.wipe') || el.classList.contains('prog') || el.classList.contains('mask')) return;
        if (el.children.length && el.querySelector('div,span')) return; // measure leaves only
        if (!el.innerText || !el.innerText.trim()) return;
        const r = el.getBoundingClientRect(); const t = el.innerText.replace(/\n/g, ' / ').slice(0, 60);
        if (r.width === 0 || r.height === 0) return;
        if (r.left < GUTTER) out.push('CLIPPED LEFT (' + Math.round(r.left) + 'px) :: ' + t);
        if (r.right > RIGHT) out.push('CROWDS RIGHT EDGE/SLEEVE (' + Math.round(r.right) + 'px) :: ' + t);
        if (r.top < 0) out.push('ABOVE FRAME :: ' + t);
        if (r.bottom > safeBottom) out.push('BELOW SAFE LINE (' + Math.round(r.bottom) + 'px) :: ' + t);
      });
      const foot = document.querySelector('.footer');
      if (foot) { const fTop = foot.getBoundingClientRect().top;
        document.querySelectorAll('#f div').forEach((el) => {
          if (el.closest('.footer') || el.closest('.sleeve') || el.classList.contains('prog') || el.classList.contains('wipe')) return;
          if (el.querySelector('div')) return; if (!el.innerText || !el.innerText.trim()) return;
          const r = el.getBoundingClientRect(); if (r.height && r.bottom > fTop - 20) out.push('CONTENT COLLIDES WITH URL LOCKUP :: ' + el.innerText.replace(/\n/g,' / ').slice(0,60)); }); }
      document.querySelectorAll('.kicker').forEach((el) => { const lh = parseFloat(getComputedStyle(el).fontSize) * 1.6;
        if (el.getBoundingClientRect().height > lh) out.push('KICKER WRAPPED :: ' + el.innerText.slice(0,60)); });
      document.querySelectorAll('.mask>span').forEach((el) => { const m = el.parentElement.getBoundingClientRect(), r = el.getBoundingClientRect();
        if (r.width > m.width + 2) out.push('LINE WIDER THAN ITS MASK :: ' + el.innerText.slice(0,60)); });
      return out;
    }, SAFE);
    report.push({ id: j.id, issues });
    if (issues.length) continue;
    for (let k = 0; k < j.frames; k++) {
      await p.evaluate(t => window.seek(t), k / FPS);
      const n = String(j.first + k).padStart(5, '0');
      await p.screenshot({ path: `${framesDir}/${n}.png`, clip: { x: 0, y: 0, width: 1080, height: 1920 } });
    }
    fs.copyFileSync(`${framesDir}/${String(j.first + j.frames - 1).padStart(5,'0')}.png`, `${framesDir}/_settled_${j.id}.png`);
  }
  await b.close(); fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
})().catch(e => { console.error(e); process.exit(2); });
"""
open(os.path.join(wd, "_m_jobs.json"), "w").write(json.dumps(jobs))
open(os.path.join(wd, "_m_shot.js"), "w").write(shot_js)
rep = os.path.join(wd, "_m_report.json")
subprocess.run(["node", "_m_shot.js", os.path.join(wd, "_m_jobs.json"), frames, rep, str(A.fps), CHROME, str(SAFE_BOTTOM)], cwd=wd, check=True)
report = json.load(open(rep)); bad = [r for r in report if r["issues"]]
if bad:
    print("BUILD FAILED — layout problems:")
    for r in bad:
        for i in r["issues"]: print(f"  {r['id']}: {i}")
    sys.exit(1)

# keep one settled still per beat for QA reading
stills = os.path.join(out, "stills"); shutil.rmtree(stills, ignore_errors=True); os.makedirs(stills)
for f in glob.glob(os.path.join(frames, "_settled_*.png")):
    shutil.move(f, os.path.join(stills, os.path.basename(f)[9:]))

# ---- soundtrack: rights-free, synthesized here (kick + hat + low drone, whoosh on every cut) ----
def soundtrack(path):
    import numpy as np
    sr = 48000; n = int(total * sr); t = np.arange(n) / sr; mix = np.zeros(n)
    bpm = spec.get("bpm", 126); step = 60 / bpm
    for k in np.arange(0, total, step):            # kick on every beat
        i = int(k * sr); L = int(.32 * sr); tt = np.arange(L) / sr
        env = np.exp(-tt * 14); f = 52 + 90 * np.exp(-tt * 38)
        mix[i:i + L] += .85 * env[:n - i] * np.sin(2 * np.pi * np.cumsum(f) / sr)[:n - i]
    rng = np.random.default_rng(7)
    for k in np.arange(step / 2, total, step):      # hat on the off-beat
        i = int(k * sr); L = int(.06 * sr)
        mix[i:i + L] += .10 * np.exp(-np.arange(L) / sr * 90)[:n - i] * rng.standard_normal(L)[:n - i]
    drone = .10 * (np.sin(2 * np.pi * 55 * t) + .5 * np.sin(2 * np.pi * 110.5 * t) + .3 * np.sin(2 * np.pi * 164.8 * t))
    drone *= .6 + .4 * np.sin(2 * np.pi * t / 6)
    mix += drone
    for b in beats[1:]:                             # whoosh riser into every cut
        end = b["_t0"]; L = int(.45 * sr); i = max(0, int((end - .4) * sr)); tt = np.arange(L) / sr
        noise = rng.standard_normal(L); sweep = np.sin(2 * np.pi * (300 + 2500 * tt / .45) * tt)
        w = .35 * (tt / .45) ** 2 * (noise * .4 + sweep * .6)
        j = min(n, i + L); mix[i:j] += w[:j - i]
    fade = int(1.2 * sr); mix[-fade:] *= np.linspace(1, 0, fade); mix[:int(.05*sr)] *= np.linspace(0, 1, int(.05*sr))
    mix = np.tanh(mix * 1.6) * .85
    pcm = (mix * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())

name = NAME
mp4 = os.path.join(out, name + ".mp4")
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(A.fps), "-i", os.path.join(frames, "%05d.png")]
if not A.silent:
    wav = os.path.join(wd, "_m_bed.wav"); soundtrack(wav)
    cmd += ["-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-shortest"]
cmd += ["-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-movflags", "+faststart", "-r", str(A.fps), mp4]
subprocess.run(cmd, check=True)
probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", mp4], capture_output=True, text=True).stdout
info = json.loads(probe); dur = float(info["format"]["duration"])
if abs(dur - total) > 0.6: sys.exit(f"BUILD FAILED: MP4 is {dur:.2f}s, beats sum to {total}s")
if not A.keep_frames: shutil.rmtree(frames, ignore_errors=True)
thumbs = render_thumbnails(name)
json.dump({"mp4": mp4, "seconds": round(dur, 2), "beats": len(beats), "audio": not A.silent,
           "streams": info["streams"], "stills": stills, "thumbnails": thumbs}, open(os.path.join(out, "manifest.json"), "w"), indent=2)
print(f"OK {mp4} — {dur:.2f}s, {len(beats)} beats, {'with soundtrack' if not A.silent else 'silent'}; settled stills in {stills}; thumbnails: {', '.join(os.path.basename(t) for t in thumbs) or 'none (no thumbnail block)'}")
