#!/usr/bin/env python3
"""
The Vault — where they stand.

Everything in this section claims to be fact read out of the sixteen
recordings. So every check here is the same question asked a different way:
is the thing on the screen actually in the record?

    python3 test/verify_ties.py [path/to/index.html]
"""
import sys, pathlib, warnings
warnings.filterwarnings("ignore")
from playwright.sync_api import sync_playwright

ARG = sys.argv[1] if len(sys.argv) > 1 else "dist/index.html"
TARGET = ARG if ARG.startswith(("http://", "https://")) else pathlib.Path(ARG).resolve().as_uri()
F, P = [], []
def check(c, m): (P if c else F).append(m)

with sync_playwright() as sp:
    b = sp.chromium.launch()
    ctx = b.new_context(viewport={'width': 1280, 'height': 900})
    ctx.add_init_script("try{localStorage.setItem('dwk-who','Marcus');}catch(e){}")
    ctx.route("**/olsoszyirfbqdinczlvc.supabase.co/**", lambda r: r.abort())
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: F.append(f"JS error: {e}"))
    pg.goto(TARGET); pg.wait_for_timeout(1600)

    # ═════ the engine ═════
    ms = pg.evaluate("()=>{TIES=null;const t=performance.now();tieIndex();return Math.round(performance.now()-t);}")
    check(ms < 400, f"reading the whole record takes {ms}ms, once")

    fold = pg.evaluate("tieIndex().fold")
    check(fold.get('rune') == 'rune willow',
          f"'Rune' and 'Rune Willow' are understood to be one person ({fold.get('rune')})")
    check('dion' not in fold,
          f"but Dion is not folded into Dion's Priest — a possessive is a different name ({fold.get('dion')})")

    selfties = pg.evaluate("""()=>{const bad=[];
      ['Nyx','Ponzi','Talon','Rune Willow','Scar','Vesh'].forEach(n=>{
        const st=standingOf(n);
        st.bonds.forEach(x=>{ if(x.key===st.me) bad.push(n+'->'+x.name); });});
      return bad;}""")
    check(not selfties, f"nobody is tied to themselves ({selfties})")

    # ═════ every count is checkable against the record ═════
    audit = pg.evaluate("""()=>{
      const st=standingOf('Nyx'), out={};
      const b=st.bonds.find(x=>x.name==='Talon');
      out.talon={n:b.n,nights:b.nights.length,first:b.first,last:b.last};
      out.total=SESSIONS.length;
      // every night in the sparkline is a real session number
      out.strayNights=st.bonds.flatMap(x=>x.nights).filter(n=>!SESSIONS.some(s=>s.n===n));
      // every counted night has at least one moment behind it
      out.emptyNights=st.bonds.filter(x=>x.nights.some(n=>!x.by[n])).map(x=>x.name);
      // the sum of the per-night counts is the headline number
      out.badSums=st.bonds.filter(x=>Object.values(x.by).reduce((a,c)=>a+c,0)!==x.n).map(x=>x.name);
      return out;}""")
    check(audit['talon']['nights'] == audit['total'],
          f"Nyx and Talon are in all {audit['total']} nights ({audit['talon']})")
    check(not audit['strayNights'], f"no tie is dated to a night that does not exist ({audit['strayNights'][:3]})")
    check(not audit['emptyNights'], f"no night is counted without a moment behind it ({audit['emptyNights'][:3]})")
    check(not audit['badSums'], f"every headline count is the sum of its own nights ({audit['badSums'][:3]})")

    # a bond's evidence has to come from the sessions the bond claims
    ev = pg.evaluate("""()=>{const bad=[];
      ['Nyx','Ponzi','Scar','Vesh'].forEach(n=>standingOf(n).bonds.slice(0,6).forEach(x=>{
        [...x.ev,...(x.tail||[])].forEach(e=>{ if(!x.nights.includes(e.sn)) bad.push(x.name+' S'+e.sn); });}));
      return bad;}""")
    check(not ev, f"every line shown as proof comes from a night the tie actually spans ({ev[:3]})")

    # ═════ the reading only says things that are true ═════
    rd = pg.evaluate("""()=>{
      const st=standingOf('Nyx'), r=readingFor(st)[0];
      const top=st.bonds.filter(b=>!b.hidden)[0];
      return {tag:r.tag,head:r.head,ok:top.nights.length===SESSIONS.length};}""")
    check(rd['tag'] == 'never' and rd['ok'],
          f"the headline about never being apart is checked before it is written ({rd})")

    gone = pg.evaluate("""()=>{const st=standingOf('Scar'); const r=readingFor(st);
      const g=r.find(x=>x.tag==='gone');
      const own=[...new Set(tieIndex().ix['scar'].hits.map(h=>h.s.n))].sort((a,b)=>a-b);
      return {found:!!g, head:g&&g.head, last:own[own.length-1], quiet:r.some(x=>x.tag==='quiet')};}""")
    check(gone['found'] and str(gone['last']) in gone['head'],
          f"a character the record stopped seeing is told so, with the right night ({gone})")
    check(not gone['quiet'], "and is not also told a single bond went quiet — that is the same news twice")

    qs = pg.evaluate("""()=>{const st=standingOf('Ponzi');
      const rx=new RegExp('\\\\bPonzi\\\\b','i');
      return {n:st.threads.length, bad:st.threads.filter(t=>!rx.test(t.q)).length};}""")
    check(qs['n'] >= 10 and qs['bad'] == 0,
          f"every question listed under a name actually has that name in it ({qs})")

    # ═════ what it looks like ═════
    pg.evaluate("openE('Nyx')"); pg.wait_for_timeout(900)
    check(pg.is_visible('.rdg h3'), "the reading is the first thing on the page after the strip")
    check(pg.eval_on_selector_all('.esec', 'e=>e[0].id||e[0].querySelector("h2").textContent')
          .strip().lower().startswith('where'), "and it opens without being asked")
    check(pg.eval_on_selector_all('.fromrec', 'e=>e.length') == 1,
          "the section says out loud that it was found in the record")
    check(pg.eval_on_selector_all('.bond .tagp', 'e=>e.length') == 0,
          "nothing found in the record wears the mark that means somebody made it up")

    ticks = pg.eval_on_selector_all('.bonds .bond:not(.said2) .spk',
        "e=>e.map(x=>x.querySelectorAll('rect').length-1)")
    n = pg.evaluate("SESSIONS.length")
    check(ticks and all(t == n for t in ticks),
          f"every bond is drawn with one tick per night ({set(ticks)} vs {n})")

    first = pg.eval_on_selector('.bond', "e=>e.querySelector('.bname').textContent")
    check('Talon' in first, f"the strongest tie is at the top ({first})")
    check('closest' in pg.eval_on_selector('.bond.top .bname',
          "e=>getComputedStyle(e,'::after').content").lower(), "and is named as the closest")

    pg.eval_on_selector_all('.bond', 'e=>e[0].click()'); pg.wait_for_timeout(700)
    check(pg.eval_on_selector('.bond', "e=>e.classList.contains('open')"), "a tie opens to show its proof")
    recs = pg.eval_on_selector_all('.bond.open .brec .li', 'e=>e.length')
    check(2 <= recs <= 6, f"with a handful of real lines, not all of them ({recs})")
    marks = pg.eval_on_selector_all('.bond.open .firstt', 'e=>e.map(x=>x.textContent.trim())')
    check(marks == ['the first time', 'most recent'],
          f"the two ends of the story are marked ({marks})")
    sess = pg.eval_on_selector_all('.bond.open .brec .li .src b', 'e=>e.map(x=>+x.textContent)')
    check(sess and sess[0] == 1 and sess[-1] == n,
          f"and they really are the first night and the latest ({sess})")

    # a line of proof is a way into the recording
    pg.eval_on_selector_all('.bond.open .brec .li', 'e=>e[0].click()'); pg.wait_for_timeout(800)
    check(pg.evaluate("SESSIONS[CUR].n") == 1, "tapping the proof opens that night")

    # ═════ running a hand across the rows answers one question at a time ═════
    pg.eval_on_selector('.bonds .bond', 'e=>e.scrollIntoView({block:"center"})'); pg.wait_for_timeout(400)
    bx = pg.eval_on_selector('.bonds .bond .bspk',
        "e=>{const r=e.getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height};}")
    pg.mouse.move(bx['x'] + bx['w'] * 0.68, bx['y'] + bx['h'] / 2); pg.wait_for_timeout(400)
    lit = pg.eval_on_selector_all('.bonds[data-lit]', 'e=>[...new Set(e.map(x=>x.dataset.lit))]')
    tag = pg.eval_on_selector_all('.scrubtag', 'e=>e.map(x=>x.textContent)')
    check(len(lit) == 1 and tag and tag[0].endswith(lit[0]),
          f"one night lights up, and the page names it ({lit}, {tag})")
    check(pg.eval_on_selector_all('.bonds[data-lit]', 'e=>e.length') > 1,
          "in every group at once, not just the row under the hand")
    stray = pg.eval_on_selector_all('.spk rect.lit', "e=>[...new Set(e.map(x=>x.dataset.n))]")
    check(stray == lit, f"and nothing from another night lights up with it ({stray})")
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    check(pg.eval_on_selector_all('.bonds[data-lit]', 'e=>e.length') == 0
          and pg.eval_on_selector_all('.scrubtag', 'e=>e.length') == 0,
          "moving away puts every row back")

    # ═════ a new character is told the truth, not shown a crash ═════
    pg.evaluate("""pushEdit('roster',{op:'claim',slot:6,name:'Brannoc',cls:'Fighter',who:'Marcus'});
                   buildParty(); openE('Brannoc');"""); pg.wait_for_timeout(800)
    check(pg.is_visible('#v-entity') and 'has not met them yet' in pg.inner_text('#e-body'),
          "somebody with no history is told so plainly")

    # ═════ a wrong tie is a correction, not an argument ═════
    pg.evaluate("EDIT=true; openE('Nyx')"); pg.wait_for_timeout(700)
    before = pg.eval_on_selector_all('.bonds .bond', 'e=>e.length')
    logbefore = pg.evaluate("CHANGES.length")
    pg.evaluate("hideTie('Nyx','scar')"); pg.wait_for_timeout(700)
    after = pg.eval_on_selector_all('.bonds .bond', 'e=>e.length')
    check(pg.evaluate("standingOf('Nyx').bonds.find(b=>b.key==='scar').hidden") is True,
          "a tie marked wrong stops being shown")
    check(pg.evaluate("CHANGES.length") == logbefore + 1 and pg.evaluate("CHANGES[CHANGES.length-1].kind") == 'pc_tie',
          "and that is one new line in the log, not a deletion")
    check('set aside as wrong' in pg.inner_text('#e-body').lower(),
          "it is still listed, where anybody can put it back")
    pg.evaluate("unhideTie('Nyx','scar')"); pg.wait_for_timeout(700)
    check(pg.evaluate("standingOf('Nyx').bonds.find(b=>b.key==='scar').hidden") is False,
          "putting it back works")
    check(pg.evaluate("CHANGES.length") == logbefore + 2,
          "and that is another line again — nothing in the log is ever removed")
    check(pg.eval_on_selector_all('.bonds .bond', 'e=>e.length') == before, "the list comes back as it was")

    # ═════ something added by hand never poses as something found ═════
    pg.evaluate("""pushEdit('pc_tie',{op:'add',name:'Nyx',id:'t1',tie:'Brannoc',
        how:'Owes him a debt neither has mentioned.',vis:'all',who:'Marcus'}); openE('Nyx');""")
    pg.wait_for_timeout(700)
    check(pg.evaluate("standingOf('Nyx').bonds.some(b=>b.name==='Brannoc')") is False,
          "a tie somebody typed does not join the ties the record found")
    check('added by the table' in pg.inner_text('#e-body').lower(), "it gets its own heading")
    check(pg.eval_on_selector_all('.bond.said2 .tagp', 'e=>e.length') == 1,
          "and wears the mark that means it has not happened yet")

    # ═════ and it does not slow the page down ═════
    t = pg.evaluate("()=>{const a=performance.now(); openE('Ponzi'); return Math.round(performance.now()-a);}")
    check(t < 900, f"opening a character page still takes {t}ms")

    b.close()

print(f"\n  PASS {len(P)}   FAIL {len(F)}\n")
for m in F: print("  FAIL  " + m)
print("\n  Everything it calls fact is in the record.\n" if not F
      else "\n  It is claiming something the record does not say.\n")
sys.exit(1 if F else 0)
