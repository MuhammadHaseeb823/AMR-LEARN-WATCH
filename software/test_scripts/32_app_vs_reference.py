#!/usr/bin/env python3
"""Run the LOCKED suite (31_make_app_suite.py) through the offline app in a headless browser and compare with the PyTorch reference.
  pip install playwright && playwright install chromium
  python 32_app_vs_reference.py --app AMR-INTELLIGENCE-18.html --suite app_suite --out app_report [--model plate|crop] [--latency-runs 5]
The app page must sit in the same folder as amr_image_model.js (and amr_image_model_crop.js). Nothing is uploaded anywhere.
Per file it records: outcome (answered / abstained / rejected by the quality check / error), the three-view probabilities seen by the app,
agreement with the reference (top class per view, largest and mean absolute probability difference, answer/abstain rule), time to answer.
Also: class-order check, repeatability (same photograph N times), latency (median, IQR), page errors. Research use only."""
import argparse, csv, json, os, time, hashlib, statistics
import numpy as np
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('--browser', default='chromium', choices=['chromium','firefox','webkit']); ap.add_argument("--app", required=True); ap.add_argument("--suite", required=True); ap.add_argument("--out", default="app_report")
ap.add_argument("--model", default="plate"); ap.add_argument("--latency-runs", type=int, default=5); ap.add_argument("--wait-ms", type=int, default=3500); ap.add_argument("--budget-s", type=float, default=0, help="stop after this many seconds and exit 3; run again to resume from out/checkpoint.jsonl (0 = no limit)")
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
ref = {}; rows = list(csv.DictReader(open(os.path.join(a.suite, "reference.csv"))))
classes = [k[5:] for k in rows[0] if k.startswith("mean_")]
for r in rows: ref[r["file"]] = r
man = {r["file"]: r for r in csv.DictReader(open(os.path.join(a.suite, "suite_manifest.csv")))}
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
meta = dict(app_file=os.path.basename(a.app), app_sha256=sha(a.app), suite_manifest_sha256=sha(os.path.join(a.suite, "suite_manifest.csv")), reference_sha256=sha(os.path.join(a.suite, "reference.csv")))
out_rows, errs = [], []
CK = os.path.join(a.out, "checkpoint.jsonl"); done = {}
if os.path.exists(CK):
    for l in open(CK):
        if l.strip(): r_ = json.loads(l); done[r_["file"]] = r_
