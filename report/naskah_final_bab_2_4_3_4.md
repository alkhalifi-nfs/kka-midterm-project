# Naskah Final: Bab 2.4 (lengkap), Bab 3, Bab 4, dan Revisi Kecil

Semua angka di naskah ini disalin dari berkas di `results/` dan `report/tabel_hasil*.md` (commit `cbbbe49`). Desimal memakai koma. Gambar diambil dari path yang disebut pada setiap keterangan gambar.

---

## A. REVISI KECIL DI BAB 2 (ganti teks lama dengan teks berikut)

**2.2.3, ganti kalimat terakhir paragraf H1** ("Kelemahan H1 adalah ...") menjadi:

> Secara konseptual, H1 hanya melihat biji yang sudah aman di lumbung dan mengabaikan potensi posisi, misalnya lubang yang akan memberi giliran tambahan atau peluang menembak pada langkah berikutnya. Seberapa besar pengaruh kelemahan ini dalam praktik diuji pada subbab 3.5.

**2.3.5, tambahkan di akhir paragraf kedua:**

> Iterasi juga dihentikan lebih awal apabila satu iterasi sudah menelusuri seluruh pohon sampai akhir permainan, karena iterasi yang lebih dalam tidak akan memberi informasi baru. Pada posisi menjelang akhir permainan, kedalaman yang dilaporkan karenanya sama dengan sisa panjang permainan dan dapat jauh melebihi kedalaman di posisi pertengahan.

**2.4.1, ganti seluruh daftar fitur** dengan:

> Fungsi evaluasi Model 3 adalah kombinasi linear enam fitur, E(s) = w1·f1 + w2·f2 + ... + w6·f6, yang dihitung dari sudut pandang agen:
>
> - **f1 (Selisih Lumbung):** b[Store(me)] − b[Store(opp)], sama dengan f1 pada H2.
> - **f2 (Selisih Biji di Sisi):** jumlah biji di lubang agen dikurangi jumlah biji di lubang lawan, sama dengan f2 pada H2.
> - **f3 (Selisih Peluang Giliran Tambahan):** banyak lubang agen yang isinya tepat sama dengan jaraknya ke lumbung agen, dikurangi besaran yang sama untuk lawan; sama dengan f3 pada H2.
> - **f4 (Peluang Tembak Agen, agresif):** jumlah biji lawan yang berada di seberang lubang kosong milik agen.
> - **f5 (Ancaman Tembak Lawan, defensif):** jumlah biji agen yang berada di seberang lubang kosong milik lawan.
> - **f6 (Selisih Mobilitas):** banyak lubang agen yang berisi dikurangi banyak lubang lawan yang berisi.
>
> Fitur f4 pada H2 sama dengan f4 − f5 di sini. Karena itu H2 adalah satu titik pada ruang bobot Model 3, yaitu (w1, ..., w6) = (1,0; 0,3; 0,5; 0,2; −0,2; 0). Algoritma Genetika mencari di ruang yang sudah memuat bobot manual, sehingga perbandingan RQ2 adil walaupun jumlah fiturnya berbeda. Kesetaraan ini diuji pada `tests/test_ga.py`. Seperti H1 dan H2, bila state terminal, nilai evaluasi diganti dengan 1000 × selisih lumbung akhir (subbab 2.2).

**2.4.3, ganti paragraf pertama dan rumus** dengan:

> Fitness setiap kromosom dihitung dengan mempertandingkannya sebagai agen Alpha-Beta (Model 2 tanpa *iterative deepening*, kedalaman 4) melawan dua lawan tetap: Alpha-Beta dengan H2 dan Alpha-Beta dengan H1, pada kedalaman yang sama. Setiap lawan dihadapi dari 8 pembukaan acak (6 langkah acak) dengan sisi bertukar, sehingga satu kromosom memainkan 32 game per generasi. Semua kromosom dalam satu generasi memakai pembukaan yang sama agar perbandingan antarkromosom adil, sedangkan pembukaan berganti setiap generasi untuk mengurangi *overfitting* terhadap posisi tertentu. Fitness adalah rata-rata per game dari
>
> Fitness = Win_Score + Margin_Biji

(Daftar butir Win_Score dan Margin_Biji tetap seperti sekarang.)

**Hapus catatan abu-abu** "[Catatan tim: H2 memakai 4 fitur ...]" di akhir 2.4.5, karena sudah terjawab di 2.4.1.

---

## B. ISI 2.4.4 DAN 2.4.5

### 2.4.4 Operator Genetika

Operator yang dipakai adalah operator standar untuk kromosom bernilai real.

