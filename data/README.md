# Folder Data — sumber Excel yang mensuplai dashboard

Taruh file Excel/CSV **terbaru** di folder sesuai tabel di bawah. `build.py` otomatis
mengambil file **paling baru** di tiap folder (berdasar tanggal modifikasi / tanggal di nama file).
Tidak perlu menghapus file lama — cukup tambahkan yang baru.

| Folder | Isi | Menggerakkan tab | Status extractor |
|---|---|---|---|
| `01_flaging/` | `FLAGING_TREG_V_2026*.xlsx` (master KPI) | Witel, TelDa, Potret, Ranking, Weekly, KPI Rising Star | ✅ AKTIF |
| `02_funnel/`  | `TREG5_SALES_FUNNEL_YYYYMMDD.xlsx` (min. 2 file: posisi awal & terkini) + `Monitoring_Request_SPH*.xlsx` | Funneling | ✅ Mytens AKTIF · SPH menyusul |
| `03_ct0/`     | `T_NAL_Full_Data_data.csv` | CT-0 / New Loss | ✅ AKTIF |
| `04_ogp/`     | `Data_OGP_*.xlsx`, `EDK_*.xlsx` | AOSODOMORO, EDK | ⏳ belum di-wire |
| `05_collection/` | `1__FORMAT_C3MR_DAN_BILLPER*.xlsx`, `WO_BULAN*.xlsx`, dll | Collection | ⏳ belum di-wire |
| `06_baseline/` | `FLAGING_TR5_2025.xlsx` | Baseline YoY 2025 | ⏳ belum di-wire |

**Yang sudah AKTIF** akan otomatis ter-update tiap hari. Yang **⏳ belum di-wire** tetap memakai
data terakhir yang tertanam di `index.html` sampai extractor-nya ditambahkan ke `build.py`.

Penamaan funnel penting: sertakan tanggal `YYYYMMDD` di nama file (mis. `TREG5_SALES_FUNNEL_20260630.xlsx`)
agar posisi "awal" vs "terkini" terdeteksi benar untuk grafik pergerakan LOP.