T0 = time.time()
with sync_playwright() as p:
    b = getattr(p, a.browser).launch(); pg = b.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    t0 = time.perf_counter(); pg.goto("file://" + os.path.abspath(a.app) + "#/lab/image"); pg.wait_for_function("typeof AMRNet!=='undefined' && (window.AMR_IMAGE_MODEL||window.AMR_IMAGE_MODEL_CROP)", timeout=60000); meta["page_and_model_load_s"] = round(time.perf_counter() - t0, 2)
    pg.wait_for_timeout(1500)
    try: meta["app_version"] = pg.evaluate("typeof APP!=='undefined'?APP.version:null")
    except Exception: meta["app_version"] = None
    try: pg.select_option("#imgModelPick", a.model); pg.wait_for_timeout(300)
    except Exception: pass
    js_classes = pg.evaluate("(window.AMR_IMAGE_MODEL&&AMR_IMAGE_MODEL.classes)||null") if a.model == "plate" else pg.evaluate("(window.AMR_IMAGE_MODEL_CROP&&AMR_IMAGE_MODEL_CROP.classes)||null")
    meta["class_order_matches_reference"] = (js_classes == classes); meta["classes_in_app"] = len(js_classes or []); meta["classes_in_reference"] = len(classes)
    pg.evaluate("(()=>{window.__P=[];const o=AMRNet.softmax;AMRNet.softmax=z=>{const p=o(z);window.__P.push(Array.from(p));return p};})()")
    def run_one(path):
        pg.evaluate("window.__P.length=0"); n_err = len(errs); pg.set_input_files("#plateImageInput", path); pg.wait_for_timeout(a.wait_ms)
        card = pg.evaluate("(()=>{const e=document.getElementById('plateImageInput'); const c=e&&e.closest('.card'); return c?c.innerText:''})()")
        if pg.is_disabled("#imgModelRun"):
            oc = "rejected_with_message" if "could not be analysed" in card else ("rejected_by_quality_check" if "Quality:" in card else "rejected_silent")
            return dict(outcome=oc, probs=None, seconds=None, text=card[-300:].replace("\n", " | "), new_errors=len(errs) - n_err)
        t = time.perf_counter(); pg.click("#imgModelRun")
        try: pg.wait_for_selector("#imgModelOut h4, #imgModelOut .callout", timeout=120000)
        except Exception: return dict(outcome="timeout", probs=None, seconds=None, text="", new_errors=len(errs) - n_err)
        dt = time.perf_counter() - t; pg.wait_for_timeout(200); txt = pg.inner_text("#imgModelOut"); P = pg.evaluate("window.__P")
        oc = "abstained" if "Cannot tell" in txt else ("answered" if P else "no_output")
        return dict(outcome=oc, probs=[np.array(x) for x in P], seconds=dt, text=txt[:300].replace("\n", " | "), new_errors=len(errs) - n_err)
    for f in sorted(os.listdir(os.path.join(a.suite, "suite"))):
        if f in done: out_rows.append(done[f]); continue
        if a.budget_s and time.time() - T0 > a.budget_s: print("budget reached; run again to resume"); b.close(); raise SystemExit(3)
        r = run_one(os.path.join(a.suite, "suite", f)); R = ref.get(f); d = dict(file=f, category=man[f]["category"], expected=man[f]["expected"], outcome=r["outcome"], seconds=r["seconds"], new_page_errors=r["new_errors"], app_text=r["text"])
        if R and R["decodes"] == "1" and r["probs"] and len(r["probs"]) >= 3 and a.model == "plate":
            V = [np.array([float(R[f"v{v}_{c}"]) for c in classes]) for v in range(3)]; B = r["probs"][:3]
            d["top_views_agree_with_ref"] = int(all(int(B[i].argmax()) == int(V[i].argmax()) for i in range(3)))
            d["max_abs_prob_diff"] = max(float(np.abs(B[i] - V[i]).max()) for i in range(3)); d["mean_abs_prob_diff"] = float(np.mean([np.abs(B[i] - V[i]).mean() for i in range(3)]))
            m = sum(B) / 3; d["app_top"] = classes[int(m.argmax())]; d["ref_top"] = R["ref_top"]; d["app_conf"] = float(m.max()); d["ref_conf"] = float(R["ref_mean_conf"])
            d["app_would_answer"] = int(len({int(x.argmax()) for x in B}) == 1 and m.max() >= 0.9); d["ref_answers"] = int(R["ref_answers"]); d["answer_rule_agrees"] = int(d["app_would_answer"] == d["ref_answers"])
        out_rows.append(d); open(CK, "a").write(json.dumps(d, default=float) + "\n"); print(f, d["outcome"], d.get("max_abs_prob_diff", ""), flush=True)
    # repeatability and latency on the first supported file
    first = next(f for f in sorted(ref) if f.startswith("A_")); rep = []; lat = []
    for i in range(a.latency_runs):
        r = run_one(os.path.join(a.suite, "suite", first))
        if r["probs"]: rep.append(np.array(r["probs"][:3])); lat.append(r["seconds"])
    meta["repeatability_runs"] = len(rep); meta["repeatability_max_abs_diff_between_runs"] = float(max(np.abs(rep[i] - rep[0]).max() for i in range(len(rep)))) if rep else None
    if lat:
        q = statistics.quantiles(lat, n=4) if len(lat) >= 4 else [min(lat), statistics.median(lat), max(lat)]
        meta["latency_seconds"] = dict(runs=len(lat), median=round(statistics.median(lat), 3), q1=round(q[0], 3), q3=round(q[-1], 3), first_run=round(lat[0], 3))
    b.close()
meta["page_errors"] = errs
keys = sorted({k for r in out_rows for k in r}, key=lambda k: (k != "file", k)); 
with open(os.path.join(a.out, "app_vs_reference.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out_rows)
S = {}
for cat in "ABCD":
    rs = [r for r in out_rows if r["category"] == cat]; S[cat] = {k: sum(1 for r in rs if r["outcome"] == k) for k in sorted({r["outcome"] for r in rs})}; S[cat]["files"] = len(rs)
cmp_ = [r for r in out_rows if "max_abs_prob_diff" in r]
if cmp_:
    S["agreement"] = dict(compared=len(cmp_), top_class_all_views_agree=sum(r["top_views_agree_with_ref"] for r in cmp_), max_abs_diff_over_all=max(r["max_abs_prob_diff"] for r in cmp_),
                          median_of_max_abs_diff=float(np.median([r["max_abs_prob_diff"] for r in cmp_])), answer_rule_agrees=sum(r["answer_rule_agrees"] for r in cmp_))
S["invalid_inputs_handled_without_page_error"] = sum(1 for r in out_rows if r["category"] == "C" and r["new_page_errors"] == 0 and r["outcome"] in ("rejected_with_message", "rejected_by_quality_check", "abstained")) 
S["supported_files_not_answered"] = [r["file"] for r in out_rows if r["category"] in "AB" and r["outcome"] not in ("answered", "abstained")]
json.dump(dict(meta=meta, summary=S), open(os.path.join(a.out, "app_validation_summary.json"), "w"), indent=1, default=float)
print(json.dumps(dict(meta=meta, summary=S), indent=1, default=float))
