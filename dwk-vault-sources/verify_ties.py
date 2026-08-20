#!/usr/bin/env python3
"""
The Vault — the character page: building one, and its connections.

Two things are being checked. First, that a player can put something into
their own character without turning anything on — the builder was once hidden
behind Edit mode and nobody ever found it. Second, that the connections are a
way into the audio and never a pile of numbers about a friendship.

    python3 test/verify_ties.py [path/to/index.html]
"""
import sys, pathlib, warnings
warnings.filterwarnings("ignore")
from playwright.sync_api import sync_playwright

ARG = sys.argv[1] if len(sys.argv) > 1 else "dist/index.html"
TARGET = ARG if ARG.startswith(("http://", "https://")) else pathlib.Path(ARG).resolve().as_uri()
F, P = [], []
def check(c, m): (P if c else F).append(m)
def openAll(pg): pg.evaluate("document.querySelectorAll('.esec').forEach(d=>d.open=true)")

with sync_playwright() as sp:
    b = sp.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    ctx.add_init_script("try{localStorage.setItem('dwk-who','Marcus');}catch(e){}")
    ctx.route("**/olsoszyirfbqdinczlvc.supabase.co/**", lambda r: r.abort())
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: F.append(f"JS error: {e}"))
    pg.goto(TARGET); pg.wait_for_timeout(1600)

    # ═════ the engine reads the record, once, and fast ═════
    ms = pg.evaluate("()=>{TIES=null;const t=performance.now();tieIndex();return Math.round(performance.now()-t);}")
    check(ms < 400, f"reading the whole record takes {ms}ms, once")
    fold = pg.evaluate("tieIndex().fold")
    check(fold.get('rune') == 'rune willow', "'Rune' and 'Rune Willow' are understood to be one person")
    check('dion' not in fold, "but Dion is not folded into Dion's Priest — a possessive is a different name")
    bad = pg.evaluate("""()=>{const out=[];['Nyx','Ponzi','Talon','Scar'].forEach(n=>{
        const st=standingOf(n); st.bonds.forEach(x=>{ if(x.key===st.me) out.push(n); });});return out;}""")
    check(not bad, f"nobody is tied to themselves ({bad})")

    # ═════ THE BUILDER — no mode to turn on ═════
    pg.evaluate("EDIT=false; openE('Nyx')"); pg.wait_for_timeout(800)
    check(pg.eval_on_selector_all('.bldbar', 'e=>e.length') == 1,
          "a character page offers a way to build them without turning Edit on")
    labels = pg.eval_on_selector_all('.bldbar .up', 'e=>e.map(x=>x.textContent.trim())')
    check(any('picture' in x.lower() for x in labels) and any('line' in x.lower() for x in labels),
          f"a picture and the line under their name, right there ({labels})")
    heads = pg.eval_on_selector_all('.esec summary h2', 'e=>e.map(x=>x.textContent)')
    check(heads[0] == 'What they carry', f"what they carry leads the page ({heads[0]})")
    check(heads[-1] == 'Connections', f"and the connections come last ({heads[-1]})")
    check(pg.eval_on_selector_all('.esec[open] summary h2', 'e=>e.map(x=>x.textContent)') == ['What they carry'],
          "the builder is the one box that starts open — everything else is folded")
    check(pg.eval_on_selector('.esec:not([open])>summary',
          "e=>getComputedStyle(e,'::after').content").strip('"') == 'open',
          "and every folded box says it opens, because nobody knew they did")
    check(pg.eval_on_selector_all('.kitnone', 'e=>e.length') == 1
          and pg.eval_on_selector_all('.esec[open] .up', 'e=>e.length') >= 1,
          "an empty kit is an invitation with a button, not a blank")

    # a real item, added the way a player would, with nothing switched on
    pg.evaluate("void addKit('Nyx')"); pg.wait_for_timeout(500)
    check(pg.is_visible('.sheet'), "the sheet opens straight off the page")
    check(pg.eval_on_selector('#sh-ok', 'e=>e.disabled') is True,
          "and still asks who it is for before it takes the writing")
    pg.click('.shvis button[data-v="all"]'); pg.wait_for_timeout(250)
    pg.fill('#sh-t', 'A chipped shortsword out of Vattenheim')
    pg.fill('#sh-t2', 'He never learned to use it.')
    pg.click('#sh-ok'); pg.wait_for_timeout(700)
    check(pg.evaluate("kitOf('Nyx').length") == 1, "the thing lands in their kit")
    check(pg.eval_on_selector_all('.kitem', 'e=>e.length') == 1, "and on the page")
    check(pg.eval_on_selector_all('.kitem .kedit button', 'e=>e.length') >= 3,
          "with picture, edit and remove on it, no mode required")
    links = pg.eval_on_selector_all('.kitem .kt a', 'e=>e.map(x=>x.textContent)')
    check(any('vattenheim' in x.lower() for x in links),
          f"and a name the campaign knows links itself to the Codex ({links})")

    # ═════ THE WEB — six names, drawn, no numbers ═════
    openAll(pg); pg.wait_for_timeout(500)
    nodes = pg.eval_on_selector_all('.wnode', 'e=>e.length')
    check(nodes == 6, f"six names in the ring, not ninety-one in a list ({nodes})")
    check(pg.eval_on_selector_all('.websvg', 'e=>e.length') == 1, "drawn, not written")
    check(pg.eval_on_selector_all('.spk', 'e=>e.length') == 0
          and pg.evaluate("typeof readingFor==='undefined'"),
          "the counting and the rankings stay gone")
    drawn = pg.eval_on_selector('.websvg', 'e=>e.textContent')
    check(not any(ch.isdigit() for ch in drawn),
          f"no number about a friendship is drawn anywhere on it ({drawn[:60]!r})")

    # every node sits on the ring at the same distance, so nothing looks like a winner
    geo = pg.eval_on_selector_all('.wnode circle:last-of-type',
        "e=>e.map(c=>Math.round(Math.hypot(+c.getAttribute('cx')-180,+c.getAttribute('cy')-166)))")
    check(len(set(geo)) == 1, f"all six sit the same distance out ({set(geo)})")
    widths = pg.eval_on_selector_all('.wline:not(.on)', "e=>[...new Set(e.map(x=>getComputedStyle(x).strokeWidth))]")
    check(len(widths) == 1, f"and every line is the same weight ({widths})")

    lit = pg.eval_on_selector_all('.wlab.on', 'e=>e.map(x=>x.textContent)')
    check(len(lit) == 1, f"one is lit to start with, so the panel is never empty ({lit})")
    recs = pg.eval_on_selector_all('.webpanel .li', 'e=>e.length')
    check(1 <= recs <= 4, f"and it shows a handful of real lines, not all of them ({recs})")
    heads2 = pg.eval_on_selector('.webhead', 'e=>e.textContent.replace(/\\s+/g," ").trim()')
    check('Nyx and' in heads2 and 'Session' in heads2, f"named plainly ({heads2})")

    pg.eval_on_selector_all('.wnode', 'e=>e[3].dispatchEvent(new MouseEvent("click",{bubbles:true}))')
    pg.wait_for_timeout(600)
    lit2 = pg.eval_on_selector_all('.wlab.on', 'e=>e.map(x=>x.textContent)')
    check(len(lit2) == 1 and lit2 != lit, f"tapping another lights that one instead ({lit2})")
    check(lit2[0] in pg.eval_on_selector('.webhead', 'e=>e.textContent'),
          "and the lines underneath are that connection's")

    # two taps from a character page to hearing the night
    pg.eval_on_selector_all('.webpanel .li', 'e=>e[0].click()'); pg.wait_for_timeout(800)
    check(pg.evaluate("SESSIONS[CUR].n") > 0, "and tapping a line opens that night's recording")

    # ═════ the long list is still there, underneath, in tens ═════
    pg.evaluate("openE('Nyx')"); openAll(pg); pg.wait_for_timeout(600)
    check(pg.eval_on_selector_all('.bonds .bond', 'e=>e.length') == 8, "eight in the list to start with")
    pg.eval_on_selector_all('#b-morebtn', 'e=>e[0].click()'); pg.wait_for_timeout(500)
    check(pg.eval_on_selector_all('.bonds .bond', 'e=>e.length') == 18,
          "and ten more at a time, never seventy-six")
    nums = pg.eval_on_selector_all('.bond .bnum', 'e=>e.map(x=>x.textContent.trim())')
    check(all(x.startswith('Session') for x in nums),
          f"a row says which nights and claims nothing else ({nums[:2]})")

    # ═════ a question the recordings inflated can be put down ═════
    pg.evaluate("go('codex'); buildCodex(); buildThreads(); cxTab('threads'); EDIT=true; buildThreads()")
    pg.wait_for_timeout(700)
    rows = pg.eval_on_selector_all('#t-body .li', 'e=>e.length')
    check(pg.eval_on_selector_all('#t-body .qed', 'e=>e.length') == rows,
          "every open question can be reworded, answered or put down")
    before = pg.evaluate("thr()")
    pg.evaluate("qPush(SESSIONS[0],0,'hidden',true); buildThreads()"); pg.wait_for_timeout(400)
    check(pg.evaluate("thr()") == before - 1, "putting one down stops it being counted")
    check(pg.evaluate("CHANGES[CHANGES.length-1].path") == 'threads.0.hidden',
          "and it goes through the same log as every other change")
    pg.evaluate("EDIT=false; buildThreads()"); pg.wait_for_timeout(400)
    check(pg.eval_on_selector_all('#t-body .li.put', 'e=>e.length') == 0,
          "everyone else simply does not see it, and nothing was deleted")

    # ═════ one card that was two people ═════
    pg.evaluate("pushEdit('codex',{op:'split',key:'ponsey / talon',value:['Ponzi','Talon']}); TIES=null;")
    pg.wait_for_timeout(500)
    ixn = pg.evaluate("Object.keys(codexIndex())")
    check('ponsey / talon' not in ixn and 'ponzi' in ixn and 'talon' in ixn,
          "a card that was two people becomes two cards")

    # ═════ and a brand-new character is told the truth ═════
    pg.evaluate("""pushEdit('roster',{op:'claim',slot:6,name:'Brannoc',cls:'Fighter',who:'Marcus'});
                   buildParty(); openE('Brannoc');""")
    openAll(pg); pg.wait_for_timeout(700)
    body = pg.inner_text('#e-body')
    check('has not met them yet' in body, "somebody with no history is told so plainly")
    check(pg.eval_on_selector_all('.bldbar', 'e=>e.length') == 1
          and pg.eval_on_selector_all('.kitnone', 'e=>e.length') == 1,
          "and still handed everything they need to build themselves")

    t = pg.evaluate("()=>{const a=performance.now(); openE('Ponzi'); return Math.round(performance.now()-a);}")
    check(t < 900, f"opening a character page takes {t}ms")

    b.close()

print(f"\n  PASS {len(P)}   FAIL {len(F)}\n")
for m in F: print("  FAIL  " + m)
print("\n  A player can build their character, and see who they are tangled with.\n" if not F
      else "\n  Not there yet.\n")
sys.exit(1 if F else 0)