- **Seleksi turnamen (k = 3).** Tiga kromosom diambil acak dari populasi, dan yang fitness-nya tertinggi menjadi induk. Seleksi dilakukan dua kali untuk mendapat dua induk.
- **Crossover BLX-α (α = 0,5), peluang 0,9.** Untuk setiap gen, nilai anak diambil acak seragam dari interval [min − α·d, max + α·d], dengan min dan max adalah nilai gen kedua induk dan d = max − min (Eshelman & Schaffer, 1993). Interval yang diperlebar memungkinkan anak keluar sedikit dari rentang kedua induk. Dengan peluang 0,1, anak adalah salinan induk pertama.
- **Mutasi Gaussian, peluang 0,2 per gen, σ = 0,15.** Gen yang terpilih ditambah bilangan acak berdistribusi normal N(0; 0,15²).
- **Pembatasan nilai.** Setelah crossover dan mutasi, setiap gen dipotong ke rentang [−1; 1], sama dengan rentang inisialisasi.
- **Elitisme 2 individu.** Dua kromosom terbaik suatu generasi disalin tanpa perubahan ke generasi berikutnya, lalu dievaluasi ulang pada pembukaan generasi baru.

### 2.4.5 Parameter dan Pemilihan Bobot Akhir

Tim tidak menetapkan parameter khusus, sehingga dipakai nilai standar yang umum untuk masalah berdimensi kecil (Tabel 3). Seluruh pelatihan memakai satu *seed* (2026) dan dapat diulang dengan perintah `python -m experiments.ga_train --out-dir results`.

**Tabel 3. Parameter Algoritma Genetika**

| Parameter | Nilai |
|---|---|
| Ukuran populasi | 20 |
| Jumlah generasi | 30 |
| Inisialisasi gen | acak seragam [−1; 1] |
| Seleksi | turnamen, k = 3 |
| Crossover | BLX-α, α = 0,5, peluang 0,9 |
| Mutasi | Gaussian per gen, peluang 0,2, σ = 0,15 |
| Elitisme | 2 individu |
| Lawan evaluasi fitness | Alpha-Beta H2 dan Alpha-Beta H1, kedalaman 4 |
| Game per kromosom per generasi | 2 lawan × 8 pembukaan × 2 sisi = 32 |
| Langkah acak pembukaan | 6 |
| Seed | 2026 |

**Pemilihan bobot akhir.** Karena fitness dihitung dari sampel game yang berbeda tiap generasi, kromosom terbaik di satu generasi bisa unggul karena kebetulan. Maka kromosom terbaik dari 10 generasi terakhir dievaluasi ulang pada 50 pembukaan validasi yang tidak pernah dipakai saat pelatihan (200 game per kandidat), bersama bobot setara H2 sebagai rujukan. Kandidat dengan fitness validasi tertinggi dipakai sebagai bobot Model 3 dan disimpan di `results/ga_weights.json`.

---

## C. BAB 3 EKSPERIMEN DAN PEMBAHASAN

### 3.1 Setup Eksperimen

**Kode dan data.** Seluruh kode, data hasil, dan perintah untuk mengulang eksperimen tersedia di repositori GitHub https://github.com/alkhalifi-nfs/kka-midterm-project. Semua angka di Bab 3 berasal dari berkas di folder `results/` pada commit `cbbbe49`, dan setiap berkas hasil disertai berkas `.meta.json` yang mencatat parameter, commit kode, dan lingkungan. Kode diuji dengan 234 *unit test*. Untuk mesin permainan, pengujian ini mencakup uji silang 1.000 game acak terhadap implementasi rujukan yang ditulis terpisah, dan untuk agen mencakup uji kesamaan Minimax dengan rumus V(s, d) serta kesamaan Alpha-Beta dengan Minimax.

**Lingkungan.** Laptop dengan prosesor Intel Core i7-12700H (14 inti, 20 *thread*), RAM 16 GB, Windows 11, Python 3.12.10, dan numpy 2.5.4.

**Agen yang diuji.**

| Nama agen | Isi |
|---|---|
| `random` | memilih langkah legal secara acak |
| `greedy` | memilih langkah dengan selisih lumbung terbesar setelah satu langkah |
| `minimax`, `minimax_h1` | Model 1 dengan H2 dan dengan H1 |
| `alphabeta`, `alphabeta_h1` | Model 2 (move ordering, TT, iterative deepening) dengan H2 dan dengan H1 |
| `ga` | Model 3: Model 2 dengan evaluasi 6 fitur berbobot hasil GA |

**Tiga eksperimen.**

