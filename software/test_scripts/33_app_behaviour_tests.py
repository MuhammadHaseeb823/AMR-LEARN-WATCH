#!/usr/bin/env python3
"""App behaviour tests for paper 2 (what the numerical comparison in 32_ does not cover). Headless browser, nothing is uploaded.
  python 33_app_behaviour_tests.py --app AMR-INTELLIGENCE-19.html --image app_suite/suite/A_kpn_0.jpg --invalid app_suite/suite/C_random_bytes.jpg --out app_behaviour
Tests: (1) decision rule on scripted probability vectors (all three views must agree and the mean probability must reach 0.9);
(2) the displayed species name against the class list; (3) network requests during a classification, and a repeat with the network switched off;
(4) what the page stores (localStorage, sessionStorage, cookies, IndexedDB) and whether any of it contains image data;
(5) repeat after a page reload; (6) recovery: valid, invalid, valid again, and no stale answer after the invalid file;
(7) double click on the run button; (8) model file unavailable. Writes app_behaviour_results.csv and app_behaviour_summary.json. Research use only."""
import argparse, csv, json, os, re, shutil, tempfile
import numpy as np
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('--browser', default='chromium', choices=['chromium','firefox','webkit']); ap.add_argument("--app", required=True); ap.add_argument("--image", required=True); ap.add_argument("--invalid", required=True)
ap.add_argument("--out", default="app_behaviour"); ap.add_argument("--wait-ms", type=int, default=3500); ap.add_argument("--threshold", type=float, default=0.9)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); APP = os.path.abspath(a.app); results = []
def rec(tid, cat, expected, observed, ok, note=""): results.append(dict(test_id=tid, category=cat, expected=expected, observed=str(observed)[:260], pass_fail="pass" if ok else "FAIL", notes=note)); print(("PASS " if ok else "FAIL ") + tid, "|", str(observed)[:110])
def load(pg, path=APP): 
    pg.goto("file://" + path + "#/lab/image"); pg.wait_for_function("typeof AMRNet!=='undefined' && window.AMR_IMAGE_MODEL", timeout=60000); pg.wait_for_timeout(1500)
    try: pg.select_option("#imgModelPick", "plate"); pg.wait_for_timeout(300)
    except Exception: pass
def upload(pg, f): pg.set_input_files("#plateImageInput", f); pg.wait_for_timeout(a.wait_ms)
def run(pg, timeout=120000):
    pg.click("#imgModelRun"); pg.wait_for_selector("#imgModelOut h4, #imgModelOut .callout", timeout=timeout); pg.wait_for_timeout(300); return pg.inner_text("#imgModelOut")
