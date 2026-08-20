#!/usr/bin/env python3
"""Are the five recordings served in a way every device at the table accepts?"""
import sys, urllib.request
FILES=["s10-vattenheim","s11-festival-planning","s12-ponzis-oath","s13-city-festival","s14-caremall"]
SESSION={"s10-vattenheim":12,"s11-festival-planning":13,"s12-ponzis-oath":14,
         "s13-city-festival":15,"s14-caremall":16}
BASE=sys.argv[1] if len(sys.argv)>1 else "https://dosenft.github.io/dwk-vault/audio/"
AUDIO=("audio/mpeg","audio/mp3","audio/mp4","audio/aac")
bad=[]; print()
for f in FILES:
    u=BASE+f+".mp3"; line=f"Session {SESSION[f]:>2}  {f:<24}"
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={"Range":"bytes=1000000-1000100"}),timeout=90)
        code,ct,ar=r.status,(r.headers.get("content-type") or "").split(";")[0],r.headers.get("accept-ranges","")
        cd=r.headers.get("content-disposition",""); got=len(r.read()); r.close()
        h=urllib.request.urlopen(urllib.request.Request(u,method="HEAD"),timeout=90)
        size=int(h.headers.get("content-length",0)); h.close()
        ok_t=ct in AUDIO; ok_r=(code==206 and got==101); ok_d=not cd
        ok=ok_t and ok_r and ok_d and size>1_000_000
        print(f"{line} {'OK ' if ok else 'BAD'}  {size/1048576:6.1f} MB  {ct:<12} "
              f"{'ranges' if ok_r else 'NO RANGES'}  {'no attachment' if ok_d else 'ATTACHMENT'}")
        if not ok_t: bad.append(f"{f}: {ct!r} — iOS refuses this")
        if not ok_r: bad.append(f"{f}: no byte ranges")
        if not ok_d: bad.append(f"{f}: sends a download header")
    except Exception as e:
        print(f"{line} BAD  {e}"); bad.append(f"{f}: {e}")
print()
print("  NOT READY:" if bad else "  All five are served correctly. Every device at the table can play them.")
for b in bad: print("   · "+b)
print(); sys.exit(1 if bad else 0)
