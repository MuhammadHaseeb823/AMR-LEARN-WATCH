# Reproduction commands

Tested here with Python 3.11, Playwright with Chromium, and Node. The PyTorch reference table is stored (`software/validation/reference.csv`); PyTorch was not run again during testing.

## Unpack the suite
    unzip software/validation/suite_files.zip -d work/        # creates work/suite/
    cp software/validation/reference.csv software/validation/suite_manifest.csv work/
    # the scripts expect: work/reference.csv, work/suite_manifest.csv, work/suite/*.jpg|png
    # the model files are already beside the application in software/apps/ (amr_image_model.js, amr_image_model_crop.js)

## Software agreement (Paper 1, Section 3.7)
    python3 software/test_scripts/32_app_vs_reference.py --app software/apps/AMR-LEARN-0.21.0.html --suite work --out out_validation --model plate --latency-runs 5
Expected: 165 of 183 files reach the classifier; 165 of 165 top class and decision agree; largest absolute probability difference 0.0107; 111 answered, 54 abstained, 18 refused. Timing depends on the machine (6.5 s median here).
The run can take over an hour in a small container; `software/test_scripts/loop.sh` shows the retry-and-resume wrapper used.

## Behaviour tests (19) and feature tests (13 AMR-LEARN, 6 AMR-WATCH)
    python3 software/test_scripts/33_app_behaviour_tests.py --app software/apps/AMR-LEARN-0.21.0.html --image work/suite/A_kpn_0.jpg --invalid work/suite/C_random_bytes.jpg --out out_behaviour
    python3 software/test_scripts/35_new_feature_tests.py --learn software/apps/AMR-LEARN-0.21.0.html --watch software/apps/AMR-WATCH-0.21.0.html --answer-image work/suite/A_ses_0.jpg --abstain-image work/suite/A_aba_0.jpg --out out_features

## Paper 2 planted-signal check (page's own button)
Open AMR-WATCH-0.21.0.html, go to Trends, choose 60 datasets per scenario, 30% peak, medium speed, press "Run planted-signal check". Expected: dashboard rule 32 of 60 found, 146 false alerts (1.2 per dataset); count-based comparison 48 of 60, 92 false alerts.

## Paper 2 ablation (Section 3.6)
    cd paper2_watch/scripts
    node ablate.js '{"peak":0.30,"ramp":4}' ../results/abl_default.json     # also peak 0.15, 0.50
    python3 an2.py     # writes ablation.json (resampling datasets, 2000 times, seed 0)
    python3 fig_abl.py # makes Figure 6
`probe021.html` is AMR-WATCH 0.21.0 plus one line that exposes the generator and detectors (`window.__T`); apart from the two text and axis fixes of the final build it is identical to the shipped file (the detection code is unchanged). Scripts expect to be run from a folder holding `probe021.html`; adjust paths if needed.

## Paper 1 numbers
`paper1_classifier/scripts/metrics.py` (per-species metrics and balanced accuracy), `cal/*.py` (calibration, threshold bands), `35_paper_numbers.py` in the toolkit (cluster-bootstrap intervals over isolates, seed 0, 2000 resamples). Inputs are the per-fold prediction files, which are not yet in this archive.

## Paper 2 additional runs (Sections 3.6 and 3.7)
    cd paper2_watch/scripts
    node ablate2.js '{}' abl_indep.json '{"seedBase":50000,"seedMul":37,"N":60}'                       # new seeds, persistent rise
    node ablate2.js '{}' abl_outbreak.json '{"scenario":"outbreak","kind":"outbreak","N":60}'         # transient outbreak
    python3 an3.py        # dataset-level resampling intervals, both measures; writes extra_runs.json
    python3 fig_extra.py  # Figure 7
End-of-series measure = detector rule met by month 24; monitoring-period measure = rule met at the end of any of months 12 to 24. Detector and generator definitions: Paper 2 Supplementary Sections S1 and S2.

## Versions used for the final tests
Playwright with Chromium 153.0.8010.12; Linux 6.18 x86-64; Python 3.13; Node 22; two-core container, no GPU. PyTorch version of the stored reference table: not recorded.

## Second browser engine (to be run by a reader; not run by the authors yet)
The three test scripts take `--browser chromium|firefox|webkit`.
    pip install playwright && playwright install firefox webkit
    python3 software/test_scripts/33_app_behaviour_tests.py --app software/apps/AMR-LEARN-0.21.0.html --image work/suite/A_kpn_0.jpg --invalid work/suite/C_random_bytes.jpg --out out_behaviour_firefox --browser firefox
    python3 software/test_scripts/32_app_vs_reference.py --app software/apps/AMR-LEARN-0.21.0.html --suite work --out out_validation_firefox --model plate --latency-runs 3 --browser firefox
Expected if the application is portable: the same counts as Chromium (165 reached the classifier, 165 of 165 decisions agree) and 19 of 19 behaviour tests.

## Paper 2 real-data step (ARMD)
Download `microbiology_cultures_cohort.csv` (257 MB) from Dryad 10.5061/dryad.jq2bvq8kp and put it in a Google Drive. In Colab run `paper2_watch/scripts/colab/colab_cell_standalone.py` to make the monthly and yearly counts (`paper2_watch/results/monthly_ecoli_urine.csv`, `yearly_ecoli_urine.csv`). `colab_cell_E_full_dataflow.py` prints the Table 2 data flow (expected: 2,241,050 rows; 634,468 Null; 18,090 conflicting; 47,254 intermediate/synergism/inconclusive; 1,541,238 left, 16.78% resistant). `colab/gee_refit_exact_colab.py` re-fits the annual-trend GEE (statsmodels; independence working correlation).
Then, with Node: `node paper2_watch/scripts/real_ecoli_eval.js` and `real_ecoli_eval_current_state.js` (see the headers of those files for arguments).
