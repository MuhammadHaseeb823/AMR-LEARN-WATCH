# Release history (applications)
| Version | Notes | Software suite |
|---|---|---|
| 0.17.1 | earlier tested build | validated, see Paper 1 Table S1 |
| 0.19.0 | | validated |
| 0.20.0 | | 165/165 agreement; 19 behaviour tests |
| 0.21.0 | calibrated-confidence display, confusable-species view, design-a-test panel, run record (AMR-LEARN); count-based comparison, adjustable planted rise, Wilson intervals on sensitivity (AMR-WATCH); final patch: timing sentence made device-neutral, chart axis label | frozen a360645f... (LEARN), d805d515... (WATCH); identical decisions to 0.20.0 |
Hashes: see `software/apps/release_manifest_0210.csv`.
| AMR-WATCH 0.22.0 | CSV upload panel for real monthly counts | self-tests pass |
| AMR-WATCH 0.23.0 | state-at-window-end scoring, per-alert reasons, truth matching after Reveal, stricter CSV validation, scenario explanations; detector code unchanged from 0.21.0 | 99 of 99 self-tests pass; ARMD parity with the analysis scripts: 0 mismatches |
AMR-LEARN stays at 0.21.0, the build that Paper 1 validated. Hashes: `software/apps/release_manifest_0210.csv`, `software/AMR_release_0230/release_manifest_0230.csv`, and `SHA256SUMS.txt` at the top level.
