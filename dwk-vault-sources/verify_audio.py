#!/usr/bin/env python3
"""Do the recordings play, in a real browser, from the real host?"""
import sys, urllib.request, pathlib, re
from playwright.sync_api import sync_playwright
FAILS, PASSES = [], []
def check(c, m): (PASSES if c else FAILS).append(m)
TARGET_PATH = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "dist/index.html")
TARGET = TARGET_PATH.resolve().as_uri()
AUDIO_OK = ("audio/mpeg", "audio/mp3", "audio/mp4", "audio/aac")
src = TARGET_PATH.read_text()
base = re.search(r'const AU\s*=\s*"([^"]+)"', src)
check(bool(base), "the build declares where the recordings live")
SMALL = (base.group(1) if base else "") + "s12-ponzis-oath.mp3"
print(f"fetching {SMALL.rsplit('/',1)[-1]} …")
with urllib.request.urlopen(SMALL, timeout=300) as r:
    DATA, CT, CD, AR = r.read(), r.headers.get('content-type',''), \
                       r.headers.get('content-disposition',''), r.headers.get('accept-ranges','')
print(f"  {len(DATA)/1048576:.1f} MB · {CT} · ranges={AR!r} · disposition={CD!r}")
check(DATA[:3] == b'ID3' or DATA[:2] == b'\xff\xfb', f"the file starts as audio ({DATA[:3]!r})")
check(CT.split(';')[0] in AUDIO_OK, f"the host labels it as audio ({CT!r}) — iOS refuses anything else")
check(not CD, f"and does not attach a download header ({CD!r})")
check(AR == 'bytes', f"and serves byte ranges ({AR!r})")
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route("**/audio/*.mp3", lambda route: route.fulfill(status=200, body=DATA,
        headers={'content-type': CT or 'audio/mpeg', 'accept-ranges': 'bytes',
                 'content-length': str(len(DATA))}))
    pg.goto(TARGET); pg.wait_for_timeout(2500)
    check(not errs, f"no JS errors ({errs[:2]})")
    idx = pg.evaluate("SESSIONS.findIndex(s=>/ponzis-oath/.test(s.slug))")
    check(idx >= 0, "the vault knows that session")
    res = pg.evaluate("""async(i)=>{
      const done=new Promise(r=>{ const log=[];
        ['loadedmetadata','canplay','playing','error'].forEach(e=>
          au.addEventListener(e,()=>{ log.push(e);
            if(e==='playing') r({ok:true,log,dur:au.duration});
            if(e==='error')   r({ok:false,log,code:au.error&&au.error.code}); },{once:true}));
        setTimeout(()=>r({ok:false,log,timeout:true}),25000); });
      listen(i,0); return done; }""", idx)
    check(res.get('ok'), f"pressing play produces sound ({res})")
    check(res.get('dur', 0) > 60, f"and the whole recording is there ({round(res.get('dur',0))}s)")
    check(pg.is_visible('#reel'), "and play takes you into the Reel")
    pg.wait_for_timeout(600)
    check(pg.eval_on_selector('#pb', 'e=>e.textContent.trim()') == '❚❚', "the button reports the true state")
    check(pg.eval_on_selector('body', 'e=>!e.classList.contains("waiting")'), "the loading ring stopped")
    ok = pg.evaluate("""async()=>{ const p=new Promise(r=>au.addEventListener('seeked',()=>r(true),{once:true}));
      jump(SESSIONS.findIndex(s=>/ponzis-oath/.test(s.slug)),600);
      await Promise.race([p,new Promise(r=>setTimeout(()=>r(false),12000))]);
      return Math.abs(au.currentTime-600)<4; }""")
    check(ok, "clicking a timecode lands on that second")
    pg.unroute("**/audio/*.mp3")
    pg.route("**/audio/*.mp3", lambda route: route.fulfill(status=404, body=b''))
    pg.evaluate("au.pause(); au.load();"); pg.wait_for_timeout(2500)
    sub = pg.inner_text('#p-sub')
    check(len(sub) > 8 and 'Playing' not in sub, f"a failure says something out loud ({sub[:60]!r})")
    b.close()
print(f"\n  PASS {len(PASSES)}   FAIL {len(FAILS)}\n")
for m in FAILS: print("  FAIL  " + m)
if not FAILS: print("  The recordings play.\n")
sys.exit(1 if FAILS else 0)
