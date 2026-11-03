#!/usr/bin/env python3
"""Tests for the 0.21.0 additions (research context panel, threshold explorer, run-record export, planted-rise options, count-based comparison row).
  python 35_new_feature_tests.py --learn AMR-LEARN-0.21.0.html --watch AMR-WATCH-0.21.0.html --answer-image A_ses_0.jpg --abstain-image A_kpn_0.jpg --out new_feature_tests
Headless Chromium; nothing is uploaded. Writes new_feature_results.csv and new_feature_summary.json. Research use only."""
import argparse, csv, json, os, re
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('--browser', default='chromium', choices=['chromium','firefox','webkit'])
ap.add_argument("--learn", required=True); ap.add_argument("--watch", required=True); ap.add_argument("--answer-image", required=True); ap.add_argument("--abstain-image", required=True)
ap.add_argument("--out", default="new_feature_tests"); ap.add_argument("--wait-ms", type=int, default=3500)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); R = []
def rec(tid, cat, expected, observed, ok): R.append(dict(test_id=tid, category=cat, expected=expected, observed=str(observed)[:240], pass_fail="pass" if ok else "FAIL")); print(tid, "pass" if ok else "FAIL", str(observed)[:90])
def load(pg, path):
    pg.goto("file://" + os.path.abspath(path) + "#/lab/image"); pg.wait_for_function("typeof AMRNet!=='undefined' && window.AMR_IMAGE_MODEL", timeout=60000); pg.wait_for_timeout(1500)
    try: pg.select_option("#imgModelPick", "plate"); pg.wait_for_timeout(300)
    except Exception: pass
def upload(pg, f): pg.set_input_files("#plateImageInput", f); pg.wait_for_timeout(a.wait_ms)
def run(pg):
    pg.click("#imgModelRun"); pg.wait_for_selector("#imgModelOut h4, #imgModelOut .callout", timeout=120000); pg.wait_for_timeout(400)
