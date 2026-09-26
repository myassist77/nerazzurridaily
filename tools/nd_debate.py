#!/usr/bin/env python3
"""Nerazzurri Daily — THE DEBATE renderer (1080x1920, 30 fps). Evergreen opinion shorts, a different look from the daily pack.

    python3 nd_debate.py --json debate.json --out ./pack --workdir <dir with node_modules> --name ND-DEBATE-2026-09-26-greatest-keeper

The look ("the curva"): a nero ground with the black-and-blue shirt stripes low in the mix, a floodlight glow,
gold (#E8C547) for honours and the verdict, Anton for the big lines, Oswald for names, IBM Plex Mono for kickers.
No CONFIRMED/REPORTED registers here — a debate is opinion, and it says so on the frame ("THE DEBATE", "OUR PICK").
Every beat is an HTML frame with a deterministic seek(t); frames are captured with Playwright and assembled with
ffmpeg. The video is rendered silent; tools/nd_voice.py plan/mix adds the voiceover (same recipe as the daily pack).
Fails the build on clipped text, anything in the bottom 15%, a wrapped kicker, or a total outside 20–40 s.

Beat kinds: hook · lineup · card · versus · verdict · text · end. See beats.debate.example.json in the repo.
Needs: node + playwright + @fontsource/{anton,oswald,ibm-plex-mono} in <workdir>, Chromium under /opt/pw-browsers, ffmpeg.
"""
import argparse, glob, html, json, os, shutil, subprocess, sys

AP = argparse.ArgumentParser()
AP.add_argument("--json", required=True)
AP.add_argument("--out", default="./pack")
AP.add_argument("--workdir", default=".")
AP.add_argument("--fps", type=int, default=30)
AP.add_argument("--name", default=None)
AP.add_argument("--keep-frames", action="store_true")
AP.add_argument("--thumb-only", action="store_true")
A = AP.parse_args()

