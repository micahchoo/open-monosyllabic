---
scope: "oms/baseline.py"
tags: [statistics, honesty]
priority: 9
source: hand-written
---

# oms: "beyond chance" is a calibrated test — keep it one

Until 2026-10-01 `chance_bands` tested only meaning–shape pairs ALREADY seen in
2+ families and called a pair beyond chance when it beat 200 shuffles. That
selects on the outcome: on data shuffled to hold no real link it still passed
~260 pairs, and the catalog showed 323. The exact, FDR-controlled version
passes 4 (May, tea, /ma/ 'mother', /tu/ 'all').

- **Hypotheses are fixed before looking at the pairing.** A pair is tested if
  `MIN_COULD` families could share it — a property of each language's meanings
  and shapes, which the shuffle preserves. Never filter hypotheses on the
  observed count (independent filtering only).
- **Benjamini–Hochberg runs over every hypothesis**, observed or not
  (unobserved = p 1). The UI must say about 1 in 20 marks may still be chance.
- **Any change here re-runs `test_no_link_passes_almost_nothing`.** If null
  data passes more than a couple of pairs, the change is wrong.
- The heatmap ratio is a descriptive share among families whose PHOIBLE
  inventories could fill the cell. Never call it "chance".
