# Dashboard Performansi Witel SUMALUT — Auto-Update

Dashboard satu-file (`index.html`) yang **otomatis ter-update tiap hari** dengan menarik data
dari file Excel di folder `data/`. Di-hosting via GitHub Pages.

```
Excel di data/  ──►  build.py  ──►  index.html  ──►  GitHub Pages
                     (tiap hari via GitHub Actions)
```

---

## 📁 Struktur Repo

```
dashboard-smlt/
├── index.html                     # dashboard (di-generate build.py, jangan edit manual)
├── build.py                       # skrip build: tarik data Excel -> regenerasi index.html
├── requirements.txt               # dependency Python (pandas, openpyxl)
├── README.md                      # dokumen ini
├── data/                          # SEMUA Excel sumber (lihat data/README.md)
│   ├── 01_flaging/                # FLAGING_TREG_V_2026*.xlsx  (master KPI)  ✅ aktif
│   ├── 02_funnel/                 # TREG5_SALES_FUNNEL_YYYYMMDD.xlsx         ✅ aktif
│   ├── 03_ct0/  04_ogp/  05_collection/  06_baseline/   (⏳ menyusul)
│   └── README.md                  # panduan file mana ke folder mana
└── .github/workflows/daily-build.yml   # penjadwal harian
```

---

## 🚀 Setup Sekali Saja

1. **Salin file-file ini ke repo** `natilotek/dashboard-smlt`:
   `index.html`, `build.py`, `requirements.txt`, `README.md`, folder `data/`, dan
   `.github/workflows/daily-build.yml`. Commit & push ke branch `main`.

2. **Aktifkan GitHub Pages** (jika belum): repo ▸ **Settings ▸ Pages** ▸ Source = *Deploy from a branch* ▸
   Branch = `main` / folder `/ (root)` ▸ Save. Dashboard akan tayang di
   `https://natilotek.github.io/dashboard-smlt/`.

3. **Beri izin Actions menulis** (agar bot bisa commit hasil build): repo ▸ **Settings ▸ Actions ▸
   General ▸ Workflow permissions** ▸ pilih **Read and write permissions** ▸ Save.

Selesai. Mulai besok pagi dashboard rebuild sendiri tiap hari.

---

## 🔁 Rutinitas Harian (cukup 1 langkah)

Ada **3 cara** memicu update — pilih yang paling nyaman:

- **Cara 1 — biarkan otomatis.** Tiap hari **06:00 WITA** GitHub Actions rebuild dashboard dari
  file terbaru di `data/`. Tidak perlu lakukan apa-apa.

- **Cara 2 — upload data baru.** Saat ada file Excel baru (mis. flaging minggu ini), taruh di folder
  yang sesuai (`data/01_flaging/…`), lalu commit/push. Cukup **drag-and-drop** lewat web GitHub:
  buka folder ▸ **Add file ▸ Upload files** ▸ Commit. Build langsung jalan otomatis.

- **Cara 3 — tombol manual.** Repo ▸ tab **Actions** ▸ *Build Dashboard Harian* ▸ **Run workflow**.

> Tidak perlu menghapus file lama di `data/`. `build.py` selalu memakai file **paling baru** di
> tiap folder. Untuk funnel, pastikan nama file memuat tanggal `YYYYMMDD`.

---

## 📊 Tab mana yang otomatis update?

| Sumber (folder) | Blok data | Tab yang ter-update | Status |
|---|---|---|---|
| `01_flaging/` | `__XLSX_B64__` | **Witel, TelDa, Potret, Ranking, Weekly**, + angka KPI Rising Star | ✅ Otomatis |
| `02_funnel/` (TREG5_SALES_FUNNEL) | `__FUNNEL__`, `__MYAGG__` | **Funneling** (Mytens LOP) + CvR F5/F0 + Kecukupan LOP | ✅ Otomatis |
| `03_ct0/` (T_NAL CSV) | `__CT0__` | **Analisis CT-0** | ✅ Otomatis |
| lainnya | `__COLLECTION__`, `__AOSODOMORO__`, `__EDK__`, `__FN_SPH__`, `__BL2025__`, dst | CT-0, Collection, AOSODOMORO, EDK, Funnel SPH, Rising Star (komputasi) | ⏳ Pakai data terakhir sampai extractor ditambahkan |

**Catatan konsistensi:** saat file flaging baru masuk, tab berbasis flaging langsung ikut berubah.
Tab yang masih ⏳ (mis. CT-0, Collection, Rising Star) tetap memakai angka terakhir sampai
extractor-nya dibuat — jadi angkanya bisa sementara tidak sinkron dengan flaging terbaru.

---

## 🧩 Menambah sumber baru ke otomasi

Setiap sumber = satu fungsi `build_xxx(html)` di `build.py` yang:
1. mengambil file dari `data/<folder>/` (pakai helper `latest(...)`),
2. mengekstrak & menyusun objek data,
3. memasukkannya dengan `replace_json(html, "__NAMA__", obj)` atau `replace_b64(...)`.

Lalu daftarkan di list `EXTRACTORS`. Semua dibungkus try/except, jadi bila 1 sumber gagal,
blok lamanya dipertahankan dan dashboard tetap aman. Kerangka + contoh (flaging & funnel) sudah ada
di `build.py`. Kirimkan file sumber + definisi kolomnya bila ingin di-wire yang berikutnya
(CT-0, Collection, AOSODOMORO, dll).

---

## 💻 Menjalankan lokal (opsional, untuk uji)

```bash
pip install -r requirements.txt
python build.py            # regenerasi index.html dari data/
# buka index.html di browser untuk cek
```

## ⏰ Mengubah jadwal

Edit baris `cron` di `.github/workflows/daily-build.yml`. Format UTC.
`0 22 * * *` = 22:00 UTC = **06:00 WITA**. Contoh 12:00 WITA → `0 4 * * *`.

## 🗂️ Catatan ukuran repo

`index.html` ~7,8 MB dan di-commit ulang setiap ada perubahan data, sehingga histori Git
bertambah seiring waktu. Ini normal dan aman. Jika kelak ingin lebih ramping, data bisa
dipisah ke file JSON eksternal yang di-*fetch* saat runtime (refactor terpisah).
