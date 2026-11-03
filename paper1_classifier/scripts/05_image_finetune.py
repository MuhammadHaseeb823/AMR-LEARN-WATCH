#!/usr/bin/env python3
"""Image classification by fine-tuning a small pretrained network (colony crops, Gram stains, ...). Research only.
Use a GPU on Colab (Runtime > Change runtime type > GPU). A CPU works for small sets but is slow.

Folder layout, one folder per class:   images/<class_name>/<files>
  python 05_image_finetune.py --images crops --epochs 8
  python 05_image_finetune.py --images crops --epochs 8 --shuffle-labels   # CONTROL: must score about chance

GROUPS: files that come from the same plate or slide must stay on the same side of the split, or accuracy is inflated.
A file name like  12__345.jpg  is grouped by the part before '__' (06_colony_crops.py names crops that way).
Otherwise trailing digits are removed from the file name to form the group; check this suits your names.
The script stops if a group appears on both sides.
"""
import argparse, os, re, random, collections
import numpy as np
import torch, torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
from amrtrain import common as C

p = argparse.ArgumentParser(); p.add_argument("--images", required=True); p.add_argument("--epochs", type=int, default=8)
p.add_argument("--batch", type=int, default=32); p.add_argument("--out", default="results"); p.add_argument("--seed", type=int, default=0)
p.add_argument("--min-per-class", type=int, default=30); p.add_argument("--max-per-class", type=int, default=1500)
p.add_argument("--size", type=int, default=160); p.add_argument("--no-pretrained", action="store_true", help="skip downloading pretrained weights (tests only)")
p.add_argument("--save-model", action="store_true", help="save the trained network (model.pt) so 07_external_test.py can score other photos with it")
p.add_argument("--stratify-groups", action="store_true", help="split the groups of each class separately so every class has groups in train, validation and test (use when each group holds one class)")
p.add_argument("--shuffle-labels", action="store_true", help="control: shuffle training labels; test accuracy must be about chance")
p.add_argument("--n-folds", type=int, default=0, help="isolate-level cross-validation with --stratify-groups: split each class's groups into N folds so every group is tested exactly once")
p.add_argument("--fold", type=int, default=0, help="which fold (0 to N-1) to use as the test set when --n-folds is given")
a = p.parse_args(); random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
classes = sorted(d for d in os.listdir(a.images) if os.path.isdir(os.path.join(a.images, d)))
items = []
for c in classes:
    fs = sorted(f for f in os.listdir(os.path.join(a.images, c)) if f.lower().endswith(EXT))
    random.Random(a.seed).shuffle(fs); fs = fs[: a.max_per_class]
    if len(fs) >= a.min_per_class: items += [(os.path.join(a.images, c, f), c) for f in fs]
    else: print(f"Dropping class '{c}': only {len(fs)} images (minimum {a.min_per_class}).")