W, H = 1080, 1920
SAFE_BOTTOM = int(H * 0.85)
wd, out = os.path.abspath(A.workdir), os.path.abspath(A.out)
os.makedirs(out, exist_ok=True)
frames = os.path.join(out, "_frames"); shutil.rmtree(frames, ignore_errors=True); os.makedirs(frames)
_CHROME_PATS = ("/opt/pw-browsers/chromium-*/chrome-linux/chrome", "/opt/pw-browsers/chromium-*/chrome-linux64/chrome",
                os.path.expanduser("~/pw-browsers/chromium-*/chrome-linux*/chrome"), os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome"))
CHROME = os.environ.get("ND_CHROME") or next((c for pat in _CHROME_PATS for c in sorted(glob.glob(pat))), "/opt/pw-browsers/chromium")
F = lambda p: "file://" + os.path.join(wd, "node_modules/@fontsource", p)
FONTS = {"Anton": F("anton/files/anton-latin-400-normal.woff2"), "IBM Plex Mono": F("ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2"),
         "Oswald": F("oswald/files/oswald-latin-600-normal.woff2")}
NERO, NAVY, BLUE, LBLUE, GOLD, PAPER, MUTED = "#06080F", "#0B1020", "#2B5BB8", "#4A7BE0", "#E8C547", "#EEF1F6", "#8A94AE"
SITE = "nerazzurridaily.com"

spec = json.load(open(A.json)); beats = spec["beats"]
KINDS = {"hook", "lineup", "card", "versus", "verdict", "text", "end"}
for b in beats:
    if b["kind"] not in KINDS: sys.exit(f"BUILD FAILED: unknown beat kind {b['kind']!r}")
if beats[0]["kind"] != "hook" or beats[-1]["kind"] != "end": sys.exit("BUILD FAILED: first beat must be 'hook', last 'end'")
if not (5 <= len(beats) <= 9): sys.exit(f"BUILD FAILED: {len(beats)} beats, must be 5-9")
total = round(sum(b["duration"] for b in beats), 3)
if not (20.0 <= total <= 40.0): sys.exit(f"BUILD FAILED: total duration {total}s is outside 20-40s")

esc = lambda s: html.escape(str(s)).replace(" · ", " &nbsp;·&nbsp; ")
EXT = {"Anton": F("anton/files/anton-latin-ext-400-normal.woff2"), "Oswald": F("oswald/files/oswald-latin-ext-600-normal.woff2")}
EXT_RANGE = "U+0100-024F,U+0259,U+1E00-1EFF,U+2020,U+20A0-20AB,U+20AD-20CF,U+2113,U+2C60-2C7F,U+A720-A7FF"
FONT_CSS = ("".join(f'@font-face{{font-family:"{k}";src:url({v}) format("woff2")}}' for k, v in FONTS.items())
            + "".join(f'@font-face{{font-family:"{k}";src:url({v}) format("woff2");unicode-range:{EXT_RANGE}}}' for k, v in EXT.items()))
STRIPES = ("repeating-linear-gradient(90deg,#0A0E1C 0 90px,#0F1F4A 90px 180px)")
CSS = FONT_CSS + f"""
*{{box-sizing:border-box;margin:0}} body{{background:#000}}
#f{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:{NERO};color:#fff;font-family:Oswald}}
.bg{{position:absolute;left:0;top:0;width:1080px;height:1920px}}
.stripes{{position:absolute;inset:-200px -300px;background:{STRIPES};opacity:.55;transform:skewX(-14deg)}}
.glow{{position:absolute;left:-400px;top:-700px;width:1880px;height:1400px;background:radial-gradient(closest-side,rgba(74,123,224,.55),rgba(74,123,224,0) 70%)}}
.vignette{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,rgba(0,0,0,0) 45%,rgba(0,0,0,.72) 100%)}}
.grain{{position:absolute;inset:0;opacity:.10;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch' seed='7'/><feColorMatrix values='0 0 0 0 .6 0 0 0 0 .6 0 0 0 0 .7 0 0 0 .8 0'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>")}}
.col{{position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:220px 84px 340px;text-align:center}}
.mono{{font-family:"IBM Plex Mono",monospace;letter-spacing:.16em;text-transform:uppercase;white-space:nowrap}}
.tag{{display:inline-flex;align-items:center;gap:16px;font-size:26px;color:{GOLD};margin-bottom:54px}}
.tag .sq{{width:16px;height:16px;background:{GOLD};display:block}}
.tag .kt{{overflow:hidden;white-space:nowrap}}
.big{{font-family:Anton;font-size:172px;line-height:1.0;text-transform:uppercase;letter-spacing:.005em}}
.big.tight{{font-size:140px}} .big.xtight{{font-size:112px}}
.mask{{overflow:hidden;padding:0 .04em}} .mask>span{{display:inline-block;will-change:transform;white-space:nowrap}}
.wm{{font-family:Anton;font-size:44px;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;color:#fff}} .wm b{{color:{LBLUE};font-weight:400}}
.rows{{width:100%;text-align:left}}
.row{{display:flex;align-items:baseline;gap:34px;padding:26px 0;border-bottom:2px solid rgba(255,255,255,.14);position:relative;overflow:hidden}}
.row .n{{font-family:"IBM Plex Mono",monospace;font-size:30px;color:{GOLD};letter-spacing:.1em;width:70px;flex:none}}
.row .nm{{font-family:Oswald;font-size:78px;line-height:1;text-transform:uppercase;white-space:nowrap;flex:1;min-width:0}}
.row .era{{font-family:"IBM Plex Mono",monospace;font-size:28px;color:{MUTED};letter-spacing:.1em;white-space:nowrap}}
.num{{font-family:Anton;font-size:400px;line-height:.9;color:{GOLD};white-space:nowrap}}
.numlbl{{font-family:Oswald;font-size:56px;text-transform:uppercase;letter-spacing:.04em;color:#fff;line-height:1.1;margin-top:10px}}
.name{{font-family:Anton;font-size:128px;line-height:1;text-transform:uppercase;white-space:nowrap;margin-top:56px}}
.chips{{display:flex;flex-direction:column;gap:18px;margin-top:44px;align-items:center}}
.chip{{font-family:Oswald;font-size:38px;text-transform:uppercase;letter-spacing:.03em;padding:14px 30px;border:2px solid rgba(232,197,71,.7);color:#fff;white-space:nowrap}}
.src{{font-size:22px;color:{MUTED};margin-top:40px;letter-spacing:.12em}}
.half{{position:absolute;top:0;bottom:0;width:50%}} .half.l{{left:0;background:{NERO}}} .half.r{{right:0;background:{BLUE}}}
.vs{{position:absolute;left:50%;top:0;height:100%;width:6px;margin-left:-3px;background:{GOLD};transform-origin:top center}}
.vsb{{position:absolute;left:50%;top:470px;transform:translate(-50%,-50%);font-family:Anton;font-size:92px;color:{NERO};background:{GOLD};width:190px;height:190px;border-radius:50%;display:flex;align-items:center;justify-content:center;line-height:1}}
.side{{position:absolute;top:200px;width:50%;text-align:center;padding:0 40px}} .side.l{{left:0}} .side.r{{right:0}}
.side .nm{{font-family:Anton;font-size:96px;line-height:1;text-transform:uppercase;white-space:nowrap}}
.side .era{{font-family:"IBM Plex Mono",monospace;font-size:24px;letter-spacing:.14em;margin-top:18px;color:rgba(255,255,255,.75)}}
.stats{{position:absolute;left:0;right:0;top:640px;display:flex;flex-direction:column}}
.stat{{display:flex;align-items:center;justify-content:space-between;padding:26px 64px;position:relative}}
.stat .v{{font-family:Anton;font-size:118px;line-height:1;width:300px;white-space:nowrap}} .stat .v.r{{text-align:right}}
.stat .lbl{{font-family:"IBM Plex Mono",monospace;font-size:22px;letter-spacing:.14em;text-transform:uppercase;text-align:center;color:{GOLD};width:340px;white-space:normal;line-height:1.4}}
.stat .win{{position:absolute;bottom:14px;height:8px;background:{GOLD};transform-origin:left center;width:300px}}
.stat .win.l{{left:64px}} .stat .win.r{{right:64px;transform-origin:right center}}
.stamp{{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:40px;letter-spacing:.24em;text-transform:uppercase;color:{GOLD};border:8px solid {GOLD};padding:22px 46px;transform:rotate(-7deg);margin-bottom:70px;white-space:nowrap}}
.vname{{font-family:Anton;font-size:250px;line-height:.95;text-transform:uppercase;white-space:nowrap;color:#fff}}
.vsub{{font-family:Oswald;font-size:46px;text-transform:uppercase;letter-spacing:.03em;margin-top:56px;line-height:1.3;color:rgba(255,255,255,.9)}}
.vsub div{{white-space:nowrap}}
.sub{{font-family:Oswald;font-size:44px;text-transform:uppercase;letter-spacing:.03em;line-height:1.35;margin-top:48px;color:rgba(255,255,255,.88)}} .sub div{{white-space:nowrap}}
.cta{{font-family:Anton;font-size:104px;line-height:1;text-transform:uppercase;color:{GOLD};white-space:nowrap;margin-top:36px}}
.footer{{position:absolute;left:84px;right:84px;bottom:300px;display:flex;flex-direction:column;align-items:center;gap:14px}}
.footer .bar{{width:56px;height:4px;background:{GOLD};opacity:.8}} .footer .url{{font-size:25px;letter-spacing:.16em;color:{LBLUE}}}
.footer .dbt{{font-size:20px;letter-spacing:.2em;color:{MUTED}}}
.prog{{position:absolute;left:0;top:0;height:10px;background:{GOLD};transform-origin:left center}}
.wipe{{position:absolute;inset:0;display:grid;grid-template-columns:repeat(8,1fr)}} .wipe i{{display:block;background:{NAVY};transform-origin:top center}}
.wipe i:nth-child(even){{background:{BLUE}}}
"""

BG_PNG = os.path.join(wd, "_d_bg.png")
def render_bg():
    """Rasterize stripes + floodlight glow + vignette + grain ONCE; frames composite it as an image (live filters cost ~0.7 s/frame)."""
    hp = os.path.join(wd, "_d_bg.html")
    open(hp, "w").write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div id="f">'
                        '<div class="stripes"></div><div class="glow"></div><div class="vignette"></div><div class="grain"></div></div>'
                        '<script>document.fonts.ready.then(()=>{document.body.dataset.fitted="1"})</script></body></html>')
    js = r"""const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({executablePath:process.argv[3]});
const p=await b.newPage({viewport:{width:1080,height:1920}});await p.goto('file://'+process.argv[2]);await p.waitForFunction(()=>document.body.dataset.fitted==='1');
await p.locator('#f').screenshot({path:process.argv[4]});await b.close();})().catch(e=>{console.error(e);process.exit(2);});"""
    open(os.path.join(wd, "_d_bg.js"), "w").write(js)
    subprocess.run(["node", "_d_bg.js", hp, CHROME, BG_PNG], cwd=wd, check=True)