1. **Pengukuran pencarian (subbab 3.2 dan 3.3).** 500 posisi uji non-terminal diambil dari permainan acak (seed 42, 4 sampai 40 langkah acak; `results/positions_seed42_n500.json`). Pada setiap posisi dan setiap kedalaman 1 sampai 6, enam konfigurasi pencarian memilih langkah: Minimax, Alpha-Beta polos, Alpha-Beta + move ordering, Alpha-Beta + TT tanpa ordering, Alpha-Beta + ordering + TT, dan Model 2 lengkap (+ iterative deepening). Semua memakai H2, TT dikosongkan sebelum setiap pencarian, dan dijalankan dalam satu proses agar pengukuran waktu tidak terganggu (`results/search_bench*`).
2. **Turnamen utama (subbab 3.4 dan 3.5).** Ketujuh agen bertanding *round-robin* pada kedalaman 4 tanpa batas waktu. Setiap pasangan bermain dari 100 pembukaan acak × 3 seed (42, 123, 2026), masing-masing dua kali dengan sisi ditukar, sehingga ada 600 game per pasangan dan 12.600 game total (`results/tournament_final.csv`).
3. **Turnamen RQ3 (subbab 3.5).** Minimax, Alpha-Beta, dan GA bertanding dengan batas waktu 0,1 detik per langkah dan tanpa batas kedalaman, dengan protokol pembukaan yang sama (1.800 game, 8 proses paralel; `results/rq3/`).

**Metrik.**

- **Node:** banyaknya state yang dikunjungi selama satu pencarian, termasuk akar dan daun.
- **Effective branching factor (EBF):** nilai b* yang memenuhi N = 1 + b* + b*² + ... + b*^d, dengan N rata-rata node dan d kedalaman (Russell & Norvig, 2021).
- **Win rate:** (menang + 0,5 × seri) / jumlah game, dengan interval kepercayaan 95% Wilson (Wilson, 1927).
- **Elo:** rating Bradley-Terry (Bradley & Terry, 1952) yang diestimasi dengan algoritma MM (Hunter, 2004) dan dinyatakan pada skala Elo (Elo, 1978) dengan rata-rata 1500, plus interval bootstrap 95% dari 1.000 resample (Efron, 1979).
- **Aturan keputusan:** sebuah agen dinyatakan lebih kuat hanya bila interval Wilson win rate langsungnya tidak memuat 50% **dan** interval Elo kedua agen tidak tumpang tindih.

### 3.2 Hasil Minimax dan Uji Kebenaran Minimax Sama dengan Alpha-Beta

**Pertumbuhan pohon Minimax.** Rata-rata node Minimax per posisi naik dari 5 pada kedalaman 1 menjadi 13.809 pada kedalaman 6, dengan EBF 4,29 sampai 4,71 (Tabel 4). EBF ini lebih kecil dari batas teoretis 7 karena posisi uji rata-rata memiliki lebih sedikit lubang berisi, dan sebagian cabang berakhir lebih awal karena permainan selesai. Waktu Minimax naik kira-kira lima kali lipat per ply, dari 7,5 ms pada kedalaman 4 menjadi 188,7 ms pada kedalaman 6.

**Uji kesamaan pada posisi uji.** Pada seluruh 3.000 kasus (500 posisi × 6 kedalaman), kelima konfigurasi Alpha-Beta memilih **langkah yang sama dan nilai akar yang sama persis** dengan Minimax, termasuk konfigurasi yang memakai TT (`results/search_bench_tabel.md`). Hasil ini sesuai dengan sifat Alpha-Beta yang hanya memangkas cabang yang tidak memengaruhi keputusan (Knuth & Moore, 1975), dan menunjukkan bahwa aturan pemutus seri di akar (subbab 2.2.2) berhasil dipertahankan walaupun urutan ekspansi diubah oleh move ordering. Secara teori, konfigurasi dengan TT boleh berbeda dari Minimax karena entri dari pencarian yang lebih dalam dapat dipakai ulang (subbab 2.3.4). Pada 500 posisi uji hal itu tidak pernah mengubah keputusan.

**Uji kesamaan pada turnamen.** Pada turnamen utama (kedalaman 4), `minimax` dan `alphabeta` memiliki rating Elo yang identik (1663,4) dan bermain seri sempurna satu sama lain (294 menang, 12 seri, 294 kalah). Melawan setiap lawan lain, hasil keduanya identik sampai jumlah langkah totalnya, misalnya 562/2/36 dengan 16.845 langkah melawan Greedy dan 286/14/300 dengan 20.780 langkah melawan GA. Artinya, kedua agen memainkan permainan yang sama langkah demi langkah. Pasangan `minimax_h1` dan `alphabeta_h1` menunjukkan pola yang sama. Kedalaman rata-rata `alphabeta` tercatat 3,91, bukan 4, karena *iterative deepening* berhenti lebih awal ketika pohon sudah habis sampai akhir permainan (subbab 2.3.5). Langkah yang dipilih tetap sama.

### 3.3 Analisis Pruning, EBF, dan Transposition Table

**Tabel 4. Rata-rata node per posisi dan persentasenya terhadap Minimax (500 posisi, H2)**

