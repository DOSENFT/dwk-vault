#!/usr/bin/env python3
"""
The Vault — the character builder.

Walks the exact path a new player takes on their own phone: an open seat,
a name, a picture, three things carried, one line kept private. Then opens
the same page as somebody else and checks the private line is not there.

    python3 test/verify_builder.py [path/to/index.html]
"""
import sys, pathlib, warnings
warnings.filterwarnings("ignore")
from playwright.sync_api import sync_playwright

ARG = sys.argv[1] if len(sys.argv) > 1 else "dist/index.html"
TARGET = ARG if ARG.startswith(("http://","https://")) else pathlib.Path(ARG).resolve().as_uri()
F, P = [], []
def check(c, m): (P if c else F).append(m)

PHONE = {'width': 390, 'height': 844}

def boot(b, who, mobile=True):
    """A fresh device that knows who is holding it and never phones home."""
    ctx = b.new_context(**({'viewport': PHONE, 'is_mobile': True, 'has_touch': True,
                            'device_scale_factor': 3} if mobile else {'viewport': {'width':1440,'height':900}}))
    ctx.add_init_script(f"try{{localStorage.setItem('dwk-who',{who!r});}}catch(e){{}}")
    # the shared vault is not part of this test — every edit stays on the device
    ctx.route("**/olsoszyirfbqdinczlvc.supabase.co/**", lambda r: r.abort())
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: F.append(f"JS error: {e}"))
    pg.goto(TARGET); pg.wait_for_timeout(1500)
    return pg

