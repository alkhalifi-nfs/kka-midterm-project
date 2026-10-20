# Runbook turnamen akhir (T37)

**Status per 20 Oktober 2026: siap dijalankan.** Semua agen sudah ada di `main`: `random`, `greedy`, Model 1 (`minimax` = H2, `minimax_h1` = H1), Model 2 (`alphabeta` = H2, `alphabeta_h1` = H1), dan Model 3 (`ga`, bobot dari `results/ga_weights.json` hasil `python -m experiments.ga_train`). Bila bobot GA dilatih ulang, jalankan ulang turnamen. Dokumen ini menyiapkan langkahnya.

## 0. Prasyarat (centang semua sebelum mulai)

- [ ] PR #1 dan #2 sudah di-merge ke `main`, dan `git pull` sudah dilakukan.
- [ ] Agen resmi sudah di-merge dan memenuhi kontrak agen: `name`, `choose_move(state, time_limit=None, depth=None) -> int`; opsional `reset(seed)` dan `metrics` (lihat `experiments/__init__.py`).
- [ ] Nama agen terdaftar di `experiments/registry.py` (`AGENT_SPECS`), atau siapkan spesifikasi `alias=modul:Kelas` untuk tiap agen.
- [ ] `git status` bersih (berkas meta mencatat bila ada perubahan yang belum di-commit) dan `python -m pytest -q` hijau.
- [ ] Uji kebenaran Minimax = Alpha-Beta pada posisi di `results/positions_seed42_n500.json` sudah lulus (tugas Ravy dan Pisnur). Turnamen tidak menguji hal ini. `tests/test_alphabeta.py` baru memeriksa 24 posisi pertama (kedalaman 1-4, TT dimatikan); seluruh 500 posisi dan angka untuk Bab 3.2 belum dijalankan.

## 1. Uji asap dengan agen final (sebelum run besar)

Tujuannya menemukan agen yang melanggar kontrak, bukan menghasilkan data laporan. Berkas `smoke_*` tidak di-commit.

```bash
python -m experiments.tournament --agents all --openings 3 --seeds 1 \
    --opening-plies 6 --depth 4 --workers 1 --out results/smoke_final_check.csv
```

Periksa: tidak ada peringatan "dilewati", `forfeit` = 0 pada semua baris, dan semua agen yang diharapkan muncul di kolom `agent_p0`/`agent_p1`. Dari berkas ini ambil waktu rata-rata per game untuk memperkirakan lama run besar.

## 2. Tentukan parameter (keputusan Anda)

| Parameter | Usulan awal (belum diputuskan) | Catatan |
|---|---|---|
| `--agents` | `random,greedy,minimax,alphabeta,ga` | 5 agen = 10 pasangan |
| `--openings` | 100 | per seed |
| `--seeds` | `42,123,2026` | |
| `--opening-plies` | **6 atau lebih** (bawaan CLI: 4) | lihat di bawah |
| `--depth` | `[tentukan]` | harus sama untuk semua agen pencarian bila perbandingannya ingin adil |
| `--time-limit` | 0 | runner tidak memotong agen, tetapi `minimax` dan `alphabeta` menghormatinya sendiri lewat iterative deepening. Untuk RQ3 (batas waktu sama) jalankan run terpisah dengan `--depth 0 --time-limit <detik>` (depth 0 = hanya dibatasi waktu); hasilnya bergantung kecepatan mesin, jadi catat mesinnya dan pakai `--workers` kecil |
| `--workers` | `[tentukan]` | lebih banyak proses mempercepat run tetapi memengaruhi pengukuran waktu |

Total game = pasangan × `--openings` × 2 × jumlah seed. Dengan usulan di atas: 10 × 100 × 2 × 3 = 6.000 game.

**Mengapa `--opening-plies` sebaiknya 6 atau lebih.** Agen deterministik memainkan game identik pada pembukaan yang sama, jadi pembukaan berulang bukan sampel baru. Pengukuran sekali pakai pada 18 Oktober 2026 (seed 42, 123, 2026 × 100 pembukaan = 300 pembukaan) memberi jumlah posisi berbeda: 4 langkah acak: 276 dari 300 (8% duplikat); 6 langkah: 299 dari 300; 8 langkah: 300 dari 300. Angka ini tidak berasal dari `results/`, jadi **jangan dikutip di laporan**. Tabel parameter dari berkas meta akan mencatat angka sebenarnya untuk run final. Untuk mengulang pengukurannya:

```bash
python -c "
from experiments.tournament import count_distinct_openings
for plies in (4, 6, 8):
    print(plies, count_distinct_openings([42, 123, 2026], 100, plies))"
```

## 3. Jalankan turnamen akhir

```bash
python -m experiments.tournament --agents random,greedy,minimax,alphabeta,ga \
    --openings 100 --seeds 42,123,2026 --opening-plies 6 --depth 4 --time-limit 0 \
    --workers 8 --out results/tournament_final.csv
```

Bila terputus, ulangi perintah yang sama persis dengan tambahan `--resume`. Runner menolak `--resume` bila parameter berbeda dari isi CSV, dan membuang baris terakhir yang terpotong. Setiap pemanggilan menambah satu entri di `results/tournament_final.meta.json` (termasuk hash commit), jadi bila kode berubah di antara dua pemanggilan, hal itu terlihat.

## 4. Analisis

```bash
python -m experiments.analyze results/tournament_final.csv --out-dir results
python -m experiments.analyze results/tournament_final.csv --out-dir results/sensitivitas_opening \
    --bootstrap-unit opening
python -m experiments.report_tables --results-dir results \
    --meta results/tournament_final.meta.json --out report/tabel_hasil.md
```

Perintah kedua adalah analisis sensitivitas (bootstrap per pembukaan); bandingkan lebar interval Elo keduanya dan tulis hasilnya di Bab 3.5.5 butir 4. Perintah ketiga menghasilkan tabel untuk ditempel di Bab 3.5.3.

## 5. Periksa sebelum menulis

- [ ] Kolom `forfeit` kosong di seluruh baris. Bila tidak, cari tahu penyebabnya dari kolom `error` dan putuskan: perbaiki agen lalu ulangi, atau laporkan.
- [ ] Jumlah baris CSV sama dengan "Total game yang direncanakan" pada berkas meta.
- [ ] Jumlah game dengan `hit_move_cap` = 1 dicatat (Bab 3.5.5 butir 8).
- [ ] `regularized` pada `results/elo.csv` bernilai `False`. Bila `True`, baca catatan di Bab 3.5.2 sebelum menafsirkan Elo.
- [ ] "Pembukaan berbeda dari yang diminta" pada tabel parameter: jumlah berbeda sama dengan jumlah diminta, atau duplikatnya dinyatakan di laporan.
- [ ] Hash commit pada berkas meta cocok dengan versi kode yang akan ditulis di Bab 1.6, dan tidak ditandai "ada perubahan belum di-commit".

## 6. Yang di-commit

`results/tournament_final.csv`, `results/tournament_final.meta.json`, `results/winrate_matrix.csv`, `results/elo.csv`, `results/search_stats.csv`, `results/figures/`, `results/sensitivitas_opening/`, dan `report/tabel_hasil.md`. Jangan meng-commit apa pun yang berawalan `smoke_`.

## Yang belum dicatat otomatis

- Jumlah game yang menyentuh batas 200 putaran tabur tidak direkam per game (hanya batas 300 langkah lewat `hit_move_cap`). Bila angka itu dibutuhkan di laporan, perlu penghitung di engine.
- Faktor percabangan efektif (EBF) belum dihitung oleh `analyze.py`.
