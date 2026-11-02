
Repo: newbroman/Newborough_welllogger. Built against main at 1963868 (cache v11).

## Change
- Log tab: new strip under Well ID showing **Previous** and **Last year** for the
  selected well, in cm below pipe top (the entry unit, independent of the Wells-tab
  frame toggle), each labelled with its month.
- Once a depth is typed, a line gives the change against the previous reading
  ("▲ 12 cm higher than Sep 2026"), as a field check on entry slips.
- Previous = newest month before the round being logged, from the pipeline hub
  (`living/readings_living.csv`) or readings stored on the phone; on a tie the hub
  wins because it carries post-intake corrections. Phone-sourced values are marked
  "· phone".
- Last year = round month minus 12: hub, then phone, then hub within ±1 month
  (same tolerance as the Wells tab).
- Hub heads are converted with the app's upstand: depth bpt = upstand − head.
- sw.js cache v11 → v12.

## Implementation
- `logHistory()` added to the Wells/Exports module and exposed as `NW.logHistory`;
  called from the top of `updateWTE()` (well select, typing, Use nearest) and once
  after the feeds load.
- CSS `.hist-*` classes; markup `#logHist` inside the Well ID field.

## Verification
- All six script blocks pass `node --check`; no U+2003.
- `logHistory()` exercised against the live hub CSV (15,549 rows): CEH20 previous
  189 cm bpt = −(−1.78) + 0.11 m ✓; tie → hub; phone newer than hub → phone;
  unknown or empty well → strip hidden.
- Outstanding: on-phone check of layout and of the feed-load re-render.

## Provenance
Claude Opus 5.5 (claude-opus-5-5), claude.ai chat session, NRG rebuild project,
2026-11-02, against Newborough_welllogger main 1963868.
