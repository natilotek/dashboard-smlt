#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Regenerasi data dashboard SUMALUT dari folder data/.

Sifat: IDEMPOTEN & AMAN.
- Membaca index.html sebagai template (berisi logika render + data terakhir).
- Menarik ulang blok data yang DIKENALI dari file Excel/CSV di folder data/.
- Blok data yang belum di-wire DIBIARKAN apa adanya (dashboard tidak akan rusak).
- Setiap extractor dibungkus try/except: jika 1 sumber gagal, blok lamanya dipertahankan.

Jalankan: python build.py
Otomatis harian: lihat .github/workflows/daily-build.yml
"""
import base64, json, re, os, glob, sys, traceback

ROOT  = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.html")
DATA  = os.path.join(ROOT, "data")

# ---------------------------------------------------------------- helpers
def latest(folder, pattern="*.xlsx"):
    """File terbaru (berdasar tanggal modifikasi) di data/<folder>/ sesuai pola."""
    files = glob.glob(os.path.join(DATA, folder, pattern))
    files = [f for f in files if not os.path.basename(f).startswith("~$")]
    if not files:
        return None
    return sorted(files, key=os.path.getmtime)[-1]

def by_name_date(folder, pattern="*.xlsx"):
    """Semua file di folder, diurut berdasar tanggal YYYYMMDD di nama file (menaik)."""
    files = glob.glob(os.path.join(DATA, folder, pattern))
    files = [f for f in files if not os.path.basename(f).startswith("~$")]
    def key(f):
        m = re.search(r"(20\d{6})", os.path.basename(f))
        return m.group(1) if m else "00000000"
    return sorted(files, key=key)

def replace_b64(html, var, b64):
    key = f'window.{var}="'
    i = html.find(key)
    if i < 0:
        return html, False
    i += len(key)
    j = html.find('"', i)
    return html[:i] + b64 + html[j:], True

def replace_json(html, var, obj):
    key = f'window.{var}='
    i = html.find(key)
    if i < 0:
        return html, False
    i += len(key)
    open_ch = html[i]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0; j = i
    while j < len(html):
        c = html[j]
        if c == open_ch: depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0: break
        j += 1
    newjson = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return html[:i] + newjson + html[j+1:], True

def _num(x):
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(x if x is not None else "")) or 0)
    except Exception:
        return 0.0

# ================================================================
# SUMBER 1 — FLAGING (master KPI)  ->  __XLSX_B64__
# Menggerakkan tab: Witel, TelDa, Potret, Ranking, Weekly, + KPI Rising Star.
# Cukup di-embed ulang (base64); dashboard mem-parsing-nya saat runtime.
# Taruh file di: data/01_flaging/  (mis. FLAGING_TREG_V_2026*.xlsx)
# ================================================================
def embed_flaging(html):
    f = latest("01_flaging", "*.xlsx") or latest("01_flaging", "*.xls")
    if not f:
        print("  [lewati] tidak ada file di data/01_flaging/ — __XLSX_B64__ dipertahankan")
        return html
    b64 = base64.b64encode(open(f, "rb").read()).decode()
    html, ok = replace_b64(html, "__XLSX_B64__", b64)
    print(f"  [OK]  __XLSX_B64__  <- {os.path.basename(f)}  ({len(b64)//1024} KB base64)"
          if ok else "  [PERINGATAN] __XLSX_B64__ tidak ditemukan di index.html")
    return html

# ================================================================
# SUMBER 2 — SALES FUNNEL  ->  __FUNNEL__ + __MYAGG__
# Menggerakkan tab: Funneling (sisi Mytens LOP) + CvR F5/F0 + tabel Kecukupan.
# Aturan: created date 2026, SEMUA LOP (termasuk Cancel/Lose) masuk F0,
#         funnel kumulatif (F_k = LOP dgn tahap >= F_k).
# Taruh 2 file (posisi awal & terkini) di: data/02_funnel/
#   mis. TREG5_SALES_FUNNEL_20260331.xlsx (q1) & _20260622.xlsx (now)
# ================================================================
def build_funnel(html):
    import pandas as pd
    files = by_name_date("02_funnel", "TREG5_SALES_FUNNEL_*.xlsx")
    if not files:
        print("  [lewati] tidak ada file di data/02_funnel/ — __FUNNEL__/__MYAGG__ dipertahankan")
        return html
    now_f = files[-1]
    q1_f  = files[0] if len(files) > 1 else files[-1]

    DIV2SEG = {"DGS": "DGS", "DPS": "DPS", "DSS": "DSS", "RSMES": "SME", "SME": "SME"}
    STI = {"F0":0,"F1":1,"F2":2,"F3":3,"F4":4,"F5":5}
    ST  = ["F0","F1","F2","F3","F4","F5"]

    def load(path):
        df = pd.read_excel(path, sheet_name="Data", dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        g = lambda r, c: r[c] if c in df.columns and pd.notna(r[c]) else None
        out = []
        for _, r in df.iterrows():
            wit = str(g(r, "witel") or "")
            if "SUMALUT" not in wit.upper():
                continue
            cr = g(r, "created_date") or g(r, "createdon")
            cr = str(cr) if cr is not None else ""
            if not cr.startswith("2026"):
                continue
            stf = str(g(r, "status_f") or "")
            if stf not in STI:
                continue
            pt = str(g(r, "project_type") or "").upper()
            bc = g(r, "estimate_contract_start")
            out.append(dict(
                id=g(r, "lopid"), judul=g(r, "judul_proyek"), cc=g(r, "pelanggan"),
                seg=DIV2SEG.get(str(g(r, "divisi") or ""), "SME"), st=stf,
                nilai=_num(g(r, "nilai_proyek")), rev=_num(g(r, "est_rev")),
                bc=(str(bc)[:7] if bc is not None else ""),
                ng=bool(re.search("NGTMA|NEW GTMA", pt)), prog=str(g(r, "proses") or ""),
                cr=cr[:10]))
        return out

    now = load(now_f); q1 = load(q1_f)

    SEGS = [("all", lambda r: True), ("SME", lambda r: r["seg"]=="SME"),
            ("DGS", lambda r: r["seg"]=="DGS"), ("DPS", lambda r: r["seg"]=="DPS"),
            ("DSS", lambda r: r["seg"]=="DSS"), ("ngtma", lambda r: r["ng"])]

    def funnel(lst):
        rows = [{"st": s, "cnt": 0, "val": 0} for s in ST]
        for x in lst:
            k = STI[x["st"]]
            for j in range(0, k+1):
                rows[j]["cnt"] += 1
                rows[j]["val"] += x["nilai"]
        return rows

    def top(lst, stages, n=5):
        f = [r for r in lst if r["st"] in stages]
        f.sort(key=lambda r: r["nilai"], reverse=True)
        return [dict(id=r["id"], judul=r["judul"], cc=r["cc"], seg=r["seg"],
                     nilai=r["nilai"], bc=r["bc"], prog=r["prog"]) for r in f[:n]]

    slices, top34, top5, seg = {}, {}, {}, {}
    for k, fil in SEGS:
        L  = [r for r in now if fil(r)]
        Lq = [r for r in q1  if fil(r)]
        slices[k] = {"q1": funnel(Lq), "now": funnel(L)}
        top34[k]  = top(L, ["F3", "F4"])
        top5[k]   = top(L, ["F5"])
        q = [r for r in L if r["st"] in ("F3","F4","F5")]
        seg[k] = {"qualNilai": sum(r["nilai"] for r in q), "estRev": sum(r["rev"] for r in q)}
    allLOP = [dict(id=r["id"], judul=r["judul"], cc=r["cc"], seg=r["seg"],
                   st=r["st"], nilai=r["nilai"], rev=r["rev"], bc=r["bc"], ng=r["ng"]) for r in now]
    FUNNEL = {"slices": slices, "top34": top34, "top5": top5, "seg": seg,
              "allLOP": allLOP, "cvr": 0.40}

    # MYAGG: per segmen x kuartal-created x tahap (nilai dalam JUTA) — untuk CvR F5/F0 & filter
    AGG = {}
    for s in ["SME","DGS","DPS","DSS"]:
        AGG[s] = {b: {st: {"c":0,"v":0,"e":0} for st in ST}
                  for b in ["2026Q1","2026Q2","2026Q3","2026Q4"]}
    for r in now:
        m = int(r["cr"][5:7]) if len(r["cr"]) >= 7 else 1
        bk = "2026Q" + str(1 if m<=3 else 2 if m<=6 else 3 if m<=9 else 4)
        cell = AGG[r["seg"]][bk][r["st"]]
        cell["c"] += 1
        cell["v"] += round(r["nilai"]/1e6)
        cell["e"] += round(r["rev"]/1e6)

    html, ok1 = replace_json(html, "__FUNNEL__", FUNNEL)
    html, ok2 = replace_json(html, "__MYAGG__", AGG)
    print(f"  [OK]  __FUNNEL__ + __MYAGG__  <- now:{os.path.basename(now_f)} q1:{os.path.basename(q1_f)}"
          f"  ({len(allLOP)} LOP created-2026)")
    return html

# ================================================================
# SUMBER LAIN — belum di-wire (extractor menyusul).
# Blok berikut DIPERTAHANKAN dari index.html sampai extractor-nya dibuat:
#   __CT0__        <- data/03_ct0/T_NAL_*.csv           (tab CT-0)
#   __AOSODOMORO__ <- data/04_ogp/Data_OGP_*.xlsx       (tab AOSODOMORO)
#   __EDK__        <- data/04_ogp/EDK_*.xlsx            (tab EDK)
#   __FN_SPH__     <- data/02_funnel/Monitoring_Request_SPH*.xlsx (Funnel SPH)
#   __COLLECTION__ / __COLLTELDA__ <- data/05_collection/*.xlsx  (tab Collection)
#   __BL2025__     <- data/06_baseline/FLAGING_TR5_2025*.xlsx
#   __GS__/__DPS__/__DSS__/__SMES__/__AMQUAD__/__GSDETAIL__/__RISINGSTAR__/__RSCOMP__
# Untuk meng-wire salah satunya, tambahkan fungsi build_xxx(html) & panggil di main().
# ================================================================

EXTRACTORS = [
    ("FLAGING (KPI master)", embed_flaging),
    ("SALES FUNNEL (Mytens)", build_funnel),
]

def main():
    if not os.path.exists(INDEX):
        print("ERROR: index.html tidak ditemukan."); sys.exit(1)
    html = open(INDEX, encoding="utf-8").read()
    before = len(html)
    print("== Build dashboard SUMALUT ==")
    for name, fn in EXTRACTORS:
        try:
            html = fn(html)
        except Exception as e:
            print(f"  [GAGAL] {name}: {e} — blok lama dipertahankan")
            traceback.print_exc()
    # sanity: pastikan skrip utama tidak korup (cari penanda)
    if "\"use strict\"" not in html or "window.__XLSX_B64__" not in html:
        print("ERROR: hasil build tampak korup, TIDAK menulis index.html."); sys.exit(1)
    open(INDEX, "w", encoding="utf-8").write(html)
    print(f"== Selesai. index.html {before//1024} KB -> {len(html)//1024} KB ==")

if __name__ == "__main__":
    main()
