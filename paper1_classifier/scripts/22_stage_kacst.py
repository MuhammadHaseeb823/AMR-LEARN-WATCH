#!/usr/bin/env python3
"""Stage a SAMPLE of the KACST phone-photo datasets (Mendeley Data kx6gz3wmcf and v54x8jdx5x, CC BY 4.0) as an EXTERNAL TEST for a model
trained on the Jilin photographs. Nothing here trains anything.

  python 22_stage_kacst.py --zips /content/drive/MyDrive/mendeley_zips --list          # first look: what is inside, how it was read
  python 22_stage_kacst.py --zips /content/drive/MyDrive/mendeley_zips --out /content/kacst_ext --per-plate 3 --max-per-cell 150

Species are read from folder/file names (E. coli -> eco, K. pneumoniae -> kpn, S. aureus -> sau; the Jilin model's codes). P. aeruginosa is
NOT among the model's 19 classes, so it is counted and left out. Photos are grouped by the folder they sit in (taken to be one plate) and
written as  <out>/<agar>_<condition>/<code>/<code>-<plate>__<n>.jpg  (longer side <= 640 px, JPEG q92: the same preparation as training), so
07_external_test.py can be run once per agar x condition folder. CHECK the --list output: if the plate/species guess is wrong, say so and it is fixed.
"""
import argparse, os, re, io, zipfile, random, hashlib, collections, csv
from PIL import Image
p = argparse.ArgumentParser(); p.add_argument("--zips", required=True, help="folder holding the already-unzipped dataset folders (or the .zip files, or one .zip)")
p.add_argument("--out", default="kacst_ext"); p.add_argument("--list", action="store_true"); p.add_argument("--per-plate", type=int, default=3)
p.add_argument("--max-per-cell", type=int, default=150, help="max photos per species x agar x condition"); p.add_argument("--seed", type=int, default=12345)
a = p.parse_args(); random.seed(a.seed)
EXT = (".jpg", ".jpeg", ".png")
zs = [a.zips] if a.zips.lower().endswith(".zip") else (sorted(os.path.join(a.zips, f) for f in os.listdir(a.zips) if f.lower().endswith(".zip")) + sorted(os.path.join(a.zips, f) for f in os.listdir(a.zips) if os.path.isdir(os.path.join(a.zips, f))))
if not zs: raise SystemExit("No .zip files or folders found in " + a.zips)
def species(s):
    s = s.lower().replace("_", " ").replace("-", " ")
    if re.search(r"e\.? ?coli|escherichia\b.*coli|\becoli\b", s): return "eco"
    if re.search(r"k\.? ?pneu|klebsiella", s): return "kpn"
    if re.search(r"s\.? ?aureus|staph", s): return "sau"
    if re.search(r"p\.? ?aerug|pseudomonas", s): return "pae"
    return None
def condition(s):
    s = s.lower()
    if re.search(r"uncon|uncom|mixed", s): return "uncontrolled"   # 'uncomtrolled' is a typo in the record; 'mixed' folders are treated as uncontrolled
    return "controlled" if "control" in s else "unknown"
def agar(s):
    t = s.lower()
    if re.search(r"maccon|mccac|mac ?conkey|escherichia/group 1,2|image repository of escherichia", t) and not re.search(r"\bbh\b|brain", t): return "MAC"
    if re.search(r"\bbh\b|bhi|brain", t): return "BHI"
    return "unknown"
def plate_of(path):
    m = re.search(r"plate\s*(\d+)", path, re.I); return m.group(1) if m else None
rows = []; skipped = collections.Counter()
def add(src, name, rel):
    if not name.lower().endswith(EXT) or "__MACOSX" in rel: return
    sp = species(rel); pn = plate_of(rel)
    grp = re.search(r"group ?(\d)", rel, re.I); grp = grp.group(1) if grp else "?"
    ag = agar(rel)
    rows.append(dict(src=src, name=name, rel=rel, sp=sp, cond=condition(rel), agar=ag, plate=f"{grp}-{sp}-{ag}-{pn}" if pn else None))
    if sp is None: skipped["species not recognised"] += 1
    if pn is None: skipped["no 'Plate N' in path (left out)"] += 1
for z in zs:
    if os.path.isdir(z):
        for dp, _, fs in os.walk(z):
            for f in fs: add(("dir", os.path.join(dp, f)), f, os.path.relpath(os.path.join(dp, f), z).replace(os.sep, "/"))
    else:
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist(): add(("zip", z, n), n.split("/")[-1], os.path.basename(z) + "/" + n)
print(f"{len(rows)} photos in {len(zs)} zip(s)/folder(s)")
tab = collections.Counter((r["sp"], r["agar"], r["cond"]) for r in rows)
print("species x agar x condition (photos):")
for k, v in sorted(tab.items(), key=lambda kv: str(kv[0])): print("  ", k, v)
plates = collections.Counter(r["plate"] for r in rows if r["plate"]); print("distinct folders treated as plates:", len(plates))
print("example paths:"); [print("  ", r["rel"], "->", r["sp"], r["agar"], r["cond"], r["plate"]) for r in random.sample(rows, min(8, len(rows)))]
if skipped: print("not recognised:", dict(skipped))
if a.list: raise SystemExit(0)
os.makedirs(a.out, exist_ok=True)
by = collections.defaultdict(list)
for r in rows:
    if r["sp"] in ("eco", "kpn", "sau") and r["plate"]: by[(r["agar"], r["cond"], r["sp"], r["plate"])].append(r)
cells = collections.defaultdict(list)
for (ag, co, sp, pl), rs in by.items():
    random.shuffle(rs); cells[(ag, co, sp)] += [(pl, r) for r in rs[: a.per_plate]]
man = []; zcache = {}
for (ag, co, sp), items in sorted(cells.items()):
    random.shuffle(items); items = items[: a.max_per_cell]
    d = os.path.join(a.out, f"{ag}_{co}", sp); os.makedirs(d, exist_ok=True)
    seen = set(); i = -1
    for pl, r in items:
        src = r["src"]
        if src[0] == "dir": data = open(src[1], "rb").read()
        else:
            zf = zcache.get(src[1]) or zcache.setdefault(src[1], zipfile.ZipFile(src[1])); data = zf.read(src[2])
        hh = hashlib.md5(data).hexdigest()
        if hh in seen: continue            # the same file sits in more than one folder in some plates
        seen.add(hh); i += 1
        try: im = Image.open(io.BytesIO(data)).convert("RGB")
        except Exception: continue
        w, h = im.size; m = max(w, h)
        if m > 640: im = im.resize((round(w * 640 / m), round(h * 640 / m)), Image.BICUBIC)
        pid = hashlib.md5(pl.encode()).hexdigest()[:6]; fn = f"{sp}-{pid}__{i}.jpg"; im.save(os.path.join(d, fn), "JPEG", quality=92)
        man.append([os.path.join(f"{ag}_{co}", sp, fn), str(src[1]), r["rel"], sp, ag, co, pl])
with open(os.path.join(a.out, "kacst_staging_manifest.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["staged", "source", "original_path", "species_code", "agar", "condition", "plate_folder"]); w.writerows(man)
print(f"staged {len(man)} photos in {len(cells)} cells under {a.out}")
for dd in sorted(os.listdir(a.out)):
    if os.path.isdir(os.path.join(a.out, dd)): print("  run:  python 07_external_test.py --model <model.pt> --images", os.path.join(a.out, dd), "--out results_ext_" + dd)
