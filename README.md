# AMR-LEARN and AMR-WATCH: offline teaching applications, validation package and analysis code

**Research and teaching use only. Not for clinical diagnosis, prescribing or real surveillance reporting. No patient data are included.**

This repository supports two papers by Tariq MH, Price C, Ammoun M, Amir A and Tariq MM.

| Paper | Subject | Folders |
|---|---|---|
| 1 | Isolate-held-out evaluation of colony-image species classification (five-fold cross-validation over isolates, shortcut controls, an external test) and software validation of the offline application AMR-LEARN 0.21.0 | `paper1_classifier/`, `software/` |
| 2 | AMR-WATCH: evaluating trend-detection methods for antimicrobial resistance on synthetic surveillance data and real-world microbiology records (ARMD) | `paper2_watch/`, `software/` |

## Run the applications (no installation, no internet needed)
1. Download this repository (green **Code** button, then **Download ZIP**) and unzip it.
2. Open the folder `software/apps/`.
3. Double-click `AMR-LEARN-0.21.0.html` or `AMR-WATCH-0.23.0.html`. They open in your browser (Chrome tested).
4. AMR-LEARN's image page needs `amr_image_model.js` in the same folder as the HTML file. Do not move or rename it.
5. Nothing is uploaded anywhere. Everything runs on your computer.

## What is where
- `software/apps/` the applications (single HTML files) and the two model files. AMR-LEARN 0.21.0 is the validated build. AMR-WATCH 0.21.0, 0.22.0 and 0.23.0 are all included; 0.23.0 is the final one. Hashes are in `release_manifest_0210.csv` and `../AMR_release_0230/release_manifest_0230.csv`.
- `software/validation/` the 183-file suite manifest, the stored PyTorch reference table, the suite photographs (`suite_files.zip`), and the final results of the three test scripts on the frozen build.
- `software/test_scripts/` the test scripts (32 reference comparison, 33 behaviour tests, 35 feature tests) and the manifest script.
- `software/AMR_release_0230/` change notes and differences between AMR-WATCH versions.
- `paper1_classifier/` per-photograph predictions of every fold, summaries, tables, the analysis scripts, the training script (`05_image_finetune.py`), the external-test script, the KACST staging script and its manifest.
- `paper2_watch/` result files (JSON, monthly and yearly ARMD counts), the analysis scripts, and the Colab cells used for the ARMD data (`scripts/colab/`).
- `docs/` reproduction commands, known limitations, records recovered, release history.
- `LICENSE`, `LICENSES.md`, `CITATION.cff`, `SHA256SUMS.txt` (hash of every file).

## Check the files
Run `sha256sum -c SHA256SUMS.txt` (Linux/macOS) or `certutil -hashfile <file> SHA256` (Windows) and compare. Expected: AMR-LEARN-0.21.0.html `a360645f…`, `amr_image_model.js` `358462a2…`, `amr_image_model_crop.js` `03496cff…`.

## Not in this repository
The Jilin photographs (get them from Zenodo 10.5281/zenodo.18256864, version 2, CC BY 4.0; only the suite photographs are included), any KACST photograph (Mendeley Data 10.17632/kx6gz3wmcf.1 and 10.17632/v54x8jdx5x.1), the ARMD source files (Dryad 10.5061/dryad.jq2bvq8kp), and training checkpoints other than the two model files. See `docs/KNOWN_LIMITATIONS.md` for the evidence limits and for what could not be recovered.

## Cite
See `CITATION.cff` (GitHub shows a "Cite this repository" button). Please also cite the datasets above.
