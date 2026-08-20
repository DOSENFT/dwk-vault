# Normalizer spec — raw Notta note → vault JSON

You are converting ONE raw Notta AI Note into one JSON file for a D&D campaign vault.

## Absolute rules

1. **Never invent content.** Every value must be traceable to the source file. If the
   source doesn't say it, the field is `null` or an empty array. A thin honest record
   beats a rich fabricated one. This vault's whole value is that it can be trusted.
2. **Timecodes.** Some source files carry `HH:MM:SS` marks; most do not. If an item
   has a timecode in the source, keep it as integer seconds in `t`. If it does not,
   `t` must be `null`. NEVER guess, interpolate, or estimate a timecode.
3. **Keep the source's own words** where possible. Compress, don't rewrite. Don't add
   drama the DM didn't create.
4. Proper nouns are sacred — copy character, NPC, place, faction and item names exactly
   as spelled in the source, even if spelling varies.

## The five cards

Every session gets exactly these five, in this order. They must work for a combat
session, an RP session, or a planning session alike. If a session genuinely has
nothing for a slot, set `headline` to null — do not pad it.

| key | means |
|---|---|
| `changed` | **What Changed** — the state of the world/party that is different now than at the start. A death, a pact, a location taken, a promise made, a secret out. |
| `learned` | **What We Learned** — the single most important piece of new knowledge, lore, or intel gained. |
| `who` | **Who Mattered** — the person (NPC or PC) this session turned on. Name them and say why. |
| `cost` | **What It Cost** — what was spent, lost, damaged, owed, or risked. Resources, HP, trust, time, a debt taken on. |
| `hanging` | **What's Still Hanging** — the sharpest unresolved question leaving this session. |

## Beats

Break the session into 8–24 beats in narrative order. A beat is a *moment*, not a
category. Merge facts from different parts of the note that describe the same moment.

`kind` must be one of: `scene`, `combat`, `magic`, `dread`, `lore`, `clue`, `item`,
`boss`, `reveal`, `rule`, `social`, `travel`, `plan`.

`facets` are the supporting details for that beat: `[["Label","text"]]`. Labels should
come from the source's own vocabulary where it has one (e.g. "New lore", "Major NPC",
"House ruling", "Item", "Check", "Combat", "Decision", "Environment", "Character").

## Output

Write ONE file: `/root/dnd-vault/data/json/<slug>.json`, valid JSON, this shape:

```json
{
  "slug": "", "title": "", "date": "", "runtime": "", "nottaId": "", "url": "",
  "template": "Auto | D&D Session Noters: V3 | General",
  "hasTimecodes": true,
  "durationSec": 0,
  "subtitle": "short evocative subtitle, max 8 words, from the material",
  "logline": "one sentence, max 30 words, what this session was",
  "recap": "the source's cinematic recap verbatim if it has one; otherwise a 3-5 sentence factual recap built only from stated events",
  "dm": null, "party": [], "opens": null, "closes": null,
  "cards": {
    "changed": {"headline": "", "detail": "", "t": null},
    "learned": {"headline": "", "detail": "", "t": null},
    "who":     {"headline": "", "detail": "", "t": null},
    "cost":    {"headline": "", "detail": "", "t": null},
    "hanging": {"headline": "", "detail": "", "t": null}
  },
  "beats": [{"t": null, "kind": "scene", "title": "", "line": "", "facets": [["",""]]}],
  "threads": [{"u": "hi|md|lo", "q": "", "t": null}],
  "next": [],
  "entities": [{"name": "", "kind": "npc|pc|faction|place|item|creature", "note": "", "t": null}],
  "gaps": ["anything the source was missing or truncated — be honest here"]
}
```

`durationSec` = the runtime in the front-matter converted to seconds.
`hasTimecodes` = true only if the source file actually contains `HH:MM:SS` marks.

Validate your JSON parses before finishing. Return only: `<slug> | <n beats> | <n with timecodes> | OK` or the problem.
