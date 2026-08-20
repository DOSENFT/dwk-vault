# The Vault — how it is put together

The published page is one file: `dist/index.html`. It is built from five,
and it can always be taken apart back into those five. That is the whole
architecture.

    build/app.html        the app — markup, style, behaviour
    vault/vault-data.js   the campaign, normalised out of the recordings
    vault/audio.js        which recording belongs to which night
    vault/sync.js         where the shared vault lives
    vault/art.js          the atmosphere plates

    python3 build.py      ->  dist/index.html

## Testing

    bash test/all.sh                 every suite
    python3 test/verify.py           the regression suite — 85 checks
    python3 test/verify_builder.py   a new player builds their character alone
    python3 test/verify_ties.py      everything the page calls fact is in the record

Each check in `test/verify.py` exists because that exact thing once broke and
shipped. Nothing in there is hypothetical.

## Things that are not to be re-litigated

* **The shared log is append-only.** Every change is a new row in
  `vault_edits`. There is no UPDATE policy and no DELETE policy, so the page
  physically cannot destroy campaign history. Undo is a compensating row.
* **The recordings live on GitHub Pages, not on Releases.** Releases serve
  `application/octet-stream` with a `Content-Disposition: attachment` header.
  Chrome sniffs past it; WebKit never does — so every iPhone at the table got
  `MediaError.code 4`. Pages serves `audio/mp3` with range support and no
  disposition header. Confirmed on a real iPhone, iOS 18.6.
* **The atmosphere layer sits at `z-index:-1` and is `100lvh` tall.** A
  `body > .thing` rule once out-specified `position:fixed` and flattened the
  Reel into a 14,000px block; `100vh` plus `background-attachment:fixed` made
  the plates lurch as a phone retracted its toolbars. Both have tests.
* **The masthead order ends in the How-to link**, with a gap before it so a
  thumb does not hit it by accident. Tested.

## Two halves of a character page, and they must never look alike

* **Found** — read out of the sixteen recordings by `tieIndex()`. Who a name
  has been put beside, which of the open questions carry it, and the actual
  lines that prove it. Keyed to moss, tagged *found in the record*, stated
  flatly. Nobody chose any of it.
* **Declared** — a kit item, a line somebody wrote, a tie somebody added by
  hand. Keyed to gold, always tagged *not played yet* until it happens at
  the table.

A found tie is never edited, because editing it would mean editing the
recording. It is shown or set aside, and setting it aside is one more row in
the log. `test/verify_ties.py` fails the build if anything found ever wears
the mark that means somebody made it up.

## Why these files are in the repo

They used to live only in a working container. Twice that container was
reclaimed mid-build, and each time the sources had to be reconstructed by
downloading the published `index.html` and splitting the script blocks back
apart — about an hour, twice. With the sources committed here, a reset costs
nothing: clone, `python3 build.py`, carry on.