| Kedalaman | Minimax | Alpha-Beta polos | + move ordering | + TT tanpa ordering | + ordering + TT | Model 2 lengkap (+ ID) |
|---|---|---|---|---|---|---|
| 2 | 25 (100%) | 18 (73,7%) | 16 (62,5%) | 18 (73,7%) | 16 (62,5%) | 22 (89,4%) |
| 3 | 118 (100%) | 59 (49,7%) | 38 (32,2%) | 59 (49,7%) | 38 (32,2%) | 62 (52,8%) |
| 4 | 570 (100%) | 177 (31,1%) | 88 (15,4%) | 176 (30,9%) | 87 (15,3%) | 150 (26,3%) |
| 5 | 2.795 (100%) | 525 (18,8%) | 195 (7,0%) | 519 (18,6%) | 192 (6,9%) | 330 (11,8%) |
| 6 | 13.809 (100%) | 1.513 (11,0%) | 424 (3,1%) | 1.489 (10,8%) | 416 (3,0%) | 690 (5,0%) |

**Tabel 5. Effective branching factor dan waktu rata-rata per pencarian pada kedalaman 6**

| Konfigurasi | EBF | Waktu (ms) |
|---|---|---|
| Minimax | 4,71 | 188,69 |
| Alpha-Beta polos | 3,18 | 29,91 |
| + move ordering | 2,52 | 9,98 |
| + TT tanpa ordering | 3,17 | 29,96 |
| + ordering + TT | 2,51 | 9,85 |
| Model 2 lengkap (+ ID) | 2,76 | 16,39 |

**Gambar 1.** Rata-rata node per posisi terhadap kedalaman, skala logaritmik (`results/search_bench_nodes.png`). Garis "Alpha-Beta polos" dan "+ TT tanpa ordering" serta garis "+ move ordering" dan "+ ordering + TT" hampir berimpit.

**Pruning.** Alpha-Beta tanpa tambahan apa pun mengurangi node menjadi 11,0% dari Minimax pada kedalaman 6 dan menurunkan EBF dari 4,71 menjadi 3,18. Penghematan relatif bertambah besar seiring kedalaman (73,7% node tersisa pada kedalaman 2, 11,0% pada kedalaman 6), karena setiap pemangkasan di dekat akar membuang subpohon yang makin besar.

**Move ordering.** Move ordering (Tabel 2) adalah komponen dengan kontribusi terbesar setelah pruning: node turun dari 11,0% menjadi 3,1% dari Minimax dan EBF turun menjadi 2,52. Nilai ini mendekati batas ideal Alpha-Beta dengan urutan sempurna, yaitu sekitar akar dari faktor percabangan Minimax (√4,71 ≈ 2,17) (Knuth & Moore, 1975). Waktu pada kedalaman 6 turun dari 188,69 ms (Minimax) menjadi 9,98 ms, sekitar 19 kali lebih cepat, walaupun biaya per node naik karena semua anak harus dibangkitkan dulu untuk diurutkan.

**Transposition table.** Kontribusi TT sangat kecil. Dengan ordering, node pada kedalaman 6 hanya turun dari 3,1% menjadi 3,0%, dan tanpa ordering dari 11,0% menjadi 10,8%. Rata-rata hanya terjadi 1,8 TT hit per pencarian pada konfigurasi ordering + TT (4,4 tanpa ordering). Isi TT terbesar 2.354 entri, sangat jauh di bawah kapasitas 2²⁰ entri, sehingga sedikitnya hit bukan disebabkan TT yang penuh. Penjelasan yang paling mungkin adalah posisi yang sama jarang dicapai melalui urutan langkah berbeda dalam beberapa ply: satu langkah congklak dapat mengubah banyak lubang sekaligus melalui menabur lanjutan dan tembak, sehingga dua urutan langkah yang berbeda hampir selalu menghasilkan papan yang berbeda. Penjelasan ini belum diuji secara langsung.

**Iterative deepening.** Pada kedalaman tetap, iterative deepening justru menambah node (3,0% menjadi 5,0% pada kedalaman 6) karena kedalaman 1 sampai d − 1 ikut dicari, dan langkah terbaik dari iterasi sebelumnya tidak cukup memperbaiki urutan untuk menutup biaya itu. Manfaatnya baru muncul bila ada batas waktu, yaitu selalu tersedia langkah yang sah dan kedalaman menyesuaikan waktu (subbab 3.5, RQ3).

### 3.4 Analisis GA

**Konvergensi.** Gambar 2 menunjukkan fitness terbaik dan rata-rata populasi per generasi. Pada generasi pertama, rata-rata fitness populasi 26,8 dengan simpangan baku 17,2, karena bobot acak banyak yang buruk (misalnya memberi bobot negatif pada selisih lumbung). Pada generasi 2 sampai 5, rata-rata naik ke kisaran 39 sampai 45, dan sejak generasi 7 rata-rata umumnya berkisar 49 sampai 54, kecuali beberapa generasi yang lebih tinggi yang dibahas di bawah. Rata-rata 10 generasi terakhir adalah 54,2 dengan simpangan baku 3,3, yang menandakan populasi sudah seragam. Fitness sekitar 50 berarti seimbang dengan lawan (kira-kira separuh menang, selisih biji mendekati nol).