with sync_playwright() as p:
    b = getattr(p, a.browser).launch(); ctx = b.new_context(accept_downloads=True); pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
    load(pg, a.learn)
    ver = pg.evaluate("APP.version"); rec("V1_version", "version", "0.21.0", ver, ver == "0.21.0")
    # answered photograph: panel present (values below are from the cross-validation analysis files thr.json, bands.json, per-species table)
    upload(pg, a.answer_image); run(pg); txt = pg.inner_text("#imgModelOut"); ans = "Cannot tell" not in txt
    rec("P1_answered_shows_panel", "panel", "context panel present when a species is suggested", f"answered={ans}; panel={'What cross-validation says' in txt}", ans and "What cross-validation says" in txt)
    pg.click("#imgModelOut details summary"); pg.wait_for_timeout(200); det = pg.inner_text("#imgModelOut details")
    rec("P2_species_figures_match_table", "panel", "Salmonella: correct in 49 of 50 cases; right in 49 of 49 when named", det[det.find("When a photograph"):det.find("When a photograph") + 200].replace("\n", " "), "correctly in 49 of 50" in det and "right in 49 of 49" in det)
    rec("P2b_band_sentence", "panel", "95-99% band: 137 of 169 (81.1%)", "present" if "137 of 169" in det and "81.1%" in det else "missing", "137 of 169" in det and "81.1%" in det)
    rec("P3_not_exact_model_caveat", "panel", "states figures are not for this exact model file or the user's photographs", "caveat present" if "not this exact model file" in det else "missing", "not this exact model file" in det)
    opts = pg.evaluate("[...document.querySelectorAll('#cvThr option')].map(o=>o.innerText)")
    rec("T0_seven_options", "explorer", "no threshold + six thresholds", str(len(opts)), len(opts) == 7)
    pg.select_option("#cvThr", "4"); pg.wait_for_timeout(200); t4 = pg.inner_text("#cvThrOut")
    rec("T1a_explorer_0.9", "explorer", "47.8% answered, 87.7% correct at 0.9 (analysis table)", t4[:150].replace("\n", " "), "47.8%" in t4 and "87.7%" in t4)
    pg.select_option("#cvThr", "6"); pg.wait_for_timeout(200); t6 = pg.inner_text("#cvThrOut")
    rec("T1_explorer_0.99", "explorer", "21.9% answered, 95.2% correct at 0.99 (analysis table)", t6[:150].replace("\n", " "), "21.9%" in t6 and "95.2%" in t6)
    mc = pg.evaluate("AMR_IMAGE_MODEL.card.min_confidence"); rec("T2_explorer_does_not_change_rule", "explorer", "application threshold still 0.9 after the explorer was moved to 0.99", str(mc), mc == 0.9)
    with pg.expect_download() as dl: pg.click("#imgExport")
    path = os.path.join(a.out, "run_record_test.json"); dl.value.save_as(path); raw = open(path).read(); rr = json.loads(raw)
    rec("E1_export_fields", "export", "version, rule (0.9, three views) and outcome present", f"{rr.get('format')} v{rr.get('app_version')} min_conf={rr['rule']['min_confidence']} abstained={rr['outcome']['abstained']}", rr.get("format") == "amr-run-record-1" and rr.get("app_version") == "0.21.0" and rr["rule"]["min_confidence"] == 0.9 and rr["rule"]["views"] == 3 and "outcome" in rr)
    rec("E2_export_no_image_data", "export", "no image data in the file", f"{len(raw)} bytes; image-like content {bool(re.search(r'data:image|/9j/|base64', raw))}", not re.search(r"data:image|/9j/|base64", raw) and len(raw) < 3000)
    # abstained photograph: no species-specific text
    upload(pg, a.abstain_image); run(pg); txt2 = pg.inner_text("#imgModelOut"); ab = "Cannot tell" in txt2
    d2 = pg.inner_text("#imgModelOut details") if pg.locator("#imgModelOut details").count() else ""
    rec("P4_abstained_shows_no_species_context", "panel", "no species-specific figures when it cannot tell", f"abstained={ab}; species text={'When a photograph really was' in d2}", ab and "When a photograph really was" not in d2)
    rec("X1_no_page_errors_learn", "robustness", "no page errors", f"{len(errs)}", len(errs) == 0)
    # WATCH
    pw = ctx.new_page(); e2 = []; pw.on("pageerror", lambda e: e2.append(str(e)[:150])); pw.goto("file://" + os.path.abspath(a.watch)); pw.wait_for_timeout(1500)
    pw.evaluate("document.querySelectorAll('[data-page=\"trends\"]').forEach(e=>e.click())"); pw.wait_for_timeout(600)
    def check(n, pk, rp):
        pw.select_option("#trValN", n); pw.select_option("#trValPeak", pk); pw.select_option("#trValRamp", rp); pw.click("#trValBtn"); pw.wait_for_timeout(6000 if n == "60" else 2500)
        return pw.evaluate("[...document.querySelectorAll('#trValOut tbody tr')].map(r=>[...r.cells].map(c=>c.innerText))")
    rows = check("60", "0.30", "4"); dash = [r for r in rows if "used on the dashboard" in r[0]][0]; cnt = [r for r in rows if r[0].startswith("Count-based")]
    rec("W1_default_reproduces_0.20.0", "trends", "dashboard rule 32 found, 28 missed, 146 false alerts (as in 0.20.0)", " / ".join(dash[1:4]), dash[1:4] == ["32", "28", "146"])
    base = {"Moving average": ["41", "19", "928"], "EWMA": ["59", "1", "1345"], "CUSUM": ["60", "0", "1934"], "2 of 3 agree": ["60", "0", "1550"]}
    ok = all([r for r in rows if r[0] == k][0][1:4] == v for k, v in base.items())
    rec("W2_other_detectors_unchanged", "trends", "four 0.20.0 detector rows identical", str(ok), ok)
    rec("W3_count_based_row_present", "trends", "one count-based row labelled compared, not used", f"{len(cnt)} row(s); {cnt[0][0] if cnt else ''}", len(cnt) == 1 and "compared, not used" in cnt[0][0])
    rec("W4_interval_columns", "trends", "sensitivity shown with a 95% interval", dash[5], bool(re.search(r"\(\d+.\d+\)", dash[5])))
    rows2 = check("30", "0.50", "1"); d2 = [r for r in rows2 if "used on the dashboard" in r[0]][0]
    rows3 = check("30", "0.30", "4"); d3 = [r for r in rows3 if "used on the dashboard" in r[0]][0]
    rec("W5_options_change_result", "trends", "a larger, faster rise is found more often than the default in the same 30 datasets", f"found {d2[1]} of 30 (50% over 1 month) against {d3[1]} of 30 (default)", int(d2[1]) > int(d3[1]))
    rec("X2_no_page_errors_watch", "robustness", "no page errors", f"{len(e2)}", len(e2) == 0)
    b.close()
json.dump(dict(tests=len(R), passed=sum(r["pass_fail"] == "pass" for r in R), failed=[r["test_id"] for r in R if r["pass_fail"] != "pass"]), open(os.path.join(a.out, "new_feature_summary.json"), "w"), indent=1)
with open(os.path.join(a.out, "new_feature_results.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(R[0])); w.writeheader(); w.writerows(R)
print("passed", sum(r["pass_fail"] == "pass" for r in R), "of", len(R))