with sync_playwright() as p:
    b = getattr(p, a.browser).launch(); ctx = b.new_context(); pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150])); reqs = []
    pg.on("request", lambda r: reqs.append(r.url))
    load(pg); classes = pg.evaluate("AMR_IMAGE_MODEL.classes"); names = pg.evaluate("AMR_IMAGE_MODEL.card.names")
    upload(pg, a.image)
    # (1) decision rule on scripted vectors
    K = len(classes)
    def vec(top, conf): v = np.full(K, (1 - conf) / (K - 1)); v[top] = conf; return v.tolist()
    cases = [("R1_all_agree_high", [vec(3, .95)] * 3, True), ("R2_agree_mean_below_threshold", [vec(3, .89)] * 3, False), ("R3_agree_mean_just_above", [vec(3, .905)] * 3, True),
             ("R4_views_disagree_each_high", [vec(3, .95), vec(5, .95), vec(3, .95)], False), ("R5_agree_conf_differs_mean_above", [vec(3, .99), vec(3, .99), vec(3, .81)], True),
             ("R6_agree_one_view_low_mean_below", [vec(3, .99), vec(3, .80), vec(3, .80)], False)]
    for tid, V, want in cases:
        pg.evaluate("window.__SCRIPT=%s; window.__I=0; if(!window.__ORIG){window.__ORIG=AMRNet.softmax;} AMRNet.softmax=z=>{const v=window.__SCRIPT[window.__I%%window.__SCRIPT.length]; window.__I++; return v;};0" % json.dumps(V))
        pg.evaluate("document.getElementById('imgModelOut').innerHTML=''"); 
        try: txt = run(pg)
        except Exception as e: rec(tid, "decision_rule", "answer" if want else "abstain", "timeout/err " + str(e)[:60], False); continue
        ans = "Cannot tell" not in txt; shown = names[classes[3]] in txt
        rec(tid, "decision_rule", "answer" if want else "abstain", "answer" if ans else "abstain", ans == want, f"species name shown: {shown}" if ans else "")
        if want and ans: rec(tid + "_display", "display", f"name of class 3 ({names[classes[3]]}) shown", f"shown={shown}", shown)
    pg.evaluate("AMRNet.softmax=window.__ORIG;0")
    # NaN output must not become an answer
    pg.evaluate("AMRNet.softmax=z=>Array.from(z).map(()=>NaN);0"); pg.evaluate("document.getElementById('imgModelOut').innerHTML=''")
    try: txt = run(pg, 30000); rec("R7_nan_output", "decision_rule", "no species answer", "answered" if "Cannot tell" not in txt and "Presumptive suggestions" in txt else "no answer", "Cannot tell" in txt or "Presumptive suggestions" not in txt, txt[:100].replace("\n", " "))
    except Exception as e: rec("R7_nan_output", "decision_rule", "no species answer", "no output (timeout/error)", True, str(e)[:60])
    pg.evaluate("AMRNet.softmax=window.__ORIG;0")
    # (3) network
    ctx2 = b.new_context(); p2 = ctx2.new_page(); r2 = []; e2 = []; p2.on("request", lambda r: r2.append(r.url)); p2.on("pageerror", lambda e: e2.append(str(e)[:120])); load(p2); r2.clear(); upload(p2, a.image); txt = run(p2)
    ext = [u for u in r2 if re.match(r"https?://", u)]; rec("N1_no_external_requests_during_classification", "network", "no http(s) request from upload to answer", f"{len(ext)} external requests: {ext[:3]}", len(ext) == 0)
    ctx2.set_offline(True); p2.evaluate("document.getElementById('imgModelOut').innerHTML=''"); upload(p2, a.image); txt = run(p2); rec("N2_works_offline", "network", "classification completes with the network off", "completed" if txt else "no output", bool(txt) and not e2)
    # (4) storage
    st = p2.evaluate("""(async()=>{const o={ls:{},ss:{},cookies:document.cookie,idb:[]}; for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);o.ls[k]=localStorage.getItem(k).length}
      for(let i=0;i<sessionStorage.length;i++){const k=sessionStorage.key(i);o.ss[k]=sessionStorage.getItem(k).length}
      try{o.idb=(await indexedDB.databases()).map(d=>d.name)}catch(e){}; const imgdata=[...Object.keys(localStorage)].filter(k=>/data:image|^\\/9j\\//.test(localStorage.getItem(k))); o.img_in_ls=imgdata; return o})()""")
    rec("S1_no_image_data_in_browser_storage", "storage", "no image data stored", f"localStorage keys {list(st['ls'])} ; sessionStorage {list(st['ss'])} ; cookies '{st['cookies'][:30]}' ; indexedDB {st['idb']} ; image data in: {st['img_in_ls']}", not st["img_in_ls"], "keys and sizes only; the page may store review records only if the user saves a confirmation")
    ctx2.close()
    # (5) reload repeatability
    probs = []
    for i in range(2):
        if i == 0: load(pg)
        else:
            pg.reload(); pg.wait_for_function("typeof AMRNet!=='undefined' && window.AMR_IMAGE_MODEL", timeout=60000); pg.wait_for_timeout(1500)
            try: pg.select_option("#imgModelPick", "plate"); pg.wait_for_timeout(300)
            except Exception: pass
        pg.evaluate("window.__P=[];const o=AMRNet.softmax;AMRNet.softmax=z=>{const p=o(z);window.__P.push(Array.from(p));return p};0"); upload(pg, a.image); run(pg); probs.append(np.array(pg.evaluate("window.__P")))
    d = float(np.abs(probs[0] - probs[1]).max()) if probs[0].shape == probs[1].shape else 1.0; rec("P1_same_output_after_reload", "repeatability", "identical probabilities", f"max difference {d}", d == 0.0)
    # (6) recovery and stale answers
    load(pg); upload(pg, a.image); t1 = run(pg); first_ans = re.findall(r"<li><strong>", pg.inner_html("#imgModelOut"))
    upload(pg, a.invalid); out_after = pg.inner_text("#imgModelOut"); card = pg.inner_text("#imageAnalysisResult")
    rec("F1_no_stale_answer_after_invalid_file", "recovery", "previous answer cleared and run button disabled", f"run disabled={pg.is_disabled('#imgModelRun')}; output starts: {out_after[:80]!r}", pg.is_disabled("#imgModelRun") and "Presumptive suggestions" not in out_after)
    rec("F2_clear_message_for_invalid_file", "recovery", "visible message that the file could not be analysed", card[:110].replace("\n", " "), "could not be analysed" in card)
    upload(pg, a.image); t3 = run(pg); rec("F3_valid_after_invalid_works", "recovery", "answer or abstention shown", t3[:60].replace("\n", " "), bool(t3))
    # (7) double click
    n0 = len(errs); upload(pg, a.image); pg.click("#imgModelRun"); 
    try: pg.click("#imgModelRun", timeout=500)
    except Exception: pass
    pg.wait_for_selector("#imgModelOut h4, #imgModelOut .callout", timeout=120000); pg.wait_for_timeout(500)
    nres = len(re.findall(r"Presumptive suggestions|Cannot tell", pg.inner_text("#imgModelOut")))
    rec("D1_double_click_safe", "robustness", "exactly one result, no page error", f"{nres} result(s); new page errors {len(errs) - n0}", nres == 1 and len(errs) == n0)
    ctx.close()
    # (8) model unavailable
    ctx3 = b.new_context(); p3 = ctx3.new_page(); e3 = []; p3.on("pageerror", lambda e: e3.append(str(e)[:120])); p3.route(re.compile(r"amr_image_model.*\.js$"), lambda r: r.abort())
    p3.goto("file://" + APP + "#/lab/image"); p3.wait_for_timeout(3000)
    try: p3.set_input_files("#plateImageInput", a.image); p3.wait_for_timeout(a.wait_ms)
    except Exception: pass
    try: dis = p3.is_disabled("#imgModelRun")
    except Exception: dis = True
    st_txt = p3.evaluate("(document.getElementById('imgModelStatus')||{}).innerText||''")
    rec("M1_model_missing_no_prediction", "robustness", "no prediction offered; clear message", f"run disabled={dis}; status: {st_txt[:90]!r}", dis and bool(st_txt))
    ctx3.close(); b.close()
n = len(results); f = [r for r in results if r["pass_fail"] == "FAIL"]
with open(os.path.join(a.out, "app_behaviour_results.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
json.dump(dict(app=os.path.basename(APP), tests=n, passed=n - len(f), failed=[r["test_id"] for r in f], page_errors=errs), open(os.path.join(a.out, "app_behaviour_summary.json"), "w"), indent=1)
print(f"\n{n - len(f)} of {n} passed; failed: {[r['test_id'] for r in f]}")
