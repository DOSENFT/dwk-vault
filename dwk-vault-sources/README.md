# The Vault — how it is put together

The published page is one file: `dist/index.html`. It is built from five, and
it can always be taken apart back into those five. That is the whole
architecture.

    build/app.html        the app — markup, style, behaviour
    vault/vault-data.js   the campaign, normalised out of the recordings
    vault/audio.js        which recording belongs to which night
    vault/sync.js         where the shared vault lives
    vault/art.js          the atmosphere plates

    python3 build.py      ->  dist/index.html

## If the workspace is ever wiped

    python3 recover.py    downloads the live vault and splits it back into the five
    python3 build.py

That is the whole recovery. It has been needed three times.

## Testing

    bash test/all.sh                 every suite
    python3 test/verify.py           the regression suite
    python3 test/verify_builder.py   a new player builds their character alone
    python3 test/verify_ties.py      the character page: building one, and its connections

Every check in `test/verify.py` exists because that exact thing once broke and
shipped. Nothing in there is hypothetical.

## Two halves of a character page, and they must never look alike

* **Found** — read out of the recordings by `tieIndex()`. Who a name has been
  put in a scene with, and the actual lines that prove it. Tagged *found in
  the record*. Nobody chose any of it.
* **Declared** — a kit item, a line somebody wrote, a tie somebody added by
  hand. Keyed to gold, always tagged *not played yet* until it happens at the
  table.

A found tie is never edited, because editing it would mean editing the
recording. It is shown or set aside, and setting it aside is one more row in
the log.

## Things that are not to be re-litigated

* **The shared log is append-only.** Every change is a new row in
  `vault_edits`. There is no UPDATE policy and no DELETE policy, so the page
  physically cannot destroy campaign history. Undo is a compensating row.
* **A character page is not the campaign record.** Putting a picture on your
  own character, writing the line under their name, and adding to their kit
  are open to whoever is holding the phone — no Edit mode. Only the campaign's
  own record (session text, the Codex, the open questions) sits behind Edit.
  The builder was once behind Edit and nobody ever found it.
* **No numbers about a friendship.** Counting how often two names land in the
  same paragraph is not a measure of how close two people are, and printed on
  a page somebody reads it as one. The web draws six names on an even ring
  with even lines, and the only claim it makes is the one it states out loud.
  `test/verify_ties.py` fails the build if a digit is ever drawn on it.
* **The recordings live on GitHub Pages, not on Releases.** Releases serve
  `application/octet-stream` with a `Content-Disposition: attachment` header.
  Chrome sniffs past it; WebKit never does — so every iPhone at the table got
  `MediaError.code 4`. Pages serves `audio/mp3` with range support and no
  disposition header. Confirmed on a real iPhone, iOS 18.6.
* **The atmosphere layer sits at `z-index:-1` and is `100lvh` tall.** A
  `body > .thing` rule once out-specified `position:fixed` and flattened the
  Reel into a 14,000px block; `100vh` plus `background-attachment:fixed` made
  the plates lurch as a phone retracted its toolbars. Both have tests.
* **A character with art gets that art as the page background**, and the
  atmosphere plate stands down. The two layered together made mud.
* **The masthead order ends in the How-to link**, with a gap before it so a
  thumb does not hit it by accident. Tested.

## Adding the sessions that are missing

The pipeline is: raw Notta AI Note (markdown) → `data/SCHEMA.md` →
`data/json/<slug>.json` → `vault/vault-data.js`. Session numbers are derived
from the date, so inserting an older night renumbers everything after it on
its own. The audio map and the shared edit log are both keyed by slug, so
neither breaks when that happens.
