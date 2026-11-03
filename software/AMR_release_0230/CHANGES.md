# AMR-WATCH 0.23.0 (from 0.22.0; 0.22.0 from 0.21.0)
No detector, generator or threshold was changed. Version string 0.23.0.
Added (all display, validation and tests):
1. Alerts show, per detector, "ever signalled" and "signalling at the end of the window" (labels: Signal present at end of window / Crossed earlier, now back below limit / No signal).
2. Drill-down "Why this series is on the dashboard": the three detectors' states, and the dashboard conditions with numerators, denominators, proportions and the Wilson limit; notes on pooling, zero months and the empty-baseline rule.
3. Low-number warning shows the actual isolate count and threshold and says it is a limited-evidence warning.
4. Scenario panel: purpose, planted series, onset, size and ramp for each scenario; after "Reveal", alerts are matched to the planted truth (no effect on calculations).
5. Validation page: design box (datasets, series, months, baseline, evaluation, parameters, seeds) and the three denominators (dataset-level, series-level, window-level).
6. CSV panel: rejects and lists invalid rows (bad month, missing identifier, non-numeric, negative, r>n, non-integer, duplicate), refuses <24 months, reports empty baselines, shows both scorings (state at window end; as shipped) and explains exactly how a rise is planted.
7. Scope notice on the Trends page about the educational lab, identification and image modules.
8. Self-tests 80 -> 99 (baseline, each detector, one-sidedness, dashboard conditions, Wilson, exact binomial, seed reproducibility, planted-check regression 4/10, CSV validation, panel reproducibility).
Verified: planted-signal check unchanged (dashboard 32/60, 146 false alerts; CUSUM 60/1,934; two-of-three 60/1,550; EWMA 59/1,345; MA 41/928; count test 48/92); ARMD panel matches saved results for all 10 series, both scorings, 0 mismatches; 99/99 self-tests; offline reload; same seed -> same output.
Not done: export-versus-display check (the Trends page has no export); time-varying EWMA and two-sided CUSUM (would be new methods).