classes = sorted({c for _, c in items}); idx = {c: i for i, c in enumerate(classes)}
if len(classes) < 2: C.die("Fewer than 2 classes with enough images.")
def group_of(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.split("__")[0] if "__" in stem else re.sub(r"[-_ ]?\d+$", "", stem)
groups = sorted({group_of(x[0]) for x in items}); random.Random(a.seed).shuffle(groups)
n_te = max(1, len(groups) // 5); n_va = max(1, len(groups) // 8)
te_g = set(groups[:n_te]); va_g = set(groups[n_te:n_te + n_va])
if a.stratify_groups:
    g2c = collections.defaultdict(set)
    for f, c in items: g2c[group_of(f)].add(c)
    if any(len(v) > 1 for v in g2c.values()): C.die("--stratify-groups needs every group to hold one class only.")
    te_g, va_g = set(), set()
    if a.n_folds:
        if not 0 <= a.fold < a.n_folds: C.die("--fold must be between 0 and --n-folds minus 1.")
        for c in classes:
            gs = sorted(g for g, v in g2c.items() if c in v); random.Random(12345).shuffle(gs)   # one fixed order for every fold, so the folds do not overlap
            fold_of = {g: i % a.n_folds for i, g in enumerate(gs)}   # round-robin: each group lands in exactly one fold
            te_g |= {g for g in gs if fold_of[g] == a.fold}; va_g |= {g for g in gs if fold_of[g] == (a.fold + 1) % a.n_folds}
    else:
      for c in classes:
        gs = sorted(g for g, v in g2c.items() if c in v); random.Random(a.seed).shuffle(gs)
        nt = max(1, round(len(gs) * 0.2)); nv = max(1, round(len(gs) * 0.125)); te_g |= set(gs[:nt]); va_g |= set(gs[nt:nt + nv])
part = lambda path: "test" if group_of(path) in te_g else "val" if group_of(path) in va_g else "train"
tr = [(f, c) for f, c in items if part(f) == "train"]; va = [(f, c) for f, c in items if part(f) == "val"]; te = [(f, c) for f, c in items if part(f) == "test"]
assert not ({group_of(f) for f, _ in tr} & {group_of(f) for f, _ in te}), "a group appears in both train and test"
print(f"{len(classes)} classes; groups: {len(groups)}; train {len(tr)} | val {len(va)} | test {len(te)}")
if len(te) < 100: print("WARNING: fewer than 100 test images; the intervals will be wide.")
if len({c for _, c in te}) < 2: C.die("The test set contains one class only; there are too few groups. Use more plates or slides.")
if a.shuffle_labels:
    labs = [c for _, c in tr]; random.Random(1).shuffle(labs); tr = [(f, c) for (f, _), c in zip(tr, labs)]; print("CONTROL RUN: training labels shuffled.")
norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]); s = a.size
t_train = transforms.Compose([transforms.Resize((s, s)), transforms.RandomHorizontalFlip(), transforms.RandomVerticalFlip(), transforms.ColorJitter(0.1, 0.1), transforms.ToTensor(), norm])
t_eval = transforms.Compose([transforms.Resize((s, s)), transforms.ToTensor(), norm])
class DS(Dataset):
    def __init__(s, it, tf): s.it, s.tf = it, tf
    def __len__(s): return len(s.it)
    def __getitem__(s, i): return s.tf(Image.open(s.it[i][0]).convert("RGB")), idx[s.it[i][1]]
dev = "cuda" if torch.cuda.is_available() else "cpu"; print("Running on", dev)
net = models.resnet18(weights=None if a.no_pretrained else models.ResNet18_Weights.DEFAULT); net.fc = nn.Linear(net.fc.in_features, len(classes)); net.to(dev)
opt = torch.optim.AdamW(net.parameters(), lr=3e-4); lossf = nn.CrossEntropyLoss()
def run(it, tf, train):
    net.train(train); P, Y = [], []
    for x, y in DataLoader(DS(it, tf), batch_size=a.batch, shuffle=train):
        x, y = x.to(dev), y.to(dev)
        with torch.set_grad_enabled(train):
            o = net(x)
            if train: opt.zero_grad(); lossf(o, y).backward(); opt.step()
        P.append(torch.softmax(o, 1).detach().cpu().numpy()); Y.append(y.cpu().numpy())
    return np.vstack(P), np.concatenate(Y)
best, state = -1, None
for ep in range(a.epochs):
    run(tr, t_train, True)
    if va:
        P, Y = run(va, t_eval, False); acc = float((P.argmax(1) == Y).mean()); print(f"epoch {ep + 1}: validation accuracy {acc:.3f}")
        if acc > best: best, state = acc, {k: v.clone() for k, v in net.state_dict().items()}
if state: net.load_state_dict(state)
if a.save_model:
    os.makedirs(a.out, exist_ok=True); torch.save({"state": net.state_dict(), "classes": classes, "size": s}, os.path.join(a.out, "model.pt")); print("Saved", os.path.join(a.out, "model.pt"))
