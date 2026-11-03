# Known limitations and open items (release 1.0)

## Evidence limits
- The offline model is a random-split-1 model (598 training photographs); the five-fold estimate describes the procedure, not this model.
- The software suite compares the application with a stored PyTorch run on photographs from the model's own dataset; it shows agreement, not accuracy. Decoded pixels and logits were not compared.
- One browser engine (headless Chromium), one machine type. The colony-crop model, other browsers, phones and large batches were not tested. Timings are machine-dependent.
- No usability study. No test on photographs from other laboratories apart from the two-class KACST test, which did not transfer.
- AMR-LEARN stays at 0.21.0, the build the validation covers. AMR-WATCH 0.22.0 and 0.23.0 were tested with their own self-tests (80 and 99 checks) and with parity runs against the analysis scripts, not with the 183-file image suite (they have no image page).
- Paper 2 uses synthetic data; its numbers describe the generator, not any hospital. The ARMD real-data analysis is one health system, one organism and specimen type, five antibiotics, with per-patient random date offsets (size not stated by the ARMD authors).

## Records that were recovered (2 November 2026) — see `RECOVERED_RECORDS_2026-11-02.md`
- Training settings and script (`paper1_classifier/scripts/05_image_finetune.py`), the KACST staging script and manifest, ARMD data-flow counts, and a re-fit of the Paper 2 GEE.

## Records that were NOT recovered
- Epochs, seed and device of the 72.2% run are not recorded in its result files (image size 224, pretrained, split sizes and date only). The notebooks of the same period call the cross-validation with 8 epochs and 224 px and the script default seed is 0, but the notebook was saved after the run, so these values are indicative, not proven. The run was on CPU by its timing.
- The original output of the Paper 2 GEE (software version and exact coding of time). A re-fit with an independence working correlation reproduces Table 4 of Paper 2 to within 0.0003.
- PyTorch version of the original reference run: re-checked on 2 November 2026 in a new session (torch 2.11.0+cpu, torchvision 0.26.0+cpu, Python 3.13.18); it may differ from the original session.
- Colab logs and a file-by-file map from every result file to its notebook cell. File dates are in `RECOVERED_RECORDS_2026-11-02.md`; file times are not an audit trail.
- Protocol file `PROTOCOL_external_test.txt` was saved 2026-10-25 15:59:49 (file time); result files of the three seeds 16:00:19, 16:00:30, 16:00:41; `kacst_optionB.zip` 16:06:01.

## Not in this repository
- Jilin photographs (except the 57 suite photographs and altered copies), any KACST photograph, the ARMD source files, training checkpoints other than the two model files.
