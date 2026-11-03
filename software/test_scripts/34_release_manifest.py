#!/usr/bin/env python3
"""Release manifest: SHA-256 and size of every file you name (app, model js files, checkpoints, suite, prediction files).
  python 34_release_manifest.py --label "paper2 frozen release" AMR-INTELLIGENCE-19.html amr_image_model.js amr_image_model_crop.js model.pt app_suite/reference.csv --out release_manifest.csv
Record the date and the app version next to it. Change a file and its hash changes; that is the point."""
import argparse, csv, hashlib, os, datetime
ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--out", default="release_manifest.csv"); ap.add_argument("--label", default="")
a = ap.parse_args(); stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["label", "file", "bytes", "sha256", "recorded"])
    for f in a.files:
        h = hashlib.sha256()
        with open(f, "rb") as g:
            for ch in iter(lambda: g.read(1 << 20), b""): h.update(ch)
        w.writerow([a.label, os.path.basename(f), os.path.getsize(f), h.hexdigest(), stamp]); print(h.hexdigest()[:16], os.path.basename(f))