def mask(lines):
    return "".join(f'<div class="mask"><span data-line="{i}">{esc(l)}</span></div>' for i, l in enumerate(lines))
def sizecls(ls):
    m = max(map(len, ls)); return "big " + ("xtight" if m > 13 else "tight" if m > 10 else "")
def tag(text):
    return f'<div class="mono tag"><i class="sq"></i><span class="kt">{esc(text)}</span></div>' if text else ""
def wm(): return '<div class="wm">Nerazzurri <b>Daily</b></div>'

def build_html(idx, b):
    kind = b["kind"]; p = [f'<img class="bg" src="file://{BG_PNG}">']
    if kind == "hook":
        p.append(f'<div class="col">{tag(b.get("eyebrow", "THE DEBATE"))}<div class="{sizecls(b["lines"])}">{mask(b["lines"])}</div>'
                 f'<div class="mono" style="font-size:28px;color:{MUTED};margin-top:64px">{esc(b.get("sub", "pick one · fight in the comments"))}</div></div>')
    elif kind == "lineup":
        rows = "".join(f'<div class="row"><span class="n">{i+1:02d}</span><span class="nm"><span>{esc(r["name"])}</span></span><span class="era">{esc(r.get("era",""))}</span></div>'
                       for i, r in enumerate(b["rows"]))
        p.append(f'<div class="col" style="justify-content:flex-start;padding-top:230px">{tag(b.get("kicker", "THE CONTENDERS"))}<div class="rows">{rows}</div></div>')
    elif kind == "card":
        chips = "".join(f'<div class="chip">{esc(c)}</div>' for c in b.get("facts", []))
        src = f'<div class="mono src">{esc(b["source"])}</div>' if b.get("source") else ""
        p.append(f'<div class="col" style="padding-top:200px">{tag(b.get("kicker",""))}'
                 f'<div class="num"><span class="cnt" data-n="{b["number"]}">{b["number"]}</span>{esc(b.get("suffix",""))}</div>'
                 f'<div class="numlbl">{esc(b["label"])}</div><div class="name"><div class="mask"><span>{esc(b["name"])}</span></div></div>'
                 f'<div class="chips">{chips}</div>{src}</div>')
    elif kind == "versus":
        L, R = b["left"], b["right"]
        stats = ""
        for r in b["rows"]:
            win = r.get("win")
            stats += (f'<div class="stat"><span class="v l"><span class="cnt" data-n="{r["l"]}">{r["l"]}</span></span><span class="lbl">{esc(r["label"])}</span>'
                      f'<span class="v r"><span class="cnt" data-n="{r["r"]}">{r["r"]}</span></span>' + (f'<i class="win {win}"></i>' if win in ("l", "r") else "") + '</div>')
        p = [f'<img class="bg" src="file://{BG_PNG}">', '<div class="half r"></div><div class="vs"></div>',
             f'<div class="side l"><div class="nm"><div class="mask"><span data-side="l">{esc(L["name"])}</span></div></div><div class="mono era">{esc(L.get("era",""))}</div></div>',
             f'<div class="side r"><div class="nm"><div class="mask"><span data-side="r">{esc(R["name"])}</span></div></div><div class="mono era">{esc(R.get("era",""))}</div></div>',
             f'<div class="stats">{stats}</div><div class="vsb">VS</div>']
    elif kind == "verdict":
        p.append(f'<div class="col"><div class="stamp">{esc(b.get("stamp","OUR PICK"))}</div><div class="vname"><div class="mask"><span>{esc(b["name"])}</span></div></div>'
                 f'<div class="vsub">' + "".join(f'<div class="s">{esc(s)}</div>' for s in b.get("lines", [])) + '</div></div>')
    elif kind == "text":
        p.append(f'<div class="col">{tag(b.get("kicker",""))}<div class="{sizecls(b["lines"])}">{mask(b["lines"])}</div>'
                 f'<div class="sub">' + "".join(f'<div class="s">{esc(s)}</div>' for s in b.get("sub", [])) + '</div></div>')
    elif kind == "end":
        p.append(f'<div class="col" style="padding-bottom:300px">{wm()}<div class="{sizecls(b["lines"])}" style="margin-top:60px">{mask(b["lines"])}</div>'
                 f'<div class="mono" style="font-size:30px;color:#fff;margin-top:54px;letter-spacing:.2em">{esc(b.get("ask","REPLY IN THE COMMENTS"))}</div>'
                 f'<div class="mono fitw" style="font-size:24px;color:{MUTED};margin-top:64px">{esc(b.get("sub","the inter press · in english · every morning"))}</div>'
                 f'<div class="cta">{SITE}</div></div>')
    if kind != "end":
        fc = ' style="color:#fff"' if kind == "versus" else ""
        p.append(f'<div class="footer"><div class="bar"></div><div class="mono url"{fc}>{SITE}</div><div class="mono dbt"{fc}>the debate · fan-made</div></div>')
    p.append('<div class="prog"></div>')
    if idx: p.append('<div class="wipe">' + "<i></i>" * 8 + '</div>')
    js = r"""
<script>
const D=%DUR%, T0=%T0%, TOTAL=%TOTAL%;
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const oExpo=x=>x>=1?1:1-Math.pow(2,-10*x), oCubic=x=>1-Math.pow(1-x,3), ioCubic=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
const seg=(t,s,d)=>clamp((t-s)/d); const $=s=>Array.from(document.querySelectorAll(s));
function fit(){
  $('.big,.name,.vname,.cta,.wm,.tag,.stamp,.side .nm,.row .nm,.numlbl,.chip,.vsub div,.sub div,.num,.fitw').forEach(el=>{
    const box=el.closest('.side')||el.closest('.row')||el.closest('.col')||document.getElementById('f');
    const cs=getComputedStyle(box); let avail=box.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
    if(el.closest('.row')){avail-=290;}
    const inner=Array.from(el.querySelectorAll('span')); const widest=()=>inner.length?Math.max(...inner.map(k=>k.scrollWidth)):el.scrollWidth;
    let size=parseFloat(getComputedStyle(el).fontSize), g=0;
    while(widest()>avail && size>20 && g<400){size-=2; el.style.fontSize=size+'px'; g++;}
  });
}
window.seek=function(t){
  $('.prog').forEach(e=>{e.style.width=(100*clamp((T0+t)/TOTAL))+'%';});
  $('.wipe i').forEach((e,i)=>{const p=oCubic(seg(t,i*.04,.36)); e.style.transform=`scaleY(${1-p})`; e.style.display=p>=1?'none':'block';});
  $('.tag').forEach(k=>{const sq=k.querySelector('.sq'), kt=k.querySelector('.kt'); if(sq) sq.style.transform=`rotate(${45*(1-oCubic(seg(t,.2,.4)))}deg) scale(${oCubic(seg(t,.2,.3))})`;
    if(kt){const w=kt.dataset.w||(kt.dataset.w=kt.scrollWidth); kt.style.width=(w*oExpo(seg(t,.3,.7)))+'px';}});
  $('.mask>span').forEach((s,i)=>{const p=oExpo(seg(t,.4+i*.13,.7)); s.style.transform=`translateY(${(1-p)*115}%)`;});
  $('.mask>span[data-side]').forEach(s=>{const p=oExpo(seg(t,.4,.7)); s.style.transform=`translateX(${(1-p)*(s.dataset.side==='l'?-70:70)}%)`; s.style.opacity=p;});
  $('.row').forEach((r,i)=>{const p=oExpo(seg(t,.55+i*.16,.6)); r.style.opacity=p; r.style.transform=`translateX(${(1-p)*120}px)`;});
  $('.cnt').forEach(n=>{const target=parseFloat(n.dataset.n); if(isNaN(target))return; const p=oCubic(seg(t,.5,1.2)); n.textContent=String(Math.round(target*p));});
  $('.num').forEach(s=>{const p=seg(t,.4,.8); s.style.transform=`scale(${.7+.3*oExpo(p)})`; s.style.opacity=oCubic(seg(t,.4,.4));});
  $('.numlbl').forEach(s=>{const p=oCubic(seg(t,1.0,.5)); s.style.opacity=p; s.style.transform=`translateY(${(1-p)*20}px)`;});
  $('.chip').forEach((c,i)=>{const p=oExpo(seg(t,1.6+i*.25,.5)); c.style.opacity=p; c.style.transform=`translateY(${(1-p)*30}px) scale(${.9+.1*p})`;});
  $('.src').forEach(s=>{s.style.opacity=oCubic(seg(t,2.3,.5));});
  $('.vs').forEach(v=>{v.style.transform=`scaleY(${oExpo(seg(t,.2,.8))})`;});
  $('.vsb').forEach(v=>{const p=oExpo(seg(t,.8,.5)); v.style.transform=`translate(-50%,-50%) scale(${p}) rotate(${(1-p)*-90}deg)`;});
  $('.side .era').forEach(e=>{e.style.opacity=oCubic(seg(t,1.0,.5));});
  $('.stat').forEach((s,i)=>{const p=oExpo(seg(t,1.0+i*.3,.6)); s.style.opacity=p; s.style.transform=`translateY(${(1-p)*40}px)`;
    const w=s.querySelector('.win'); if(w) w.style.transform=`scaleX(${oExpo(seg(t,1.9+i*.3,.5))})`;});
  $('.stamp').forEach(s=>{const p=oExpo(seg(t,.25,.5)); s.style.opacity=p; s.style.transform=`rotate(-7deg) scale(${1.8-.8*p})`;});
  $('.vsub .s, .sub .s').forEach((s,i)=>{const p=oCubic(seg(t,1.2+i*.18,.5)); s.style.opacity=p; s.style.transform=`translateY(${(1-p)*24}px)`;});
  $('.wm').forEach(w=>{const p=oExpo(seg(t,.2,.7)); w.style.opacity=p; w.style.transform=`translateY(${(1-p)*-30}px)`;});
  $('.footer').forEach(f=>{f.style.opacity=oCubic(seg(t,1.0,.6));});
  $('.cta').forEach(c=>{const p=oExpo(seg(t,1.1,.8)); const pulse=1+.025*Math.sin(Math.max(0,t-1.9)*4.2); c.style.opacity=p; c.style.transform=`scale(${(.85+.15*p)*pulse})`;});
  document.body.dataset.t=t;
};
document.fonts.ready.then(()=>{fit(); window.seek(0); document.body.dataset.fitted='1';});
</script>"""
    js = js.replace("%DUR%", str(b["duration"])).replace("%T0%", str(b["_t0"])).replace("%TOTAL%", str(total))
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div id="f">{"".join(p)}</div>{js}</body></html>'