**Gambar 2.** Kurva konvergensi Algoritma Genetika (`results/ga_convergence.png`).

Lonjakan pada generasi 6, 20 sampai 21, 25 sampai 26, dan 30 terjadi pada fitness terbaik **dan** rata-rata populasi sekaligus. Karena seluruh populasi naik bersamaan, lonjakan ini disebabkan set pembukaan generasi tersebut yang kebetulan lebih menguntungkan, bukan karena populasi tiba-tiba menjadi lebih kuat. Ini konsekuensi dari mengganti pembukaan setiap generasi.

**Validasi.** Tabel 6 merangkum evaluasi ulang pada 50 pembukaan validasi (200 game per kandidat).

**Tabel 6. Hasil validasi kandidat bobot (sumber: `results/ga_validation.csv`)**

| Kandidat | Fitness | Win rate | Margin rata-rata |
|---|---|---|---|
| Terbaik generasi 23 (dipilih) | 57,1 | 53,0% | 3,6 |
| Terbaik generasi 24 | 56,1 | 53,5% | 2,1 |
| Terbaik generasi 22 | 55,0 | 52,5% | 2,5 |
| Kandidat lainnya (generasi 20, 21, 25 sampai 29) | 52,2 sampai 54,7 | 49,0% sampai 51,5% | 1,1 sampai 3,1 |
| H2 (bobot manual, rujukan) | 52,4 | 51,5% | 0,9 |

Semua kandidat, termasuk H2, berada dalam rentang fitness yang sempit (52,2 sampai 57,1). Dengan 200 game, galat baku win rate sekitar 3,5 poin persentase, sehingga selisih antara kandidat terbaik dan H2 (53,0% dan 51,5%) masih dalam batas variasi acak. Selain itu, kandidat terbaik dipilih sebagai maksimum dari 10 kandidat pada data validasi yang sama, sehingga fitness validasinya cenderung sedikit terlalu optimistis.

**Bobot hasil evolusi dibandingkan bobot manual.**

**Tabel 7. Bobot H2 (dalam ruang 6 fitur) dan bobot hasil GA**

| Fitur | H2 manual | Hasil GA |
|---|---|---|
| f1 selisih lumbung | 1,00 | 1,00 |
| f2 selisih biji di sisi | 0,30 | −0,04 |
| f3 selisih peluang giliran tambahan | 0,50 | 0,09 |
| f4 peluang tembak agen | 0,20 | −0,25 |
| f5 ancaman tembak lawan | −0,20 | 0,37 |
| f6 selisih mobilitas | 0,00 | 0,94 |

GA mempertahankan selisih lumbung sebagai fitur utama (bobot pada batas atas 1,00) dan memberi bobot besar pada mobilitas (0,94), fitur yang tidak dipakai H2. Sebaliknya, selisih biji di sisi dan peluang giliran tambahan nyaris diabaikan. Tanda f4 dan f5 berlawanan dengan dugaan awal di subbab 2.4.1: peluang tembak agen diberi bobot negatif dan ancaman tembak lawan diberi bobot positif. Karena banyak bobot yang sangat berbeda menghasilkan fitness yang hampir sama (Tabel 6), bobot individual sebaiknya tidak ditafsirkan sebagai "pentingnya" fitur. Landskap fitness yang datar ini konsisten dengan temuan subbab 3.5 bahwa pada kedalaman 4, perbedaan fungsi evaluasi hanya berpengaruh kecil.

**Biaya pelatihan.** Seluruh pelatihan (30 generasi × 20 kromosom × 32 game ditambah validasi) selesai dalam 195,5 detik dengan 19 proses paralel. Bobot hanya dilatih sekali dan tidak menambah biaya saat bermain: waktu per langkah GA (8,7 ms) hampir sama dengan Alpha-Beta H2 (8,3 ms) pada turnamen utama.

**Hasil di turnamen.** Pada turnamen utama, `ga` menang 51,2% melawan `alphabeta` (300 menang, 14 seri, 286 kalah) dengan interval Wilson [47,2%; 55,1%], dan pada turnamen RQ3 50,5% [46,5%; 54,5%]. Kedua interval memuat 50%, dan interval Elo `ga` [1662,1; 1688,5] tumpang tindih dengan `alphabeta` [1651,5; 1676,9]. Menurut aturan keputusan subbab 3.1, **bobot hasil GA tidak terbukti lebih kuat daripada bobot manual H2**.

### 3.5 Perbandingan Lintas Model

**Protokol.** Setiap pembukaan dimainkan dua kali dengan sisi ditukar, sehingga keunggulan pemain pertama dan keunggulan pembukaan saling meniadakan. Pembukaan diturunkan hanya dari pasangan (seed, nomor pembukaan) dan sama untuk semua pasangan agen. Dari 300 pembukaan yang diminta, 299 berbeda (satu pembukaan muncul dua kali). Tidak ada game yang berakhir karena agen gagal (*forfeit* = 0) dan tidak ada game yang menyentuh batas 300 langkah. Rata-rata satu game berlangsung 31,6 langkah.

