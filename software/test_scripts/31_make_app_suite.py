#!/usr/bin/env python3
"""Build the LOCKED app test suite (paper 2) and its PyTorch reference outputs.
  python 31_make_app_suite.py --images /content/staged_jilin --model results_jilin_with_model/model.pt --out app_suite --per-class 3 --seed 2026
Groups: A supported photographs (fixed number per species, seeded); B the same photographs altered (rotated, PNG, grey, RGBA, large, low JPEG quality);
C invalid files (empty, corrupt, truncated, wrong content, wrong type); D out-of-scope pictures (synthetic, no species is correct).
Reference = the saved PyTorch checkpoint, torchvision preprocessing (longest side limited to 640 px, resize to the model size, ImageNet normalisation),
three views (as taken, horizontal flip, vertical flip). Writes suite/, reference.csv, suite_manifest.csv. Freeze the folder; do not edit it after the first app run."""
import argparse, os, random, shutil, csv, hashlib, io
import numpy as np
from PIL import Image, ImageDraw
import torch, torch.nn as nn, torch.nn.functional as F
from torchvision import models, transforms
ap = argparse.ArgumentParser(); ap.add_argument("--images", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--out", default="app_suite"); ap.add_argument("--per-class", type=int, default=3); ap.add_argument("--seed", type=int, default=2026)
a = ap.parse_args(); rnd = random.Random(a.seed); np.random.seed(a.seed)
EXT = (".jpg", ".jpeg", ".png")
S = os.path.join(a.out, "suite"); shutil.rmtree(a.out, ignore_errors=True); os.makedirs(S)
ck = torch.load(a.model, map_location="cpu"); classes = ck["classes"]; size = ck["size"]
net = models.resnet18(weights=None); net.fc = nn.Linear(net.fc.in_features, len(classes)); net.load_state_dict(ck["state"]); net.eval()
T = transforms.Compose([transforms.Resize((size, size)), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
def ref_views(path):
    im = Image.open(path).convert("RGB"); s = 640 / max(im.size)
    if s < 1: im = im.resize((round(im.size[0] * s), round(im.size[1] * s)))
    x = T(im)[None]
    with torch.no_grad(): return [F.softmax(net(v), 1)[0].numpy() for v in (x, torch.flip(x, [3]), torch.flip(x, [2]))]
rows = []
def add(cat, fname, expected, note=""): rows.append(dict(file=fname, category=cat, expected=expected, note=note, sha256=hashlib.sha256(open(os.path.join(S, fname), "rb").read()).hexdigest()))
base = []
for c in classes:
    fs = sorted(f for f in os.listdir(os.path.join(a.images, c)) if f.lower().endswith(EXT)); rnd.shuffle(fs)
    for k, f in enumerate(fs[: a.per_class]):
        fn = f"A_{c}_{k}.jpg"; Image.open(os.path.join(a.images, c, f)).convert("RGB").save(os.path.join(S, fn), quality=95); add("A", fn, "predict", f"source {c}/{f}"); base.append(fn)
# B: altered versions of a seeded subset of A (one per species)
sub = [b for b in base if b.endswith("_0.jpg")]
for b in sub:
    im = Image.open(os.path.join(S, b)); stem = b[:-4].replace("A_", "B_")
    im.rotate(90, expand=True).save(os.path.join(S, stem + "_rot90.jpg"), quality=95); add("B", stem + "_rot90.jpg", "predict", "rotated 90 degrees (portrait)")
    im.save(os.path.join(S, stem + "_png.png")); add("B", stem + "_png.png", "predict", "lossless PNG copy")
    im.convert("L").save(os.path.join(S, stem + "_grey.jpg"), quality=95); add("B", stem + "_grey.jpg", "predict", "single-channel greyscale JPEG")
    im.convert("RGBA").save(os.path.join(S, stem + "_rgba.png")); add("B", stem + "_rgba.png", "predict", "RGBA PNG, opaque")
    big = im.convert("RGB").resize((im.size[0] * 4, im.size[1] * 4), Image.BICUBIC); big.save(os.path.join(S, stem + "_big.jpg"), quality=92); add("B", stem + "_big.jpg", "predict", "upscaled x4 (large photograph)")
    im.convert("RGB").save(os.path.join(S, stem + "_q35.jpg"), quality=35); add("B", stem + "_q35.jpg", "predict", "strong JPEG compression (quality 35)")
# C: invalid
good = open(os.path.join(S, base[0]), "rb").read()
inv = {"C_empty.jpg": b"", "C_random_bytes.jpg": bytes(np.random.randint(0, 256, 5000, dtype=np.uint8)), "C_truncated.jpg": good[: len(good) // 3],
       "C_text_named_jpg.jpg": b"this is not an image\n" * 50, "C_notes.txt": b"plain text file\n", "C_document.pdf": b"%PDF-1.4\n%%EOF\n"}
for fn, b in inv.items(): open(os.path.join(S, fn), "wb").write(b); add("C", fn, "reject_or_clear_error")
Image.fromarray(np.tile(np.linspace(0, 255, 9000, dtype=np.uint8), (6000, 1))).save(os.path.join(S, "C_huge_9000x6000.png")); add("C", "C_huge_9000x6000.png", "reject_or_clear_error", "9000 x 6000 pixels")
Image.new("RGB", (4, 4), (200, 40, 40)).save(os.path.join(S, "C_tiny_4x4.png")); add("C", "C_tiny_4x4.png", "reject_or_clear_error", "4 x 4 pixels")
# D: out of scope (synthetic)
r = np.random.default_rng(a.seed)
Image.new("RGB", (600, 600), (128, 128, 128)).save(os.path.join(S, "D_grey.png")); add("D", "D_grey.png", "any_documented", "uniform grey")
Image.fromarray((r.random((600, 600, 3)) * 255).astype("uint8")).save(os.path.join(S, "D_noise.png")); add("D", "D_noise.png", "any_documented", "random noise")
g = np.zeros((600, 600, 3), np.uint8); g[..., 0] = np.linspace(0, 255, 600)[None, :]; g[..., 2] = np.linspace(255, 0, 600)[:, None]
Image.fromarray(g).save(os.path.join(S, "D_gradient.png")); add("D", "D_gradient.png", "any_documented", "colour gradient")
im = Image.new("RGB", (600, 600), "white"); d = ImageDraw.Draw(im); d.text((40, 280), "NOT A CULTURE PLATE " * 2, fill="black"); im.save(os.path.join(S, "D_text.png")); add("D", "D_text.png", "any_documented", "text on white")
# reference for everything that decodes
with open(os.path.join(a.out, "reference.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["file", "category", "decodes"] + [f"mean_{c}" for c in classes] + ["ref_top", "ref_mean_conf", "ref_views_agree", "ref_answers"] + [f"v{v}_{c}" for v in range(3) for c in classes])
    for r_ in rows:
        try: V = ref_views(os.path.join(S, r_["file"]))
        except Exception: w.writerow([r_["file"], r_["category"], 0] + [""] * (len(classes) * 4 + 4)); continue
        m = sum(V) / 3; tops = [int(v.argmax()) for v in V]; agree = len(set(tops)) == 1
        w.writerow([r_["file"], r_["category"], 1] + [f"{x:.6f}" for x in m] + [classes[int(m.argmax())], f"{m.max():.6f}", int(agree), int(agree and m.max() >= 0.9)] + [f"{x:.6f}" for v in V for x in v])
with open(os.path.join(a.out, "suite_manifest.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "files:", {k: sum(1 for r_ in rows if r_["category"] == k) for k in "ABCD"}, "| classes", len(classes), "| seed", a.seed)
print("Freeze this folder now (copy it to Drive, note the date). Do not change it after the first app run.")