# ---- thumbnails: 9:16 (TikTok cover / Shorts) and 16:9 (YouTube) — the VS split -----------------------------
def thumb_html(T, W_, H_):
    land = W_ > H_; L, R = T["left"], T["right"]
    q = "".join(f'<div class="q fit">{esc(l)}</div>' for l in T["lines"])
    if land:
        body = (f'<div class="half l" style="width:50%"><div class="stripes"></div></div><div class="half r" style="width:50%"></div>'
                f'<div class="nm fit" style="position:absolute;left:40px;top:70px;width:520px;font-size:120px">{esc(L["name"])}</div>'
                f'<div class="mono" style="position:absolute;left:40px;top:210px;font-size:22px;color:{MUTED}">{esc(L.get("era",""))}</div>'
                f'<div class="nm fit" style="position:absolute;right:40px;top:70px;width:520px;text-align:right;font-size:120px">{esc(R["name"])}</div>'
                f'<div class="mono" style="position:absolute;right:40px;top:210px;font-size:22px;color:rgba(255,255,255,.8)">{esc(R.get("era",""))}</div>'
                f'<div class="vsb" style="top:50%;width:150px;height:150px;font-size:72px">VS</div>'
                f'<div style="position:absolute;left:0;right:0;bottom:60px;text-align:center;font-size:118px">{q}</div>'
                f'<div class="mono" style="position:absolute;left:40px;bottom:30px;font-size:20px;color:{GOLD}">THE DEBATE · NERAZZURRI DAILY</div>')
    else:
        body = (f'<div class="half l" style="width:100%;height:50%;top:0;bottom:auto"><div class="stripes"></div></div><div class="half r" style="width:100%;height:50%;top:50%"></div>'
                f'<div class="nm fit" style="position:absolute;left:70px;top:330px;width:940px;font-size:230px">{esc(L["name"])}</div>'
                f'<div class="mono" style="position:absolute;left:70px;top:590px;font-size:30px;color:{MUTED}">{esc(L.get("era",""))}</div>'
                f'<div class="nm fit" style="position:absolute;left:70px;top:1130px;width:940px;font-size:230px">{esc(R["name"])}</div>'
                f'<div class="mono" style="position:absolute;left:70px;top:1390px;font-size:30px;color:rgba(255,255,255,.8)">{esc(R.get("era",""))}</div>'
                f'<div class="vsb" style="top:50%;width:230px;height:230px;font-size:110px">VS</div>'
                f'<div style="position:absolute;left:70px;top:110px;width:940px;font-size:96px">{q}</div>'
                f'<div class="mono" style="position:absolute;left:70px;bottom:120px;font-size:26px;color:{GOLD}">THE DEBATE · NERAZZURRI DAILY</div>'
                '')
    css = CSS + f".nm{{font-family:Anton;text-transform:uppercase;line-height:.95;white-space:nowrap;color:#fff}} .q{{font-family:Anton;text-transform:uppercase;line-height:1;color:{GOLD};white-space:nowrap;display:inline-block}}"
    fit = """<script>document.fonts.ready.then(()=>{const F=document.getElementById('f');
document.querySelectorAll('.fit').forEach(el=>{const avail=el.style.width?parseFloat(el.style.width):(el.parentElement.style.width?parseFloat(el.parentElement.style.width):F.clientWidth-140);
let s=parseFloat(getComputedStyle(el).fontSize),g=0;while(el.scrollWidth>avail&&s>30&&g<300){s-=2;el.style.fontSize=s+'px';g++;}});
const bad=[];document.querySelectorAll('#f div').forEach(el=>{if(!el.innerText||!el.innerText.trim()||el.querySelector('div'))return;const r=el.getBoundingClientRect();
if(r.left<20||r.right>F.clientWidth-20||r.top<0||r.bottom>F.clientHeight-10)bad.push(el.innerText.slice(0,40)+' @'+Math.round(r.right)+','+Math.round(r.bottom));});
document.body.dataset.bad=JSON.stringify(bad);document.body.dataset.fitted='1';});</script>"""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>'
            f'<div id="f" style="width:{W_}px;height:{H_}px">{body}<div class="vignette"></div><div class="grain"></div></div>{fit}</body></html>')

