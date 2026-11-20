# Checks run on the version 1.0 interface files (19 November 2026)

- AMR-LEARN: the 183-file validation suite (in Zenodo release v1.0.0) was run on this file with the offline script. All files were handled with no page errors; 165 of 165 top-class agreements and 165 of 165 answer-rule agreements; maximum probability difference 0.0107; outcome per file identical to the stored run. In-app self-tests: 80 of 80.
- AMR-WATCH: the analysis script big_run.js (40 planted and 40 unplanted synthetic datasets, seed 7919) gave byte-identical output on the original AMR-WATCH 0.23.0 file and on this file. In-app self-tests: 99 of 99.
- Interface: page sweeps at phone and desktop widths without overflow or script errors; automated accessibility scan (axe-core, WCAG 2 A and AA, colour contrast) clean on the pages scanned.

These checks show that detector, rule and model behaviour is unchanged. They do not validate the pages added in the interface update, and no usability study was done. The original files and the scripts are in Zenodo release v1.0.0.
