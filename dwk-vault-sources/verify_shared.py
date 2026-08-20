#!/usr/bin/env python3
"""Two people, two devices, one vault. Writes only to a throwaway name —
the shared vault holds live campaign data and a test must never scribble on it."""
import subprocess, sys, time, signal, urllib.request, urllib.error, pathlib
from playwright.sync_api import sync_playwright
PORT, FAILS, PASSES = 8901, [], []
URL = f"http://localhost:{PORT}/"
SCRATCH = "__selftest__"
def check(c, m): (PASSES if c else FAILS).append(m)
def relay(route):
    req = route.request
    r = urllib.request.Request(req.url, data=req.post_data_buffer, method=req.method)
    for k, v in req.headers.items():
        if k.lower() in ('apikey','authorization','content-type','prefer','accept'):
            r.add_header(k, v)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            route.fulfill(status=resp.status, body=resp.read(),
                headers={'content-type': resp.headers.get('content-type','application/json'),
                         'access-control-allow-origin':'*'})
    except urllib.error.HTTPError as e:
        route.fulfill(status=e.code, body=e.read(),
            headers={'content-type':'application/json','access-control-allow-origin':'*'})
    except Exception:
        route.abort()
def wire(page): page.route("**/*.supabase.co/**", relay)
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=root,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        A = b.new_context(); a = A.new_page(); wire(a)
        errs = []; a.on('pageerror', lambda e: errs.append(str(e)))
        a.add_init_script("window.localStorage.setItem('dwk-who','test-A')")
        a.goto(URL); a.wait_for_timeout(3000)
        check(not errs, f"A: no JS errors ({errs[:2]})")
        check(a.evaluate("SYNC.on"), "A: the shared layer is switched on")
        a.wait_for_function("SYNC.state==='live'", timeout=20000)
        check(a.evaluate("SYNC.state") == 'live', "A: reached the shared vault")
        stamp = f"selftest-{int(time.time())}"
        a.evaluate(f"pushEdit('pc_meta',{{name:'{SCRATCH}',field:'sub',value:'{stamp}'}})")
        a.wait_for_function("SYNC.queue.length===0", timeout=25000)
        check(a.evaluate("SYNC.queue.length") == 0, "A: the edit was accepted by the shared vault")
        check(a.evaluate(f"metaOf('{SCRATCH}').sub") == stamp, "A: and lands locally at once")
        B = b.new_context(); bb = B.new_page(); wire(bb)
        berrs = []; bb.on('pageerror', lambda e: berrs.append(str(e)))
        bb.add_init_script("window.localStorage.setItem('dwk-who','test-B')")
        bb.goto(URL); bb.wait_for_timeout(1000)
        bb.wait_for_function("SYNC.state==='live'", timeout=20000); bb.wait_for_timeout(1500)
        check(not berrs, f"B: no JS errors ({berrs[:2]})")
        got = bb.evaluate(f"metaOf('{SCRATCH}').sub")
        check(got == stamp, f"B: a second device sees A's edit with no file passing ({got!r})")
        bb.evaluate("openE('Nyx')"); bb.wait_for_timeout(700)
        check(bb.is_visible('#v-entity'), "B: character pages still render after a replay")
        check(bb.eval_on_selector_all('#e-body .arcrow', 'e=>e.length') > 3,
              "B: and the arc survived the replay intact")
        d = bb.evaluate("""async()=>{
          const h={apikey:SUPA.key,Authorization:'Bearer '+SUPA.key};
          const r=await fetch(SUPA.url+'/rest/v1/vault_edits?id=gt.0',{method:'DELETE',headers:h});
          const after=await (await fetch(SUPA.url+'/rest/v1/vault_edits?select=id',{headers:h})).json();
          return {status:r.status, rows:after.length};}""")
        check(d['rows'] > 0, f"the page cannot delete campaign history ({d})")
        M = b.new_context(viewport={'width':390,'height':844}, is_mobile=True)
        m = M.new_page(); wire(m)
        m.goto(URL); m.wait_for_timeout(3000)
        m.evaluate("openE('Nyx')"); m.wait_for_timeout(900)
        check(not m.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1"),
              "MOBILE: a character page does not scroll sideways")
        b.close()
finally:
    srv.send_signal(signal.SIGTERM)
print(f"\n  PASS {len(PASSES)}   FAIL {len(FAILS)}\n")
for m in FAILS: print("  FAIL  " + m)
if not FAILS: print("  Two devices, one vault. It holds.\n")
sys.exit(1 if FAILS else 0)