def render_thumbnails(name):
    T = spec.get("thumbnail")
    if not T: return []
    jobs = []
    for tg, (w_, h_) in {"9x16": (1080, 1920), "16x9": (1280, 720)}.items():
        hp = os.path.join(wd, f"_dt_{tg}.html"); open(hp, "w").write(thumb_html(T, w_, h_))
        jobs.append({"html": hp, "png": os.path.join(out, f"{name}-thumb-{tg}.png"), "w": w_, "h": h_})
    js = r"""const {chromium}=require('playwright');const fs=require('fs');const jobs=JSON.parse(fs.readFileSync(process.argv[2]));
(async()=>{const b=await chromium.launch({executablePath:process.argv[3]});const rep=[];
for(const j of jobs){const p=await b.newPage({viewport:{width:j.w,height:j.h}});await p.goto('file://'+j.html);
await p.waitForFunction(()=>document.body.dataset.fitted==='1');await p.waitForTimeout(250);
rep.push({png:j.png,bad:JSON.parse(await p.evaluate(()=>document.body.dataset.bad))});await p.locator('#f').screenshot({path:j.png});await p.close();}
await b.close();fs.writeFileSync(process.argv[4],JSON.stringify(rep));})().catch(e=>{console.error(e);process.exit(2);});"""
    open(os.path.join(wd, "_dt.js"), "w").write(js); jp = os.path.join(wd, "_dt_jobs.json"); open(jp, "w").write(json.dumps(jobs))
    rp = os.path.join(wd, "_dt_report.json"); subprocess.run(["node", "_dt.js", jp, CHROME, rp], cwd=wd, check=True)
    bad = [r for r in json.load(open(rp)) if r["bad"]]
    if bad:
        print("BUILD FAILED — thumbnail layout problems:"); [print("  ", os.path.basename(r["png"]), r["bad"]) for r in bad]; sys.exit(1)
    return [j["png"] for j in jobs]

