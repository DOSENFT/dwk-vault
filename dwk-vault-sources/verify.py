#!/usr/bin/env python3
"""
The Vault — regression test.

Every check here exists because that exact thing once broke and shipped.

    python3 test/verify.py [path/to/index.html | https://your-site/]
"""
import sys, pathlib, io, warnings
warnings.filterwarnings("ignore")

ARG = sys.argv[1] if len(sys.argv) > 1 else "dist/index.html"
IS_URL = ARG.startswith(("http://", "https://"))
TARGET = ARG if IS_URL else pathlib.Path(ARG).resolve().as_uri()
FAILS, WARNS, PASSES = [], [], []
def check(cond, msg, soft=False):
    (PASSES if cond else (WARNS if soft else FAILS)).append(msg)

MIN_SESSIONS, MIN_BEATS, MIN_ENTITIES, MIN_THREADS, MIN_AUDIO = 16, 340, 240, 100, 5
REQUIRED_VIEWS = ['v-home','v-session','v-codex','v-entity','v-party','v-score','v-search']
REQUIRED_IDS = [
    'vault-data','vault-audio','vault-sync','vault-art','atmos',
    'h-list','h-roster','h-listen','h-offline',
    's-five','s-tabs','s-panes','s-listen','s-shape',
    'cx-tabs','cx-pane-all','cx-pane-threads','cx-body','cx-controls','t-body',
    'e-body','e-extra','e-hero','pt-body','pt-sub','sc-body','q-body',
    'reel','r-scroll','r-rail','r-trk','r-play','r-close','r-next','r-prev','r-back','r-fwd','r-hint',
    'p-exp','pb','p-trk','au','srch','editBtn','saveBtn','syncPill',
]
REQUIRED_FNS = ['openS','openE','openReel','closeReel','listen','jump','seekTo','startPlay',
                'buildShape','stripFor','arcOf','buildParty','cxTab','openThreads',
                'pushEdit','applyEdit','resetToBaked','doReplace','trouble','stepMoment']

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()

    # ═════ DESKTOP ═════
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(TARGET); pg.wait_for_timeout(2000)
    check(not errs, f"no JS errors on load ({errs[:2]})")

    missing = [i for i in REQUIRED_IDS if pg.eval_on_selector_all(f'#{i}', 'e=>e.length') != 1]
    check(not missing, f"every element the code reaches for exists ({missing})")
    missing = [v for v in REQUIRED_VIEWS if pg.eval_on_selector_all(f'#{v}', 'e=>e.length') != 1]
    check(not missing, f"every view exists ({missing})")
    missing = pg.evaluate("fns=>fns.filter(f=>typeof window[f]!=='function')", REQUIRED_FNS)
    check(not missing, f"every load-bearing function is defined ({missing})")

    # a class collision once shrank the wordmark to 22px
    mk = pg.eval_on_selector('.mk', "e=>{const c=getComputedStyle(e),r=e.getBoundingClientRect();"
                                    "return {w:r.width,pos:c.position,clipped:r.width<e.scrollWidth-1};}")
    check(mk['pos'] == 'static' and mk['w'] > 60 and not mk['clipped'],
          f"the masthead wordmark is laid out as itself ({mk})")
    check(pg.eval_on_selector('.mnav .howto', 'e=>e.getAttribute("href")') == 'guide.html',
          "the top bar links to the guide")
    order = pg.eval_on_selector_all('.mnav > *', 'e=>e.map(x=>x.id||x.className||x.textContent.trim())')
    check('howto' in str(order[-1]), f"the guide link is last in the bar ({order})")
    gap = pg.eval_on_selector('.mnav .howto', "e=>{const q=e.previousElementSibling;"
                                              "return q?Math.round(e.getBoundingClientRect().left"
                                              "-q.getBoundingClientRect().right):999;}")
    check(gap >= 16, f"and set far enough from Edit to not be hit by accident ({gap}px)")
    check(pg.eval_on_selector_all('#atmosBtn', 'e=>e.length') == 0, "the background toggle is gone")

    S = pg.evaluate('SESSIONS')
    check(len(S) >= MIN_SESSIONS, f"{len(S)} sessions (>= {MIN_SESSIONS})")
    check(sum(len(s['beats']) for s in S) >= MIN_BEATS, "moments above the floor")
    check(sum(len(s['entities']) for s in S) >= MIN_ENTITIES, "entities above the floor")
    check(sum(len(s['threads']) for s in S) >= MIN_THREADS, "threads above the floor")

    bad_t = [(s['slug'], x['t']) for s in S for x in s['beats']
             if x.get('t') is not None and s.get('durationSec') and x['t'] > s['durationSec']]
    check(not bad_t, f"no moment is timecoded past the end of its recording ({bad_t[:3]})")
    nocards = [s['slug'] for s in S
               if sum(1 for v in (s.get('cards') or {}).values() if v and v.get('headline')) < 5]
    check(not nocards, f"every session has all five cards ({nocards[:3]})")
    check(not [s['slug'] for s in S if not (s.get('recap') or '').strip()], "every session has a recap")

    A = pg.evaluate('AUDIO_URLS')
    check(len(A) >= MIN_AUDIO, f"{len(A)} recordings wired")
    check(all(u.startswith('https://') for u in A.values()), "every recording is https")
    rel = [k for k, u in A.items() if 'releases/download' in u]
    check(not rel, f"no recording points at a GitHub release — Apple devices refuse those ({rel})")
    check(pg.eval_on_selector('#au', 'e=>e.src').endswith(('.mp3','.m4a','.wav')), "the player has a real source")

    check(pg.eval_on_selector('#h-listen .lbig', 'e=>e.getBoundingClientRect().width >= 48'),
          "the home page opens with a real play button")
    check(pg.eval_on_selector_all('#h-list .rp', 'e=>e.length') == len(A),
          "sessions with a recording are marked")

    pg.eval_on_selector_all('#h-list a', 'e=>e[0].click()'); pg.wait_for_timeout(900)
    check(pg.is_visible('#v-session'), "clicking a session opens it")
    check(pg.eval_on_selector_all('.row', 'e=>e.length') > 5, "moments render")
    check(pg.eval_on_selector_all('.f', 'e=>e.length') == 5, "the five cards render")
    check(pg.eval_on_selector('#s-listen .lbig', 'e=>e.getBoundingClientRect().width >= 48'),
          "a session leads with a play button")
    ticks = pg.eval_on_selector_all('#s-shape .shk', 'e=>e.length')
    check(ticks == pg.evaluate("SESSIONS[CUR].beats.length"), f"one tick per moment ({ticks})")
    check(pg.eval_on_selector_all('#s-shape .shk i',
          'e=>[...new Set(e.map(n=>getComputedStyle(n).backgroundColor))].length') > 2,
          "ticks are coloured by kind of moment")
    pg.hover('#s-shape .shk:nth-of-type(4)'); pg.wait_for_timeout(400)
    check(pg.is_visible('#s-pop'), "touching a tick names that moment")

    pg.click('#p-exp'); pg.wait_for_timeout(900)
    check(pg.is_visible('#reel'), "the Reel opens")
    check(pg.eval_on_selector('#reel', 'e=>getComputedStyle(e).position') == 'fixed',
          "the Reel is a full-screen room, not a block in the page")
    cards = pg.eval_on_selector_all('#r-scroll .rcard', 'e=>e.length')
    check(cards > 5, f"the Reel holds one card per moment ({cards})")
    check(pg.eval_on_selector_all('#r-scroll .rcard.on', 'e=>e.length') == 1, "one moment lit at a time")
    check('mandatory' in pg.eval_on_selector('#r-scroll', 'e=>getComputedStyle(e).scrollSnapType'),
          "the Reel snaps to a moment")
    check(pg.eval_on_selector_all('#r-rail .notch', 'e=>e.length') == cards, "every moment marked on the bar")
    n0 = pg.inner_text('#r-pos'); pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(700)
    check(pg.inner_text('#r-pos') != n0, "arrow keys move through the Reel")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    check(not pg.is_visible('#reel'), "Escape closes the Reel")

    pg.click('.mnav button[data-v="codex"]'); pg.wait_for_timeout(900)
    check(pg.eval_on_selector_all('#cx-body .cx', 'e=>e.length') > 50, "the Codex renders entries")
    check(pg.eval_on_selector_all('#cx-body .cxsec[data-k="pc"]', 'e=>e.length') == 0,
          "the Codex does not repeat the party")
    pg.evaluate("cxTab('threads')"); pg.wait_for_timeout(700)
    check(pg.eval_on_selector_all('#t-body .li', 'e=>e.length') > 30, "the Still Hanging tab renders")
    check(pg.eval_on_selector('#cx-pane-all', 'e=>e.hidden'), "opening it puts the codex list away")
    pg.evaluate("cxTab('all')"); pg.wait_for_timeout(400)

    # typing 'Vesh' in the masthead box jumps to the search view, which hides the
    # codex — so each box gets walked back to a page where it is actually on screen.
    for box, where in [('#srch', 'the search box'), ('#cxq', 'the codex filter')]:
        pg.click('.mnav button[data-v="codex"]'); pg.wait_for_timeout(600)
        pg.evaluate("cxTab('all')"); pg.wait_for_timeout(300)
        pg.fill(box, ''); pg.click(box); pg.type(box, 'Vesh', delay=70); pg.wait_for_timeout(700)
        got = pg.input_value(box)
        check(got == 'Vesh', f"{where} types forwards ({got!r})")
        pg.fill(box, ''); pg.wait_for_timeout(400)

    pg.click('.mnav button[data-v="party"]'); pg.wait_for_timeout(900)
    check(pg.is_visible('#v-party'), "the Driftwood Kin have their own page")
    check('Driftwood Kin' in pg.inner_text('#v-party .st'), "and it is called that")
    ratio = pg.eval_on_selector('#h-roster .pc', "e=>{const r=e.getBoundingClientRect();return r.height/r.width;}")
    check(1.2 < ratio < 1.5, f"portrait-shaped cards ({ratio:.2f})")

    pg.eval_on_selector_all('#h-roster .pc', 'e=>e[0].click()'); pg.wait_for_timeout(900)
    check(pg.is_visible('#v-entity'), "a portrait opens that character")
    smk = pg.eval_on_selector_all('#e-strip .smk', 'e=>e.length')
    rows = pg.eval_on_selector_all('#e-body .arcrow', 'e=>e.length')
    check(smk > 4 and smk == rows == pg.evaluate("STRIP.length"),
          f"their strip and their arc tell the same story ({smk}/{rows})")
    check(pg.eval_on_selector_all('#e-body .esec', 'e=>e.length') >= 3, "folded into sections")
    check('really' not in pg.inner_text('.ehead').lower(), "no 'really <name>' on the front")
    pg.hover('#e-strip .smk:nth-of-type(3)'); pg.wait_for_timeout(400)
    check(pg.is_visible('#e-pop'), "hovering a mark says what that night was")

    pg.eval_on_selector_all('#h-list a', 'e=>e[0].click()'); pg.wait_for_timeout(800)
    pg.click('#editBtn'); pg.wait_for_timeout(500)
    check(pg.eval_on_selector('body', 'e=>e.classList.contains("editing")'), "edit mode turns on")
    check(pg.eval_on_selector_all('[data-e]', 'e=>e.length') > 40, "editable fields exist")
    pg.eval_on_selector('#s-title', 'e=>{e.focus();e.textContent="__TEST__";e.blur();}')
    pg.wait_for_timeout(500)
    check(pg.evaluate('SESSIONS[CUR].title') == '__TEST__', "editing a field updates the data")
    pg.click('#editBtn'); pg.wait_for_timeout(300)

    pg.evaluate("scrollTo(0,1400)"); pg.wait_for_timeout(500)
    vh = pg.evaluate("innerHeight")
    st = pg.evaluate("""()=>({bar:getComputedStyle(document.querySelector('.bar')).position,
        mast:getComputedStyle(document.querySelector('.mast')).position,
        reel:getComputedStyle(document.querySelector('.reel')).position,
        barBottom:Math.round(document.querySelector('.bar').getBoundingClientRect().bottom),
        mastTop:Math.round(document.querySelector('.mast').getBoundingClientRect().top)})""")
    check(st['bar'] == 'fixed' and abs(st['barBottom'] - vh) <= 1, f"the player floats ({st})")
    check(st['mast'] == 'sticky' and st['mastTop'] <= 1, "the masthead stays at the top")
    check(st['reel'] == 'fixed', "the Reel is still an overlay")

    css = pg.content()
    check('100lvh' in css, "the atmosphere is sized to the large viewport, not the shifting one")
    check('background-attachment:fixed' not in css.replace(' ', ''), "no fixed-attachment background")
    atmos = pg.eval_on_selector('.atmos', "e=>({pos:getComputedStyle(e).position,tr:getComputedStyle(e).transform})")
    check(atmos['pos'] == 'fixed' and atmos['tr'] != 'none', f"the atmosphere has its own paint layer ({atmos})")

    pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(700)
    on = pg.screenshot()
    pg.evaluate("document.querySelector('.atmos').style.visibility='hidden'"); pg.wait_for_timeout(300)
    off = pg.screenshot()
    pg.evaluate("document.querySelector('.atmos').style.visibility=''")
    try:
        from PIL import Image
        a, c = Image.open(io.BytesIO(on)).convert('RGB'), Image.open(io.BytesIO(off)).convert('RGB')
        box = (0, 0, a.width, a.height // 3)
        pa, pb = list(a.crop(box).getdata()), list(c.crop(box).getdata())
        d = sum(abs(x[0]-y[0])+abs(x[1]-y[1])+abs(x[2]-y[2]) for x, y in zip(pa, pb)) / (3*len(pa))
        check(d > 6, f"the photographs reach the screen (mean difference {d:.1f}/255)")
        check(d < 70, f"and are not overpowering the type ({d:.1f}/255)")
    except ImportError:
        check(True, "atmosphere pixel check skipped (no PIL)", soft=True)

    check(not errs, f"no JS errors after all of that ({errs[:2]})")
    pg.close()

    # ═════ MOBILE ═════
    m = b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True)
    merrs = []; m.on('pageerror', lambda e: merrs.append(str(e)))
    m.goto(TARGET); m.wait_for_timeout(1800)

    def spills(page):
        return page.evaluate("""()=>{const w=document.documentElement.clientWidth;
          const inScroller=e=>{for(let n=e.parentElement;n;n=n.parentElement){
            const s=getComputedStyle(n);
            if((s.overflowX==='auto'||s.overflowX==='scroll')&&n.scrollWidth>n.clientWidth)return true;}
            return false;};
          return [...document.querySelectorAll('body *')].filter(e=>{
            if(e.closest('.reel'))return false;
            const r=e.getBoundingClientRect();
            return (r.width>w+2||r.right>w+4)&&!inScroller(e);})
            .map(e=>e.id?'#'+e.id:(typeof e.className==='string'&&e.className?'.'+e.className.split(' ')[0]:e.tagName))
            .filter((v,i,a)=>a.indexOf(v)===i).slice(0,8);}""")
    def page_scrolls(page):
        return page.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")

    check(not page_scrolls(m), "MOBILE: the home page does not scroll sideways")
    o = spills(m); check(not o, f"MOBILE: nothing overflows on home ({o})")
    off = m.evaluate("""()=>{const w=document.documentElement.clientWidth;
      return [...document.querySelectorAll('.mnav > *')].filter(e=>{
        const r=e.getBoundingClientRect();
        if(!r.width && !r.height) return false;
        return r.right>w+1 || r.left<-1;}).map(e=>e.textContent.trim()||e.id);}""")
    check(not off, f"MOBILE: every control in the top bar is on screen ({off})")
    pos = m.evaluate("""()=>{const r=x=>document.querySelector(x).getBoundingClientRect();
      const h=r('.mnav .howto'), e=r('#editBtn');
      const sameLine = h.bottom>e.top && h.top<e.bottom;
      return {after: sameLine ? h.left>e.right : h.top>e.top, gap: Math.round(h.left-e.right)};}""")
    check(pos['after'], f"MOBILE: the guide link comes after Edit ({pos})")

    m.click('#p-exp'); m.wait_for_timeout(900)
    check(m.is_visible('#reel'), "MOBILE: the Reel opens")
    for cid in ['#r-close', '#r-play', '#r-next', '#r-prev', '#r-back', '#r-fwd']:
        vis = m.eval_on_selector(cid, "e=>{const r=e.getBoundingClientRect();const d=document.documentElement;"
                                      "return r.right<=d.clientWidth+1 && r.left>=-1 && r.bottom<=d.clientHeight+1"
                                      " && r.width>=40 && r.height>=40;}")
        check(vis, f"MOBILE: {cid} is on screen and thumb-sized")
    check(m.eval_on_selector('#r-rail', 'e=>getComputedStyle(e).display!=="none"'),
          "MOBILE: the moment marks are still on the time bar")
    m.click('#r-close'); m.wait_for_timeout(700)
    check(not m.is_visible('#reel'), "MOBILE: the close button closes the Reel")

    m.eval_on_selector_all('#h-list a', 'e=>e[0].click()'); m.wait_for_timeout(900)
    check(m.eval_on_selector('#s-listen .lbig', 'e=>e.getBoundingClientRect().width >= 48'),
          "MOBILE: a session leads with a real play button")
    o = spills(m); check(not o, f"MOBILE: nothing overflows on a session ({o})")
    m.evaluate("buildParty();go('party')"); m.wait_for_timeout(900)
    check(not page_scrolls(m), "MOBILE: the Kin page does not scroll sideways")
    m.eval_on_selector_all('#h-roster .pc', 'e=>e[0].click()'); m.wait_for_timeout(900)
    check(not page_scrolls(m), "MOBILE: a character page does not scroll sideways")
    check(not merrs, f"MOBILE: no JS errors ({merrs[:2]})")
    m.close()

    # ═════ ACCESSIBILITY FLOOR ═════
    a = b.new_page(viewport={'width': 1440, 'height': 900})
    a.goto(TARGET); a.wait_for_timeout(1500)
    check(a.eval_on_selector('html', 'e=>e.lang') == 'en', "html lang is set")
    check(a.eval_on_selector_all('img:not([alt])', 'e=>e.length') == 0, "no image missing alt text")
    nameless = a.eval_on_selector_all('button',
        'e=>e.filter(x=>!x.textContent.trim()&&!x.getAttribute("aria-label")).length')
    check(nameless == 0, f"every button has an accessible name ({nameless} without)", soft=True)
    check('prefers-reduced-motion' in a.content(), "reduced motion is honoured", soft=True)
    a.close(); b.close()

print(f"\n  PASS {len(PASSES)}   WARN {len(WARNS)}   FAIL {len(FAILS)}\n")
for m in WARNS: print("  WARN  " + m)
for m in FAILS: print("  FAIL  " + m)
if not FAILS: print("\n  Safe. The vault still does everything it promised.\n")
sys.exit(1 if FAILS else 0)
