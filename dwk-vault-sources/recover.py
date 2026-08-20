#!/usr/bin/env python3
"""
The Vault — recover.

    python3 recover.py [https://dosenft.github.io/dwk-vault/ | path/to/index.html]

The published page is one file, and this is the proof that it can always be
taken apart again into the five it was built from. Run it after a workspace is
wiped: it downloads the live vault, splits the four data blocks back out into
vault/, puts the injection markers back into build/app.html, and leaves the
tree exactly as `build.py` expects to find it.

This exists because a working container was reclaimed mid-build three times,
and each time the sources had to be reconstructed by hand.
"""
import sys, re, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SRC = sys.argv[1] if len(sys.argv) > 1 else "https://dosenft.github.io/dwk-vault/index.html"

if SRC.startswith(("http://", "https://")):
    if SRC.endswith("/"):
        SRC += "index.html"
    html = urllib.request.urlopen(SRC, timeout=60).read().decode()
else:
    html = pathlib.Path(SRC).read_text()

print(f"  read {len(html)/1024:.0f} KB from {SRC}")

BLOCKS = [("vault-data", "vault/vault-data.js", "/*__DATA__*/"),
          ("vault-audio", "vault/audio.js", "/*__AUDIO__*/"),
          ("vault-sync", "vault/sync.js", "/*__SYNC__*/"),
          ("vault-art", "vault/art.js", "/*__ART__*/")]

(ROOT / "vault").mkdir(exist_ok=True)
(ROOT / "build").mkdir(exist_ok=True)

for sid, out, marker in BLOCKS:
    m = re.search(rf'(<script id="{sid}">\n)(.*?)(\n</script>)', html, re.S)
    if not m:
        sys.exit(f"  the page has no <script id=\"{sid}\"> — it is not a vault build.")
    body = m.group(2)
    if sid == "vault-data":
        # the build stamps the version on the end of the campaign data
        body = re.sub(r"\nconst BUILD='[^']*';\s*$", "", body)
    (ROOT / out).write_text(body + "\n")
    html = html[:m.start(2)] + marker + html[m.end(2):]
    print(f"  {out:<24} {len(body)/1024:>7.1f} KB")

(ROOT / "build" / "app.html").write_text(html)
print(f"  build/app.html           {len(html)/1024:>7.1f} KB   markers restored")
print("\n  Now run:  python3 build.py\n")
