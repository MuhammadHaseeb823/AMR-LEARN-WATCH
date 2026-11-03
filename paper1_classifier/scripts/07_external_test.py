#!/usr/bin/env python3
"""Score a SAVED model on a DIFFERENT set of colony crops (an external test). No training happens here.

  python 05_image_finetune.py --images crops --save-model --out results_images      (once, makes results_images/model.pt)
  python 07_external_test.py --model results_images/model.pt --images other_crops --out results_external

--images is a folder of class sub-folders, exactly like the training crops. Class folder names must match the names the model
was trained on (sp01 ...). Classes the model does not know are left out and listed; a class the second set lacks is simply not scored.
Crop file names like  12__345.jpg  keep colonies of one plate together for the plate-level interval.
Reports accuracy with a whole-plate interval, the strict lazy baseline, per-class sensitivity, confusions and calibration.
An external result is usually LOWER than the internal one. Report it anyway.
"""
import argparse, os, re
import numpy as np
import torch, torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
from amrtrain import common as C

p = argparse.ArgumentParser(); p.add_argument("--model", required=True); p.add_argument("--images", required=True)
p.add_argument("--out", default="results_external"); p.add_argument("--batch", type=int, default=64); p.add_argument("--max-per-class", type=int, default=1500)
a = p.parse_args()
ck = torch.load(a.model, map_location="cpu"); classes = ck["classes"]; s = ck["size"]; idx = {c: i for i, c in enumerate(classes)}
EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
folders = sorted(d for d in os.listdir(a.images) if os.path.isdir(os.path.join(a.images, d)))
known = [d for d in folders if d in idx]; unknown = [d for d in folders if d not in idx]
if not known: C.die("None of the class folders in --images match the model's classes. The model knows: " + ", ".join(classes[:30]) + ". Folders found: " + ", ".join(folders[:30]) + ". Rename the folders or use a model trained on the same class names.")
if unknown: print("Left out (the model does not know these classes):", unknown)
items = []
for c in known:
    fs = sorted(f for f in os.listdir(os.path.join(a.images, c)) if f.lower().endswith(EXT))[: a.max_per_class]
    items += [(os.path.join(a.images, c, f), c) for f in fs]
if len(items) < 50: C.die(f"Only {len(items)} usable crops found; an external test needs a few hundred at least.")
def group_of(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.split("__")[0] if "__" in stem else re.sub(r"[-_ ]?\d+$", "", stem)
norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]); tf = transforms.Compose([transforms.Resize((s, s)), transforms.ToTensor(), norm])
class DS(Dataset):
    def __len__(self): return len(items)
    def __getitem__(self, i): return tf(Image.open(items[i][0]).convert("RGB")), idx[items[i][1]]
dev = "cuda" if torch.cuda.is_available() else "cpu"; print("Running on", dev, "|", len(items), "crops,", len(known), "classes")
net = models.resnet18(weights=None); net.fc = nn.Linear(net.fc.in_features, len(classes)); net.load_state_dict(ck["state"]); net.to(dev).eval()
P, Y = [], []
with torch.no_grad():
    for x, y in DataLoader(DS(), batch_size=a.batch):
        P.append(torch.softmax(net(x.to(dev)), 1).cpu().numpy()); Y.append(y.numpy())
P, Y = np.vstack(P), np.concatenate(Y); pred = P.argmax(1); ok = pred == Y; lo, hi = C.wilson(int(ok.sum()), len(ok))
groups = np.array([group_of(f) for f, _ in items]); ug = sorted(set(groups)); rng = np.random.default_rng(0); by = {g: np.where(groups == g)[0] for g in ug}; boots = []
for _ in range(1000):
    pick = rng.integers(0, len(ug), len(ug)); ii = np.concatenate([by[ug[k]] for k in pick]); boots.append(ok[ii].mean())
glo, ghi = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
lazy = float(np.bincount(Y).max() / len(Y)); chance = 1 / len(known)
per = []
for c in sorted(set(Y)):
    m = Y == c; per.append({"class": classes[c], "n_test": int(m.sum()), "sensitivity": round(float(ok[m].mean()), 3), "ci95": [round(x, 3) for x in C.wilson(int(ok[m].sum()), int(m.sum()))]})
per.sort(key=lambda r: r["sensitivity"])
conf = {}
for t_, q in zip(Y[~ok], pred[~ok]): conf[(classes[t_], classes[q])] = conf.get((classes[t_], classes[q]), 0) + 1
res = {"task": "EXTERNAL TEST of a saved resnet18 (no retraining)", "model": a.model, "data": a.images, "n_crops": int(len(Y)), "n_plate_groups": len(ug), "classes_scored": len(set(Y)), "classes_left_out_unknown_to_model": unknown,
       "top1_accuracy": {"value": round(float(ok.mean()), 3), "ci95_resampling_whole_plates": [round(glo, 3), round(ghi, 3)], "ci95_if_images_were_independent_TOO_NARROW": [round(lo, 3), round(hi, 3)]},
       "lazy_baseline_accuracy_most_common_class": round(lazy, 3), "chance_accuracy": round(chance, 3), "clearly_above_chance_and_lazy": bool(glo > max(lazy, chance)),
       "ece_of_confidence": C.ece(ok.astype(int), P.max(1)), "weakest_classes": per[:8], "all_classes": per,
       "common_confusions": [{"true": t_, "predicted": q, "count": n} for (t_, q), n in sorted(conf.items(), key=lambda kv: -kv[1])[:8]],
       "caveats": ["a different photo set from training: compare with the internal result and report both", "plate grouping comes from file names; check it suits them", "research only; not a diagnostic tool"]}
os.makedirs(a.out, exist_ok=True)
C.write_app_predictions(os.path.join(a.out, "external_predictions_for_app.csv"), [classes[i] for i in Y], [classes[i] for i in pred], P.max(1), groups=list(groups))
C.finish(a.out, "external_test", res)