render_bg()
NAME = A.name or f"ND-DEBATE-{spec.get('date_iso','video')}-{spec.get('slug','debate')}"
if A.thumb_only:
    for p_ in render_thumbnails(NAME): print("OK", p_)
    sys.exit(0)

t0 = 0.0
for b in beats: b["_t0"] = round(t0, 3); t0 += b["duration"]
jobs = []
for i, b in enumerate(beats):
    hp = os.path.join(wd, f"_d_{b['id']}.html"); open(hp, "w").write(build_html(i, b))
    nf = int(round(b["duration"] * A.fps)); jobs.append({"id": b["id"], "html": hp, "dur": b["duration"], "frames": nf, "first": sum(j["frames"] for j in jobs)})

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
    await p.evaluate(t => window.seek(t), j.dur - 0.05);
    const issues = await p.evaluate((safeBottom) => {
      const out = []; const GUTTER = 30;
      document.querySelectorAll('#f div, #f span').forEach((el) => {
        if (el.closest('.wipe') || el.classList.contains('prog') || el.classList.contains('mask') || el.closest('.vsb')) return;
        if (el.children.length && el.querySelector('div,span')) return;
        if (!el.innerText || !el.innerText.trim()) return;
        const r = el.getBoundingClientRect(); const t = el.innerText.replace(/\n/g, ' / ').slice(0, 60);
        if (r.width === 0 || r.height === 0) return;
        if (r.left < GUTTER) out.push('CLIPPED LEFT (' + Math.round(r.left) + 'px) :: ' + t);
        if (r.right > 1080 - GUTTER) out.push('CLIPPED RIGHT (' + Math.round(r.right) + 'px) :: ' + t);
        if (r.top < 0) out.push('ABOVE FRAME :: ' + t);
        if (r.bottom > safeBottom) out.push('BELOW SAFE LINE (' + Math.round(r.bottom) + 'px) :: ' + t);
      });
      const foot = document.querySelector('.footer');
      if (foot) { const fTop = foot.getBoundingClientRect().top;
        document.querySelectorAll('#f div').forEach((el) => {
          if (el.closest('.footer') || el.classList.contains('prog') || el.closest('.wipe')) return;
          if (el.querySelector('div')) return; if (!el.innerText || !el.innerText.trim()) return;
          const r = el.getBoundingClientRect(); if (r.height && r.bottom > fTop - 20) out.push('CONTENT COLLIDES WITH URL LOCKUP :: ' + el.innerText.replace(/\n/g,' / ').slice(0,60)); }); }
      document.querySelectorAll('.tag').forEach((el) => { if (el.getBoundingClientRect().height > parseFloat(getComputedStyle(el).fontSize) * 1.8) out.push('KICKER WRAPPED :: ' + el.innerText.slice(0,60)); });
      document.querySelectorAll('.mask>span').forEach((el) => { const m = el.parentElement.getBoundingClientRect(), r = el.getBoundingClientRect();
        if (r.width > m.width + 2) out.push('LINE WIDER THAN ITS MASK :: ' + el.innerText.slice(0,60)); });
      return out;
    }, SAFE);
    report.push({ id: j.id, issues }); if (issues.length) continue;
    for (let k = 0; k < j.frames; k++) {
      await p.evaluate(t => window.seek(t), k / FPS);
      await p.screenshot({ path: `${framesDir}/${String(j.first + k).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92, clip: { x: 0, y: 0, width: 1080, height: 1920 } });
    }
    fs.copyFileSync(`${framesDir}/${String(j.first + j.frames - 1).padStart(5,'0')}.jpg`, `${framesDir}/_settled_${j.id}.jpg`);
  }
  await b.close(); fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
})().catch(e => { console.error(e); process.exit(2); });
"""
open(os.path.join(wd, "_d_jobs.json"), "w").write(json.dumps(jobs)); open(os.path.join(wd, "_d_shot.js"), "w").write(shot_js)
rep = os.path.join(wd, "_d_report.json")
subprocess.run(["node", "_d_shot.js", os.path.join(wd, "_d_jobs.json"), frames, rep, str(A.fps), CHROME, str(SAFE_BOTTOM)], cwd=wd, check=True)
bad = [r for r in json.load(open(rep)) if r["issues"]]
if bad:
    print("BUILD FAILED — layout problems:")
    for r in bad:
        for i in r["issues"]: print(f"  {r['id']}: {i}")
    sys.exit(1)
stills = os.path.join(out, "stills"); shutil.rmtree(stills, ignore_errors=True); os.makedirs(stills)
for f in glob.glob(os.path.join(frames, "_settled_*.jpg")): shutil.move(f, os.path.join(stills, os.path.basename(f)[9:]))

mp4 = os.path.join(out, NAME + ".mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(A.fps), "-i", os.path.join(frames, "%05d.jpg"), "-vf", "format=yuv420p",
                "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-movflags", "+faststart", "-r", str(A.fps), mp4], check=True)
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", mp4],
                                 capture_output=True, text=True).stdout)
dur = float(info["format"]["duration"])
if abs(dur - total) > 0.6: sys.exit(f"BUILD FAILED: MP4 is {dur:.2f}s, beats sum to {total}s")
if not A.keep_frames: shutil.rmtree(frames, ignore_errors=True)
thumbs = render_thumbnails(NAME)
json.dump({"mp4": mp4, "seconds": round(dur, 2), "beats": len(beats), "audio": False, "format": "debate", "streams": info["streams"],
           "stills": stills, "thumbnails": thumbs}, open(os.path.join(out, "manifest.json"), "w"), indent=2)
print(f"OK {mp4} — {dur:.2f}s, {len(beats)} beats, silent (voice is mixed on by nd_voice.py); stills in {stills}; thumbnails: {', '.join(os.path.basename(t) for t in thumbs)}")