with sync_playwright() as b0:
    b = b0.chromium.launch()

    # ═════ CHASE, on his phone, with nobody helping him ═════
    pg = boot(b, 'Chase')
    pg.evaluate("buildParty(); go('party')"); pg.wait_for_timeout(600)

    seats = pg.eval_on_selector_all('.pc.open', 'e=>e.length')
    check(seats == 2, f"two seats are open and both invite a tap ({seats})")
    check(pg.eval_on_selector('.pc.open', "e=>getComputedStyle(e).cursor") == 'pointer',
          "an open seat reads as something you can take")

    pg.eval_on_selector_all('.pc.open', 'e=>e[0].click()'); pg.wait_for_timeout(500)
    check(pg.is_visible('.sheet'), "tapping it opens the sheet")
    check(pg.eval_on_selector('#sh-ok', 'e=>e.disabled') is False,
          "claiming a seat does not ask who it is for — a character is public")
    pg.fill('#sh-t', 'Brannoc'); pg.fill('#sh-t2', 'Fighter of the Low Road')
    pg.click('#sh-ok'); pg.wait_for_timeout(800)

    check(not pg.is_visible('.sheet'), "the sheet closes behind him")
    check(pg.is_visible('#v-entity'), "and he lands on his own character page")
    check(pg.inner_text('#e-name').strip() == 'Brannoc', "with his name on it")
    check('not in a recording yet' in pg.inner_text('#e-kind').lower(),
          f"honest about having no history yet ({pg.inner_text('#e-kind')})")
    check(pg.evaluate("CAMPAIGN.roster.filter(r=>r.name==='???').length") == 1,
          "one seat left open")
    check(pg.evaluate("CAMPAIGN.roster.find(r=>r.name==='Brannoc').status") == 'active',
          "and he is at the table, not still 'joining soon'")
    kinds = pg.evaluate("CHANGES.map(c=>c.kind)")
    check('roster' in kinds, f"the claim went through the change log ({kinds})")

    # ── a hero shot ──
    pg.evaluate("EDIT=true; openE('Brannoc')"); pg.wait_for_timeout(500)
    px = ("data:image/gif;base64,R0lGODlhAQABAIAAAP8AAAAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw==")
    pg.evaluate(f"pushEdit('pc_art',{{name:'Brannoc',slot:'hero',url:{px!r}}}); openE('Brannoc')")
    pg.wait_for_timeout(500)
    check(pg.eval_on_selector('#e-hero', "e=>e.classList.contains('on')")
          and pg.eval_on_selector('#atmos', "e=>!e.classList.contains('on')"),
          "a hero shot becomes the background of his page, instead of blending with the plate")

    # ── three things he carries, one of them private ──
    async_items = [
        ('A chipped shortsword, my father’s', 'He never taught me to use it.', 'all'),
        ('A writ of passage out of Vattenheim', 'Forged. Badly.', 'all'),
        ('The name of the man who paid me', '', 'mine'),
    ]
    for text, note, vis in async_items:
        pg.evaluate("void addKit('Brannoc')"); pg.wait_for_timeout(400)
        check(pg.is_visible('.sheet'), f"the sheet opens for '{text[:18]}…'")
        check(pg.eval_on_selector('#sh-ok', 'e=>e.disabled') is True,
              "and will not take the writing until it knows who it is for")
        check(pg.eval_on_selector('#sh-f', "e=>!e.classList.contains('live')"),
              "the writing box stays shut until that is answered")
        pg.click(f'.shvis button[data-v="{vis}"]'); pg.wait_for_timeout(250)
        check(pg.eval_on_selector('#sh-f', "e=>e.classList.contains('live')"),
              "answering it opens the writing box")
        pg.fill('#sh-t', text)
        if note: pg.fill('#sh-t2', note)
        pg.click('#sh-ok'); pg.wait_for_timeout(600)

    K = pg.evaluate("kitOf('Brannoc')")
    check(len(K) == 3, f"three things in his kit ({len(K)})")
    check([k['vis'] for k in K] == ['all','all','mine'], f"each remembered who it was for ({[k['vis'] for k in K]})")
    check(all(k['who'] == 'Chase' for k in K), "and that he is the one who put them there")

    # ── an image on one of them ──
    pg.evaluate(f"pushEdit('pc_kit',{{op:'img',name:'Brannoc',id:kitOf('Brannoc')[0].id,img:{px!r}}}); openE('Brannoc')")
    pg.wait_for_timeout(500)
    pg.evaluate("document.querySelectorAll('.esec').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
    check(pg.eval_on_selector_all('.kitem .kimg:not(.none)', 'e=>e.length') == 1,
          "one of them carries its own picture")

    # ── the vault joins his writing to what it already knows ──
    pg.evaluate("openE('Brannoc'); document.querySelectorAll('.esec').forEach(d=>d.open=true)")
    pg.wait_for_timeout(400)
    links = pg.eval_on_selector_all('.kitem .kt a', 'e=>e.map(x=>x.textContent)')
    check(any('vattenheim' in l.lower() for l in links),
          f"'Vattenheim' linked itself to the codex without being asked ({links})")

    # ── the three declared lines ──
    pg.evaluate("void sayEdit('Brannoc','from')"); pg.wait_for_timeout(400)
    check(pg.eval_on_selector('#sh-t', "e=>e.tagName") == 'TEXTAREA', "a declared line gets room to breathe")
    pg.click('.shvis button[data-v="all"]'); pg.wait_for_timeout(200)
    pg.fill('#sh-t', 'A fishing town the maps stopped printing.')
    pg.click('#sh-ok'); pg.wait_for_timeout(600)
    check(pg.evaluate("(sayOf('Brannoc').from||{}).v") == 'A fishing town the maps stopped printing.',
          "it is written down")
    check(pg.eval_on_selector_all('.sayrow', 'e=>e.length') == 1,
          "one question only — the other two spoiled what the table is meant to find out")
    check(pg.evaluate("SAYS.map(x=>x[0])") == ['from'], "and they are gone from the file, not just hidden")
    check(pg.eval_on_selector_all('.tagp', 'e=>e.length') >= 4,
          "everything he made up is marked as not having happened yet")

    pg.evaluate("document.querySelectorAll('.esec').forEach(d=>d.open=true)"); pg.wait_for_timeout(400)
    body = pg.inner_text('#e-body')
    check('The name of the man who paid me' in body, "his private line is there for him")

    # ── it survives being replayed from scratch, which is how everyone else gets it ──
    log = pg.evaluate("JSON.stringify(CHANGES)")
    pg.close()

    # ═════ MARCUS, on his own phone, replaying the same log ═════
    pg2 = boot(b, 'Marcus')
    pg2.evaluate("""log=>{ log.forEach(c=>{ const {kind,...rest}=c; applyEdit({kind,payload:rest}); });
                          buildParty(); openE('Brannoc'); }""", pg2.evaluate("l=>l", __import__('json').loads(log)))
    pg2.evaluate("document.querySelectorAll('.esec').forEach(d=>d.open=true)")
    pg2.wait_for_timeout(700)

    check(pg2.is_visible('#v-entity') and pg2.inner_text('#e-name').strip() == 'Brannoc',
          "Marcus opens the same page and the character is simply there")
    b2 = pg2.inner_text('#e-body')
    check('chipped shortsword' in b2, "he sees the kit Chase wrote")
    check('fishing town' in b2, "and the line Chase declared")
    check('The name of the man who paid me' not in b2,
          "but not the one Chase kept to himself")
    check(pg2.eval_on_selector_all('.kitem', 'e=>e.length') == 2,
          f"two items on his screen, not three ({pg2.eval_on_selector_all('.kitem','e=>e.length')})")
    check(pg2.eval_on_selector_all('.pc.open', 'e=>e.length') == 0 or True, "")
    P.pop()  # the line above is a placeholder for shape; drop it

    # the roster he sees has one seat left
    pg2.evaluate("go('party')"); pg2.wait_for_timeout(400)
    check(pg2.eval_on_selector_all('#h-roster .pc', 'e=>e.map(x=>x.querySelector(".pcn").textContent)').count('Brannoc') == 1,
          "and Brannoc is at the table on the Kin page")
    check(pg2.eval_on_selector_all('.pc.open', 'e=>e.length') == 1, "with one seat still open")

    # ── nothing was destroyed to hide anything ──
    check(pg2.evaluate("kitOf('Brannoc').length") == 3,
          "the hidden line was never deleted — it is hidden, not gone")

    b.close()

print(f"\n  PASS {len(P)}   FAIL {len(F)}\n")
for m in F: print("  FAIL  " + m)
print("\n  A new player can build their character alone.\n" if not F
      else "\n  The builder is not ready.\n")
sys.exit(1 if F else 0)
