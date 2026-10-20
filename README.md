# Congklak-Master

**Perbandingan Minimax, Alpha-Beta Pruning, dan Alpha-Beta dengan evaluasi hasil Algoritma Genetika pada permainan tradisional congklak.**

Midterm Project mata kuliah Konsep Kecerdasan Artifisial (M), Kelompok 4, Institut Teknologi Sepuluh Nopember, 2026.
Dosen: Imam Mustafa Kamal, Ph.D.

Repositori ini berisi mesin permainan congklak, tiga model AI yang dibandingkan, skrip eksperimen, dan semua data hasil yang dikutip di laporan. Semua angka di laporan bisa dihasilkan ulang dari kode di sini.

---

## Daftar isi

1. [Hasil utama dalam satu menit](#1-hasil-utama-dalam-satu-menit)
2. [Mulai cepat: instal, tes, dan coba main](#2-mulai-cepat-instal-tes-dan-coba-main)
3. [Aturan congklak yang dipakai](#3-aturan-congklak-yang-dipakai)
4. [Cara kerja ketiga model AI](#4-cara-kerja-ketiga-model-ai)
5. [Isi repositori: tiap folder dan file untuk apa](#5-isi-repositori-tiap-folder-dan-file-untuk-apa)
6. [Mengulang eksperimen di laporan](#6-mengulang-eksperimen-di-laporan)
7. [Peta bab laporan ke file hasil](#7-peta-bab-laporan-ke-file-hasil)
8. [Istilah yang sering muncul](#8-istilah-yang-sering-muncul)
9. [Masalah yang sering terjadi](#9-masalah-yang-sering-terjadi)
10. [Tim](#10-tim)

---

## 1. Hasil utama dalam satu menit

Tiga model dibandingkan:

| Model | Nama di kode | Isi singkat |
|---|---|---|
| Model 1 | `minimax` | Minimax dengan batas kedalaman |
| Model 2 | `alphabeta` | Alpha-Beta + *move ordering* + *transposition table* + *iterative deepening* |
| Model 3 | `ga` | Model 2, tetapi bobot fungsi evaluasinya dicari dengan Algoritma Genetika |

Sebagai pembanding juga ada `random` (asal pilih), `greedy` (hanya melihat satu langkah ke depan), serta `minimax_h1` dan `alphabeta_h1` (memakai fungsi evaluasi paling sederhana, H1).

Jawaban ketiga pertanyaan penelitian:

- **RQ1. Apakah Alpha-Beta memilih langkah yang sama dengan Minimax, dan berapa node yang dihemat?**
  Ya. Di 3.000 kasus uji (500 posisi × 6 kedalaman), langkah dan nilainya selalu sama. Pada kedalaman 6, Alpha-Beta hanya memeriksa 11,0% node Minimax, dan dengan *move ordering* tinggal 3,1%. *Transposition table* hampir tidak menambah penghematan (3,0%).
- **RQ2. Apakah bobot hasil GA mengalahkan bobot manual (H2)?**
  Tidak terbukti. GA menang 51,2% melawan Alpha-Beta H2, dengan interval kepercayaan 95% [47,2%; 55,1%] yang masih memuat 50%.
- **RQ3. Dengan batas waktu yang sama, model mana yang terkuat?**
  Alpha-Beta dan GA. Dengan 0,1 detik per langkah, keduanya mencari jauh lebih dalam daripada Minimax dan menang 56,4% dan 57,4% melawan Minimax (signifikan).

Pesan utamanya: di congklak, kekuatan agen ditentukan terutama oleh **seberapa dalam ia bisa mencari**, bukan oleh penyetelan fungsi evaluasinya.

---

## 2. Mulai cepat: instal, tes, dan coba main

### Yang dibutuhkan

- Python 3.10 atau lebih baru (diuji dengan Python 3.12).
- Library: numpy, pandas, matplotlib, pytest. Semuanya dipasang otomatis dari `requirements.txt`.

### Langkah instalasi

Jalankan dari folder utama repositori.

**Windows (PowerShell atau Command Prompt):**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS atau Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Setelah `activate`, cukup ketik `python` untuk perintah-perintah di bawah. Kalau `activate` tidak bisa dipakai, ganti `python` dengan `.venv\Scripts\python.exe` (Windows) atau `.venv/bin/python` (macOS/Linux).

### Menjalankan semua tes

```bash
python -m pytest -q
```

Hasil yang diharapkan: semua tes lulus (`229 passed`), dalam waktu sekitar 15 detik.

### Menonton AI bermain

```bash
python -m experiments.demo --p0 alphabeta --p1 greedy
```

Papan dicetak setiap langkah. Pemain 0 di baris bawah, Pemain 1 di baris atas, dan lumbung di kiri dan kanan:

```
            nomor:  7  6  5  4  3  2  1
         Pemain 1:  7  7  7  7  7  7  7
  [lumbung P1  0]                       [lumbung P0  0]
         Pemain 0:  7  7  7  7  7  7  7
            nomor:  1  2  3  4  5  6  7
```

Agen lain bisa dicoba dengan mengganti nama di `--p0` dan `--p1`: `random`, `greedy`, `minimax`, `minimax_h1`, `alphabeta`, `alphabeta_h1`, `ga`. Tambahkan `--quiet` kalau hanya ingin melihat skor akhir.

### Bermain melawan AI

```bash
python -m experiments.demo --p0 manusia --p1 alphabeta
```

Anda menjadi Pemain 0 (jalan pertama). Ketik nomor lubang 1 sampai 7, lalu tekan Enter.

---

## 3. Aturan congklak yang dipakai

Varian yang dipakai: **7 lubang per pemain, 7 biji per lubang (total 98 biji), dan 1 lumbung per pemain.** Aturan lengkapnya ada di [docs/rules.md](docs/rules.md). Ringkasnya:

1. **Menabur.** Ambil semua biji dari satu lubang milik sendiri, lalu taruh satu per satu ke lubang berikutnya berlawanan arah jarum jam. Lumbung sendiri diisi, lumbung lawan dilewati.
2. **Giliran tambahan.** Kalau biji terakhir jatuh di lumbung sendiri, pemain yang sama jalan lagi.
3. **Menabur lanjutan (*relay*).** Kalau biji terakhir jatuh di lubang yang sudah berisi (sisi mana pun), seluruh isi lubang itu diambil dan ditabur lagi. Ini diulang sampai biji terakhir jatuh di lumbung sendiri atau di lubang kosong.
4. **Tembak.** Kalau biji terakhir jatuh di lubang kosong milik sendiri dan lubang lawan di seberangnya berisi, biji di kedua lubang itu masuk ke lumbung sendiri.
5. **Akhir permainan.** Permainan selesai kalau pemain yang mendapat giliran tidak punya biji di lubangnya. Sisa biji masuk ke lumbung pemilik sisinya. Pemenangnya pemain dengan lumbung terbanyak.
6. **Pengaman.** Paling banyak 200 putaran tabur per giliran dan 300 langkah per permainan, supaya permainan pasti berakhir. Di semua eksperimen, batas 300 langkah tidak pernah tersentuh.

Di kode, papan disimpan sebagai daftar 16 angka:

| Indeks | Isi |
|---|---|
| 0 sampai 6 | lubang Pemain 0 |
| 7 | lumbung Pemain 0 |
| 8 sampai 14 | lubang Pemain 1 |
| 15 | lumbung Pemain 1 |

---

## 4. Cara kerja ketiga model AI

### Model 1: Minimax ([src/agents/minimax.py](src/agents/minimax.py))

AI membayangkan semua kemungkinan langkah sampai beberapa langkah ke depan (kedalaman *d*): "kalau saya pilih lubang ini, lawan akan membalas begini, lalu saya membalas begitu." Posisi di ujung bayangan itu diberi nilai oleh **fungsi evaluasi**. Pada giliran sendiri AI mengambil nilai terbesar, dan pada giliran lawan ia menganggap lawan memilih yang terkecil.

Bedanya dengan Minimax di buku: karena ada **giliran tambahan**, pemain yang sama bisa jalan dua kali berturut-turut. Jadi peran "giliran saya" atau "giliran lawan" ditentukan oleh siapa yang sedang memegang giliran, bukan oleh urutan level pohon.

### Model 2: Alpha-Beta ([src/agents/alphabeta.py](src/agents/alphabeta.py))

Hasilnya sama persis dengan Minimax, tetapi jauh lebih hemat. Ada empat tambahan:

| Komponen | Gunanya |
|---|---|
| **Pruning (pemangkasan)** | Berhenti memeriksa cabang yang sudah pasti tidak akan dipilih |
| **Move ordering** | Mencoba langkah yang paling menjanjikan lebih dulu: langkah terbaik sebelumnya, lalu giliran tambahan, lalu tembak, lalu sisanya. Pemangkasannya jadi lebih banyak |
| **Transposition table (TT)** | Mengingat posisi yang sudah pernah dinilai, dengan kunci *Zobrist hashing* |
| **Iterative deepening** | Mencari kedalaman 1, 2, 3, dan seterusnya sampai waktu habis, supaya selalu ada langkah siap pakai |

Setiap komponen bisa dimatikan satu per satu (`ordering`, `use_tt`, `iterative`). Inilah yang dipakai untuk mengukur kontribusi masing-masing di Bab 3.3.

### Model 3: Alpha-Beta + Algoritma Genetika ([src/agents/ga.py](src/agents/ga.py), [experiments/ga_train.py](experiments/ga_train.py))

Mesin pencariannya sama dengan Model 2. Bedanya ada di fungsi evaluasi: 6 fitur yang bobotnya dicari oleh **Algoritma Genetika**. Caranya: 20 kandidat bobot diadu melawan agen lain, yang terbaik "dikawinkan" dan "dimutasi", lalu diulang 30 generasi. Bobot terbaik disimpan di `results/ga_weights.json`.

### Fungsi evaluasi ([src/agents/evaluation.py](src/agents/evaluation.py))

| Fungsi | Isi | Dipakai oleh |
|---|---|---|
| **H1** | lumbung saya − lumbung lawan | `minimax_h1`, `alphabeta_h1` |
| **H2** | 1,0 × selisih lumbung + 0,3 × selisih biji di sisi + 0,5 × selisih peluang giliran tambahan + 0,2 × peluang tembak | `minimax`, `alphabeta` |
| **6 fitur GA** | fitur H2, ditambah ancaman tembak lawan dan mobilitas, dengan bobot hasil GA | `ga` |

Kalau permainan sudah selesai, nilainya diganti dengan 1000 × selisih lumbung akhir, supaya menang atau kalah selalu lebih penting daripada nilai perkiraan.

H2 sebenarnya adalah salah satu titik di ruang bobot 6 fitur, yaitu bobot (1; 0,3; 0,5; 0,2; −0,2; 0). Jadi GA mencari di ruang yang sudah memuat H2, dan perbandingan GA dengan H2 tetap adil.

---

## 5. Isi repositori: tiap folder dan file untuk apa

```
kka-midterm-project/
├── src/                  Kode utama: mesin permainan dan semua agen AI
│   ├── engine/           Mesin permainan congklak
│   └── agents/           Agen-agen AI
├── experiments/          Skrip untuk menjalankan eksperimen dan mengolah hasil
├── tests/                Tes otomatis (pytest)
├── results/              Data hasil eksperimen, tabel, dan grafik yang dikutip di laporan
├── report/               Tabel siap tempel untuk laporan dan catatan referensi
├── docs/                 Aturan permainan lengkap
├── requirements.txt      Daftar library Python yang dibutuhkan
└── pytest.ini            Pengaturan pytest
```

### `src/engine/`: mesin permainan

| File | Tugasnya |
|---|---|
| `board.py` | Logika papan: menabur, menabur lanjutan, giliran tambahan, tembak, dan akhir permainan |
| `api.py` | "Pintu masuk" untuk agen: `get_initial_state`, `get_legal_moves`, `apply_move`, `is_terminal`, `get_scores`. Semua agen hanya memakai fungsi-fungsi ini |
| `__init__.py` | Mengekspor ulang isi `api.py` |

### `src/agents/`: agen AI

| File | Tugasnya |
|---|---|
| `baseline.py` | Agen pembanding: `RandomAgent` (acak) dan `GreedyAgent` (satu langkah ke depan) |
| `evaluation.py` | Fungsi evaluasi H1, H2, dan 6 fitur GA |
| `minimax.py` | **Model 1**, Minimax |
| `alphabeta.py` | **Model 2**, Alpha-Beta lengkap, termasuk Zobrist hashing dan transposition table |
| `ga.py` | **Model 3**, Alpha-Beta yang membaca bobot dari `results/ga_weights.json` |

Semua agen punya bentuk yang sama: `choose_move(state, time_limit=None, depth=None)` mengembalikan nomor lubang, dan `metrics` mencatat jumlah node, pemangkasan, kedalaman, dan waktu.

### `experiments/`: skrip eksperimen

| File | Tugasnya | Dipakai untuk |
|---|---|---|
| `demo.py` | Menonton agen bermain atau melawan AI | Mencoba program |
| `registry.py` | Daftar nama agen (`minimax`, `ga`, dan lainnya) beserta kelas Python-nya | Dipakai skrip lain |
| `positions.py` | Membuat 500 posisi uji acak yang bisa diulang | Bab 3.2, 3.3 |
| `search_bench.py` | Mengukur node, EBF, TT, dan kesamaan langkah dengan Minimax di posisi uji | Bab 3.2, 3.3 |
| `ga_train.py` | Melatih bobot Model 3 dengan Algoritma Genetika | Bab 2.4, 3.4 |
| `tournament.py` | Turnamen *round-robin* antar agen, dengan sisi bertukar dan pembukaan acak | Bab 3.5 |
| `analyze.py` | Menghitung *win rate*, Elo, dan interval kepercayaan, lalu menggambar grafik | Bab 3.5 |
| `report_tables.py` | Mengubah hasil analisis menjadi tabel Markdown siap tempel | Bab 3.5 |

### `tests/`: tes otomatis

| File | Yang diuji |
|---|---|
| `test_engine.py`, `test_engine_rules.py` | Aturan permainan, dengan contoh yang dihitung manual |
| `test_engine_oracle.py`, `reference_engine.py` | 1.000 permainan acak dibandingkan dengan mesin rujukan yang ditulis terpisah dari teks aturan |
| `test_evaluation.py` | H1, H2, dan skor akhir permainan |
| `test_minimax.py` | Minimax sama dengan rumus di laporan, dan giliran tambahan ditangani benar |
| `test_alphabeta.py` | Alpha-Beta sama dengan Minimax, Zobrist, TT, dan batas waktu |
| `test_ga.py` | 6 fitur, operator genetika, dan training |
| `test_search_bench.py`, `test_tournament.py`, `test_analyze.py`, `test_positions.py`, `test_report_tables.py` | Skrip eksperimen dan analisis |
| `test_demo.py` | Program demo |
| `fake_agents.py` | Agen palsu untuk menguji turnamen saat ada agen yang error |

### `results/`: hasil eksperimen

| File | Isi |
|---|---|
| `positions_seed42_n500.json` | 500 posisi uji |
| `search_bench.csv` (+ `_summary.csv`, `_tabel.md`, `_nodes.png`, `.meta.json`) | Hasil pengukuran pencarian |
| `ga_weights.json` | Bobot terbaik hasil GA, yang dipakai agen `ga` |
| `ga_history.csv`, `ga_population.csv`, `ga_validation.csv`, `ga_convergence.png` | Riwayat training GA: per generasi, semua individu, validasi, dan kurva konvergensi |
| `tournament_final.csv` (+ `.meta.json`) | 12.600 game turnamen utama (7 agen, kedalaman 4) |
| `elo.csv`, `winrate_matrix.csv`, `search_stats.csv`, `figures/` | Hasil analisis turnamen utama |
| `sensitivitas_opening/` | Analisis yang sama, dengan bootstrap per pembukaan (uji sensitivitas) |
| `rq3/` | Turnamen dengan batas waktu 0,1 detik per langkah (1.800 game) beserta analisisnya |

Setiap file `.meta.json` mencatat parameter yang dipakai, commit kode, versi Python, dan tanggal. Jadi selalu bisa dilacak dari mana sebuah angka berasal.

### `report/` dan `docs/`

| File | Isi |
|---|---|
| `report/tabel_hasil.md` | Tabel turnamen utama siap tempel (dibuat otomatis) |
| `report/tabel_hasil_rq3.md` | Tabel turnamen RQ3 siap tempel (dibuat otomatis) |
| `report/referensi.md` | Catatan pemeriksaan setiap referensi di daftar pustaka |
| `docs/rules.md` | Aturan congklak lengkap |

---

## 6. Mengulang eksperimen di laporan

Semua eksperimen deterministik. Dengan perintah yang sama, hasilnya sama, berapa pun jumlah proses paralel (`--workers`) yang dipakai, kecuali kolom waktu. Perkiraan durasi di bawah diukur pada laptop Intel Core i7-12700H.

**1. Posisi uji** (sudah ada di `results/`, beberapa detik):

```bash
python -m experiments.positions --n 500 --seed 42
```

**2. Pengukuran pencarian, Bab 3.2 dan 3.3** (sekitar 3 menit; pakai 1 worker supaya angka waktunya bersih):

```bash
python -m experiments.search_bench --depths 1-6 --workers 1 --out results/search_bench.csv
```

**3. Training GA, Bab 2.4 dan 3.4** (sekitar 3 menit dengan 19 worker):

```bash
python -m experiments.ga_train --out-dir results
```

**4. Turnamen utama, Bab 3.5** (sekitar 2 menit dengan 19 worker):

```bash
python -m experiments.tournament --agents random,greedy,minimax,minimax_h1,alphabeta,alphabeta_h1,ga --openings 100 --seeds 42,123,2026 --opening-plies 6 --depth 4 --time-limit 0 --out results/tournament_final.csv
python -m experiments.analyze results/tournament_final.csv --out-dir results
python -m experiments.analyze results/tournament_final.csv --out-dir results/sensitivitas_opening --bootstrap-unit opening
python -m experiments.report_tables --results-dir results --meta results/tournament_final.meta.json --out report/tabel_hasil.md
```

**5. Turnamen dengan batas waktu sama, RQ3** (sekitar 10 menit dengan 8 worker; hasilnya sedikit bergantung pada kecepatan komputer):

```bash
python -m experiments.tournament --agents minimax,alphabeta,ga --openings 100 --seeds 42,123,2026 --opening-plies 6 --depth 0 --time-limit 0.1 --workers 8 --out results/rq3/tournament_rq3.csv
python -m experiments.analyze results/rq3/tournament_rq3.csv --out-dir results/rq3
python -m experiments.report_tables --results-dir results/rq3 --meta results/rq3/tournament_rq3.meta.json --out report/tabel_hasil_rq3.md
```

`--depth 0` berarti agen hanya dibatasi waktu. Setiap skrip punya penjelasan lengkap lewat `--help`, misalnya `python -m experiments.tournament --help`. Untuk percobaan kecil yang cepat, kurangi `--openings` atau pakai `--limit` pada `search_bench`.

---

## 7. Peta bab laporan ke file hasil

| Bab | Isi | File sumber |
|---|---|---|
| 2.1 | Aturan formal | `docs/rules.md`, `src/engine/board.py` |
| 2.2 | Minimax, H1, H2 | `src/agents/minimax.py`, `src/agents/evaluation.py` |
| 2.3 | Alpha-Beta dan komponennya | `src/agents/alphabeta.py` |
| 2.4 | Algoritma Genetika | `experiments/ga_train.py`, `src/agents/ga.py` |
| 3.2 | Minimax sama dengan Alpha-Beta | `results/search_bench_tabel.md`, `results/tournament_final.csv` |
| 3.3 | Pruning, EBF, TT (Tabel 4–5, Gambar 1) | `results/search_bench_summary.csv`, `results/search_bench_nodes.png` |
| 3.4 | Analisis GA (Tabel 6–7, Gambar 2) | `results/ga_validation.csv`, `results/ga_weights.json`, `results/ga_convergence.png` |
| 3.5 | Turnamen (Tabel 8–10, Gambar 3–4) | `report/tabel_hasil.md`, `results/figures/` |
| 3.5 | RQ3 (Tabel 11) | `report/tabel_hasil_rq3.md`, `results/rq3/` |

---

## 8. Istilah yang sering muncul

| Istilah | Artinya |
|---|---|
| **Ply / kedalaman** | Satu kali pemain memilih lubang. Kedalaman 4 berarti AI melihat 4 langkah ke depan |
| **Node** | Satu posisi papan yang diperiksa AI selama mencari. Makin sedikit node untuk hasil yang sama, makin efisien |
| **EBF (*effective branching factor*)** | Rata-rata banyak cabang yang benar-benar diperiksa per langkah. Minimax sekitar 4,7, sedangkan Alpha-Beta dengan move ordering sekitar 2,5 |
| **Pruning** | Melewati cabang yang sudah pasti tidak memengaruhi keputusan |
| **Transposition table (TT)** | "Ingatan" berisi posisi yang sudah pernah dinilai |
| **Zobrist hashing** | Cara cepat memberi setiap posisi papan sebuah kode unik 64-bit, sebagai kunci TT |
| **Iterative deepening** | Mencari kedalaman 1, 2, 3, dan seterusnya sampai waktu habis |
| **Fungsi evaluasi** | Rumus yang memberi nilai pada posisi yang belum selesai ("seberapa bagus posisi ini untuk saya") |
| **Fitness** | Nilai sebuah kandidat bobot di GA: rata-rata (100 kalau menang, 50 kalau seri, 0 kalau kalah) + selisih biji |
| **Win rate** | (menang + 0,5 × seri) / jumlah game |
| **Interval Wilson 95%** | Rentang tempat *win rate* sebenarnya kemungkinan besar berada. Kalau rentangnya memuat 50%, perbedaannya belum terbukti |
| **Elo** | Rating kekuatan relatif (rata-rata 1500). Selisih 100 poin berarti peluang menang sekitar 64% |
| **Pembukaan (*opening*)** | Beberapa langkah acak di awal game supaya setiap game berbeda. Setiap pembukaan dimainkan dua kali dengan sisi ditukar |
| **Seed** | Angka awal pembangkit acak. Seed yang sama menghasilkan hasil yang sama |

---

## 9. Masalah yang sering terjadi

| Gejala | Solusi |
|---|---|
| `python` tidak dikenali, atau Windows membuka Microsoft Store | Instal Python dari python.org atau `winget install Python.Python.3.12`, lalu buka ulang terminal |
| `ModuleNotFoundError: No module named 'numpy'` (atau pandas, pytest) | Virtual environment belum aktif. Jalankan `.venv\Scripts\activate` (Windows) atau `source .venv/bin/activate`, atau pakai `.venv\Scripts\python.exe` langsung |
| `ModuleNotFoundError: No module named 'src'` | Jalankan perintah dari folder utama repositori, dan selalu dengan bentuk `python -m ...` |
| PowerShell menolak menjalankan `activate` | Jalankan `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` sekali, atau pakai `.venv\Scripts\python.exe` langsung |
| Peringatan "agen 'ga' dilewati" | File `results/ga_weights.json` tidak ada. Jalankan `python -m experiments.ga_train --out-dir results` |
| Peringatan "hanya 299 dari 300 pembukaan yang berbeda" | Normal. Satu pembukaan acak kebetulan muncul dua kali, dan hal ini dicatat di laporan |

---

## 10. Tim

| Nama | NRP |
|---|---|
| Dheva Alvian Alfarizzy Excellent | 5053251005 |
| Muhammad Nafis Al Khalifi | 5053251019 |
| Hafidz Nur Ikhsan Isnaeni | 5053251015 |
| Achmad Mirza Arzheta Rahman | 5053251011 |
| Mhd. Ravy Enstein Wahieda Elmunif | 5953251018 |
