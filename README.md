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

## Why these files are in the repo

They used to live only in a working container. Twice that container was
reclaimed mid-build, and each time the sources had to be reconstructed by
downloading the published `index.html` and splitting the script blocks back
apart — about an hour, twice. With the sources committed here, a reset costs
nothing: clone, `python3 build.py`, carry on.