P, Y = run(te, t_eval, False); pred = P.argmax(1); ok = pred == Y; lo, hi = C.wilson(int(ok.sum()), len(ok))
# Colonies from one plate are not independent, so resample whole PLATES (groups) for the honest interval.
te_groups = np.array([group_of(f) for f, _ in te]); ug = sorted(set(te_groups)); rng = np.random.default_rng(0); by = {g: np.where(te_groups == g)[0] for g in ug}; boots = []
for _ in range(1000):
    pick = rng.integers(0, len(ug), len(ug)); ii = np.concatenate([by[ug[k]] for k in pick]); boots.append(ok[ii].mean())
glo, ghi = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
pg = np.array([ok[by[g]].mean() for g in ug]); gw = float(pg.mean()); gb = []
for _ in range(1000): gb.append(pg[rng.integers(0, len(pg), len(pg))].mean())  # every held-out group counts once, however many photos it has
train_counts = np.bincount([idx[c] for _, c in tr], minlength=len(classes)); lazy = max(float((Y == train_counts.argmax()).mean()), float(np.bincount(Y).max() / len(Y)))  # strictest lazy guess: train-majority or test-majority class
per = []
for c in sorted(set(Y)):
    m = Y == c; per.append({"class": classes[c], "n_test": int(m.sum()), "sensitivity": round(float(ok[m].mean()), 3), "ci95": [round(x, 3) for x in C.wilson(int(ok[m].sum()), int(m.sum()))]})
per.sort(key=lambda r: r["sensitivity"])
conf = {}
for t_, q in zip(Y[~ok], pred[~ok]): conf[(classes[t_], classes[q])] = conf.get((classes[t_], classes[q]), 0) + 1
res = {"task": "image classification (fine-tuned resnet18)" + (" [SHUFFLED-LABEL CONTROL]" if a.shuffle_labels else ""), "data": a.images, "pretrained": not a.no_pretrained, "n_classes": len(classes),
       "n_train": len(tr), "n_test": int(len(Y)), "groups_held_out_for_test": len(te_g), "image_size": s,
       "top1_accuracy": {"value": round(float(ok.mean()), 3), "ci95_resampling_whole_plates": [round(glo, 3), round(ghi, 3)], "ci95_if_images_were_independent_TOO_NARROW": [round(lo, 3), round(hi, 3)]},
       "group_weighted_accuracy": {"value": round(gw, 3), "ci95_resampling_groups": [round(float(np.percentile(gb, 2.5)), 3), round(float(np.percentile(gb, 97.5)), 3)], "n_test_groups": len(ug), "note": "each held-out group (plate or set of near-copies) counts once"},
       "n_train_groups": len({group_of(f) for f, _ in tr}), "cv_fold": (a.fold if a.n_folds else None), "cv_n_folds": (a.n_folds or None),
       "lazy_baseline_accuracy_most_common_class": round(lazy, 3), "chance_accuracy": round(1 / len(classes), 3), "beats_lazy_baseline": bool(ok.mean() > lazy),
       "clearly_above_chance_and_lazy": bool(glo > max(lazy, 1 / len(classes))),
       "ece_of_confidence": C.ece(ok.astype(int), P.max(1)), "weakest_classes": per[:8],
       "common_confusions": [{"true": t_, "predicted": q, "count": n} for (t_, q), n in sorted(conf.items(), key=lambda kv: -kv[1])[:8]],
       "caveats": ["whole plates or slides held out; check the grouping suits your file names", "one source of photos: expect worse results on other cameras, media or labs", "research only; not a diagnostic tool"]}
os.makedirs(a.out, exist_ok=True)
C.write_app_predictions(os.path.join(a.out, "image_predictions_for_app.csv"), [classes[i] for i in Y], [classes[i] for i in pred], P.max(1), groups=list(te_groups))
C.finish(a.out, "image_finetune" + ("_CONTROL" if a.shuffle_labels else ""), res)