**Tabel 8. Rating Elo turnamen utama (kedalaman 4, 12.600 game)**

| Peringkat | Agen | Elo | Interval bootstrap 95% | Skor |
|---|---|---|---|---|
| 1 | ga | 1675,6 | [1662,1; 1688,5] | 66,7% |
| 2 | alphabeta | 1663,4 | [1651,5; 1676,9] | 65,2% |
| 2 | minimax | 1663,4 | [1651,5; 1676,9] | 65,2% |
| 4 | alphabeta_h1 | 1659,5 | [1646,8; 1672,2] | 64,7% |
| 4 | minimax_h1 | 1659,5 | [1646,1; 1671,4] | 64,7% |
| 6 | greedy | 1199,0 | [1181,6; 1216,3] | 18,3% |
| 7 | random | 979,6 | [953,7; 1006,1] | 5,3% |

**Gambar 3.** Matriks win rate baris melawan kolom (`results/figures/winrate_heatmap.png`).

**Gambar 4.** Rating Elo dengan interval bootstrap 95% (`results/figures/elo_bar.png`).

**Tabel 9. Pasangan kunci pada turnamen utama (600 game per pasangan)**

| Agen | Lawan | Menang / Seri / Kalah | Win rate | Wilson 95% |
|---|---|---|---|---|
| ga | alphabeta | 300 / 14 / 286 | 51,2% | [47,2%; 55,1%] |
| alphabeta | minimax | 294 / 12 / 294 | 50,0% | [46,0%; 54,0%] |
| alphabeta | alphabeta_h1 | 299 / 8 / 293 | 50,5% | [46,5%; 54,5%] |
| minimax | minimax_h1 | 299 / 8 / 293 | 50,5% | [46,5%; 54,5%] |
| alphabeta | greedy | 562 / 2 / 36 | 93,8% | [91,6%; 95,5%] |
| alphabeta | random | 583 / 2 / 15 | 97,3% | [95,7%; 98,4%] |
| greedy | random | 473 / 20 / 107 | 80,5% | [77,1%; 83,5%] |

Matriks lengkap 7 × 7 dan rincian semua pasangan ada di `report/tabel_hasil.md`.

**Tiga kelompok kekuatan.** Hasil membentuk tiga kelompok yang jelas: kelima agen pencarian (Elo 1659 sampai 1676), Greedy (1199), dan Random (980). Agen pencarian menang 93,8% sampai 94,6% melawan Greedy dan 97,3% sampai 97,8% melawan Random, dengan interval yang jauh dari 50%. Sebaliknya, di dalam kelompok agen pencarian semua interval Elo tumpang tindih dan semua win rate langsung berada antara 47,2% dan 52,8%, sehingga **tidak ada agen pencarian yang terbukti lebih kuat dari yang lain pada kedalaman yang sama.**

**H1 dan H2.** Pada model pencarian yang sama, H2 menang 50,5% [46,5%; 54,5%] melawan H1, baik pada Minimax maupun Alpha-Beta. Fitur tambahan H2 tidak memberi keunggulan yang terukur pada kedalaman 4. Penjelasan yang mungkin adalah pencarian empat ply sudah "melihat" sebagian besar giliran tambahan dan tembakan yang ingin ditangkap oleh f3 dan f4, sehingga informasi itu sudah tercermin pada selisih lumbung di daun pohon.

**Beban pencarian di turnamen.**

**Tabel 10. Beban pencarian per langkah pada turnamen utama**

| Agen | Node/langkah | Cutoff/langkah | Waktu/langkah (ms) |
|---|---|---|---|
| ga | 129,6 | 28,7 | 8,7 |
| alphabeta | 124,7 | 27,9 | 8,3 |
| minimax | 568,7 | 0,0 | 24,4 |
| alphabeta_h1 | 124,4 | 27,9 | 7,3 |
| minimax_h1 | 566,1 | 0,0 | 17,8 |

Pada permainan nyata, Alpha-Beta mengunjungi sekitar 4,6 kali lebih sedikit node daripada Minimax untuk keputusan yang identik (subbab 3.2). Rasio ini lebih kecil daripada pada Tabel 4 (15,3% pada kedalaman 4) karena Model 2 di turnamen memakai iterative deepening, yang menambah biaya pada kedalaman tetap (subbab 3.3).

**Batas waktu yang sama (RQ3).**

**Tabel 11. Turnamen dengan batas waktu 0,1 detik per langkah (1.800 game)**

