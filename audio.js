#!/usr/bin/env python3
"""Installed to a home screen, does this behave like an app?"""
import subprocess, sys, time, json, signal, urllib.request, pathlib
from playwright.sync_api import sync_playwright
import socket
def freeport():
    """A leftover server from an interrupted run once held 8907 and every
       later run hung waiting on it. Take whatever port is actually free."""
    s = socket.socket(); s.bind(('127.0.0.1', 0)); n = s.getsockname()[1]; s.close(); return n
PORT, FAILS, PASSES = freeport(), [], []
URL = f"http://localhost:{PORT}/"
def check(c, m): (PASSES if c else FAILS).append(m)
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=root,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
try:
    man = json.load(urllib.request.urlopen(URL + "manifest.webmanifest", timeout=20))
    check(man.get('display') == 'standalone', "the manifest asks for a standalone window")
    check(bool(man.get('start_url')) and bool(man.get('scope')), "it has a start url and a scope")
    sizes = {i['sizes'] for i in man['icons']}
    check('192x192' in sizes and '512x512' in sizes, f"both required icon sizes are declared ({sizes})")
    check(any(i.get('purpose') == 'maskable' for i in man['icons']), "a maskable icon for Android")
    for i in man['icons']:
        check(urllib.request.urlopen(URL + i['src'], timeout=20).status == 200, f"icon {i['src']} is actually there")
    check(urllib.request.urlopen(URL + "apple-touch-icon.png", timeout=20).status == 200, "the iOS icon is there")
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(); pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL); pg.wait_for_timeout(2500)
        check(not errs, f"no JS errors ({errs[:2]})")
        check(pg.evaluate("navigator.serviceWorker.ready.then(()=>true).catch(()=>false)"),
              "the offline shell registers")
        pg.wait_for_timeout(1500); ctx.set_offline(True)
        pg.reload(); pg.wait_for_timeout(2500)
        n = pg.evaluate("typeof SESSIONS!=='undefined' ? SESSIONS.length : 0")
        check('Vault' in pg.title() and n > 10, f"with the network pulled, the vault still opens ({n} sessions)")
        check(pg.is_visible('#h-list'), "and the record is still there to read")
        ctx.set_offline(False); pg.reload(); pg.wait_for_timeout(2000)
        check(pg.evaluate("'mediaSession' in navigator"), "this browser exposes media controls")
        missing = pg.evaluate("""()=>{const want=['play','pause','seekbackward','seekforward',
            'previoustrack','nexttrack']; const bad=[];
            for(const k of want){ try{ navigator.mediaSession.setActionHandler(k,()=>{});}catch(e){bad.push(k);} }
            return bad;}""")
        check(not missing, f"every lock-screen control is a supported action ({missing})")
        check(pg.evaluate("typeof stepMoment==='function'"), "skip is wired to moments, not to files")
        pg.evaluate("openS(0); mediaMeta();"); pg.wait_for_timeout(600)
        meta = pg.evaluate("""()=>{const m=navigator.mediaSession.metadata;
            return m?{title:m.title,artist:m.artist,art:(m.artwork[0]||{}).src||''}:null;}""")
        check(bool(meta and meta['title']), f"the lock screen gets a real title ({meta})")
        check(bool(meta and 'Session' in (meta['artist'] or '')), "and says which session it is")
        check(bool(meta and meta['art'].endswith('.png')), "and carries artwork")
        check(pg.evaluate("LOCALFILE") is False, "served over http, the saved-copy warning stays hidden")
        b.close()
finally:
    srv.send_signal(signal.SIGTERM)
print(f"\n  PASS {len(PASSES)}   FAIL {len(FAILS)}\n")
for m in FAILS: print("  FAIL  " + m)
if not FAILS: print("  It behaves like an app.\n")
sys.exit(1 if FAILS else 0)
