#!/usr/bin/env python3
"""
The Vault — build.

    python3 build.py            ->  dist/index.html

Four small files get poured into the four holes in build/app.html:

    build/app.html      the whole app: markup, style, behaviour
    vault/vault-data.js the campaign itself, straight out of the recordings
    vault/audio.js      which recording belongs to which night
    vault/sync.js       where the shared vault lives
    vault/art.js        the atmosphere plates

Nothing here is clever on purpose. The point is that the published page is
one file, and that one file can always be taken apart again into these five.
"""
import pathlib, subprocess, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parent
def rd(p): return (ROOT / p).read_text()

def rev():
    try:
        return subprocess.run(['git','rev-parse','--short','HEAD'], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip() or 'nogit'
    except Exception:
        return 'nogit'

BUILD = f"{datetime.date.today():%Y-%m-%d}-{rev()}"

html = rd('build/app.html')
parts = {
    '/*__DATA__*/':  rd('vault/vault-data.js').rstrip() + f"\nconst BUILD='{BUILD}';",
    '/*__AUDIO__*/': rd('vault/audio.js').rstrip(),
    '/*__SYNC__*/':  rd('vault/sync.js').rstrip(),
    '/*__ART__*/':   rd('vault/art.js').rstrip(),
}
for marker, body in parts.items():
    if marker not in html:
        sys.exit(f"build/app.html is missing {marker} — refusing to ship a half-built page.")
    html = html.replace(marker, body)

out = ROOT / 'dist' / 'index.html'
out.parent.mkdir(exist_ok=True)
out.write_text(html)
print(f"  {out.relative_to(ROOT)}   {len(html)/1024:.0f} KB   build {BUILD}")