| Agen | Elo [interval 95%] | Kedalaman rata-rata | Node/langkah | Waktu/langkah (ms) |
|---|---|---|---|---|
| ga | 1518,5 [1504,9; 1531,6] | 14,66 | 2.080,1 | 94,8 |
| alphabeta | 1513,8 [1500,4; 1526,4] | 14,88 | 2.043,4 | 93,5 |
| minimax | 1467,8 [1454,2; 1480,9] | 5,38 | 3.143,1 | 90,6 |

| Agen | Lawan | Menang / Seri / Kalah | Win rate | Wilson 95% |
|---|---|---|---|---|
| alphabeta | minimax | 336 / 5 / 259 | 56,4% | [52,4%; 60,3%] |
| ga | minimax | 341 / 7 / 252 | 57,4% | [53,4%; 61,3%] |
| ga | alphabeta | 300 / 6 / 294 | 50,5% | [46,5%; 54,5%] |

Dengan batas waktu yang sama, Alpha-Beta dan GA **mengalahkan Minimax secara signifikan**: interval Wilson keduanya berada di atas 50%, dan interval Elo keduanya tidak tumpang tindih dengan Minimax. Karena pada kedalaman yang sama Alpha-Beta dan Minimax memilih langkah yang identik (subbab 3.2), seluruh keunggulan ini berasal dari kedalaman yang dapat dicapai dalam waktu yang sama. Minimax justru mengunjungi lebih banyak node per langkah (3.143 dibanding 2.043), karena biaya per node-nya lebih murah (tanpa pengurutan dan hashing). Namun karena tidak memangkas, node itu tersebar di pohon yang lebih dangkal.

Angka kedalaman rata-rata perlu dibaca dengan hati-hati. Menjelang akhir permainan, pohon cukup kecil untuk ditelusuri sampai selesai, dan iterative deepening melaporkan kedalaman sebesar sisa panjang permainan (subbab 2.3.5). Langkah-langkah ini menaikkan rata-rata, sehingga 14,88 bukan kedalaman tipikal di posisi pertengahan. Yang dapat disimpulkan adalah urutannya: Alpha-Beta mencapai kedalaman yang jauh lebih besar daripada Minimax.

**Sensitivitas interval Elo.** Bila bootstrap dilakukan per pembukaan (seluruh game dari satu pembukaan diresampel bersama) dan bukan per game, interval Elo turnamen utama melebar, misalnya dari lebar 26,3 menjadi 35,4 poin untuk `ga` dan dari 25,4 menjadi 35,8 poin untuk `alphabeta` (`results/sensitivitas_opening/elo.csv`). Semua kesimpulan di atas tetap sama, karena interval yang tumpang tindih tetap tumpang tindih dan interval yang terpisah tetap terpisah.

### 3.6 Diskusi

**Trade-off.** Hasil eksperimen menunjukkan bahwa di congklak, kekuatan agen terutama ditentukan oleh **seberapa dalam ia mencari**, bukan oleh fungsi evaluasinya. Pada kedalaman yang sama, Minimax dan Alpha-Beta identik, H1 dan H2 setara, dan bobot GA tidak terbukti lebih baik. Pada waktu yang sama, Alpha-Beta unggul jelas atas Minimax karena mampu mencari lebih dalam. Dari komponen Model 2, pruning dan move ordering memberi hampir seluruh penghematan. TT hampir tidak membantu, tetapi biayanya juga kecil (paling banyak sekitar 2.354 entri per pencarian pada kedalaman 6). Iterative deepening menambah biaya pada kedalaman tetap, tetapi diperlukan agar agen dapat bekerja dengan batas waktu. GA membutuhkan waktu persiapan sekitar 3 menit dan tidak menambah biaya saat bermain, tetapi tidak memberi keunggulan yang terukur.

**Ancaman validitas dan keterbatasan.**

1. **Satu kali pelatihan GA.** Interval di Bab 3 menggambarkan variasi karena pemilihan pembukaan, bukan variasi antar pelatihan GA dengan seed berbeda. Kesimpulan tentang GA berlaku untuk bobot yang dilatih, bukan untuk GA secara umum.
2. **Fitness yang bising.** Dengan 32 game per kromosom per generasi, selisih fitness kecil antar kromosom tidak dapat dibedakan dari kebetulan. GA dengan lebih banyak game per evaluasi mungkin menemukan bobot yang lebih baik.
3. **Satu kedalaman dan satu batas waktu.** Turnamen utama hanya memakai kedalaman 4 dan turnamen RQ3 hanya 0,1 detik per langkah. Pada kedalaman yang lebih kecil, peran fungsi evaluasi bisa lebih besar.
4. **Rating bersifat relatif.** Elo hanya membandingkan agen di turnamen yang sama dan berubah bila agen ditambah atau dikurangi.
5. **Pembukaan acak pendek.** Posisi hasil 6 langkah acak tidak sepenuhnya mewakili permainan dari posisi awal. Satu dari 300 pembukaan muncul dua kali.
6. **Pengukuran waktu.** Waktu turnamen RQ3 adalah waktu dinding dengan 8 proses paralel, dan kedalaman yang dicapai bergantung pada kecepatan mesin. Waktu pada Tabel 5 diukur dengan satu proses.
7. **Satu varian aturan.** Hasil berlaku untuk varian 7 lubang, 7 biji, dengan menabur lanjutan, serta pengaman 200 putaran tabur dan 300 langkah (tidak ada game yang menyentuh batas 300 langkah).
8. **Penjelasan TT dan H1/H2 belum diuji langsung.** Alasan rendahnya TT hit dan setaranya H1/H2 di subbab 3.3 dan 3.5 adalah dugaan yang konsisten dengan data, bukan hasil eksperimen tersendiri.

---

## D. BAB 4 KESIMPULAN

### 4.1 Kesimpulan

Proyek ini membangun mesin congklak yang teruji dan membandingkan tiga model agen pada 500 posisi uji dan 14.400 game turnamen. Jawaban atas pertanyaan penelitian adalah sebagai berikut.

1. **RQ1.** Pada kedalaman yang sama, Alpha-Beta memilih langkah yang identik dengan Minimax pada seluruh 3.000 kasus uji dan memainkan permainan yang identik di turnamen. Pada kedalaman 6, pruning saja menyisakan 11,0% node Minimax, ditambah move ordering 3,1%, dan ditambah transposition table 3,0%. Move ordering adalah komponen terpenting setelah pruning, sedangkan kontribusi transposition table dapat diabaikan pada congklak.
2. **RQ2.** Bobot evaluasi hasil Algoritma Genetika tidak terbukti mengalahkan bobot manual H2. Win rate GA melawan Alpha-Beta H2 adalah 51,2% [47,2%; 55,1%] pada kedalaman yang sama dan 50,5% [46,5%; 54,5%] pada batas waktu yang sama, keduanya tidak signifikan. Banyak kombinasi bobot yang berbeda menghasilkan kekuatan yang hampir sama, dan H1 pun setara dengan H2.
3. **RQ3.** Dengan batas waktu 0,1 detik per langkah, Alpha-Beta dan GA mencapai kedalaman jauh lebih besar daripada Minimax dan menang secara signifikan (56,4% dan 57,4%). Harga yang dibayar kecil: transposition table paling banyak memuat sekitar 2.354 entri per pencarian pada kedalaman 6, dan pelatihan GA hanya sekali, sekitar 3 menit.

Dengan demikian, agen congklak yang kuat dengan batas waktu per langkah paling efektif dibangun dari Alpha-Beta dengan move ordering yang baik. Kontribusi terbesar berasal dari kemampuan mencari lebih dalam, bukan dari penyetelan fungsi evaluasi.

### 4.2 Saran

1. **Pelatihan GA yang lebih kuat:** beberapa seed pelatihan, lebih banyak game per evaluasi, dan lawan yang lebih beragam, agar perbedaan kecil antarbobot dapat terdeteksi.
2. **Kedalaman dan batas waktu lain:** mengulang perbandingan H1, H2, dan GA pada kedalaman 1 sampai 3, tempat fungsi evaluasi diduga lebih berpengaruh, serta pada beberapa batas waktu.
3. **Mencatat kedalaman per langkah,** bukan hanya rata-rata per game, agar kedalaman di posisi pertengahan dan di akhir permainan dapat dipisahkan.
4. **Metode lain:** Monte Carlo Tree Search, fungsi evaluasi nonlinear (misalnya jaringan saraf kecil), atau basis data posisi akhir.
5. **Varian aturan lain** (jumlah lubang atau biji berbeda, tanpa menabur lanjutan) untuk melihat apakah rendahnya manfaat transposition table merupakan sifat congklak secara umum.
6. **Uji dengan pemain manusia,** sebagai dasar tingkat kesulitan untuk game edukasi.

---

## E. TAMBAHAN DAFTAR PUSTAKA (sisipkan sesuai urutan abjad)

Bradley, R. A., & Terry, M. E. (1952). Rank analysis of incomplete block designs: I. The method of paired comparisons. *Biometrika, 39*(3/4), 324–345.

Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *The Annals of Statistics, 7*(1), 1–26. https://doi.org/10.1214/aos/1176344552

Elo, A. E. (1978). *The rating of chessplayers, past and present*. Arco Publishing.

Eshelman, L. J., & Schaffer, J. D. (1993). Real-coded genetic algorithms and interval-schemata. Dalam L. D. Whitley (Ed.), *Foundations of genetic algorithms 2* (hlm. 187–202). Morgan Kaufmann.

Hunter, D. R. (2004). MM algorithms for generalized Bradley-Terry models. *The Annals of Statistics, 32*(1), 384–406. https://doi.org/10.1214/aos/1079120141

Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association, 22*(158), 209–212. https://doi.org/10.1080/01621459.1927.10502953
