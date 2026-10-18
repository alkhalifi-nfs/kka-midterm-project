# BAB 3 (lanjutan)

## 3.5 Analisis Hasil Turnamen Akhir

> **Status draf (18 Oktober 2026).** Bagian 3.5.1, 3.5.2, dan 3.5.5 sudah lengkap dan berasal dari kode yang ada. **Bagian 3.5.3 (Hasil) dan 3.5.4 (Pembahasan) belum berisi hasil**, karena turnamen akhir belum bisa dijalankan: agen Minimax, Alpha-Beta, dan GA resmi belum ada di repositori. Tidak ada angka hasil eksperimen di berkas ini. Cakupan bagian ini adalah asumsi saya (analisis turnamen: win rate, Elo, beban pencarian); sesuaikan bila pedoman tugas mendefinisikan 3.5 secara berbeda. Isian bertanda `[...]` harus dilengkapi.

### 3.5.1 Protokol Turnamen

Seluruh agen dipertandingkan dalam turnamen *round-robin*: setiap pasangan agen yang unik bertemu, tanpa *self-play*. Untuk $k$ agen terdapat $k(k-1)/2$ pasangan. Permainan dijalankan oleh `experiments/tournament.py` dengan rancangan berikut.

**Game berpasangan dengan sisi ditukar.** Pemain pertama berpotensi memperoleh keunggulan besar pada varian ini: dari posisi awal, pembuka lubang 1 sampai 6 langsung menghasilkan 10 biji di lumbung Pemain 0 (diuji pada `tests/test_engine_rules.py`). Karena itu setiap pembukaan dimainkan dua kali untuk setiap pasangan agen, dengan sisi kedua agen ditukar, sehingga keunggulan sisi dan keunggulan pembukaan saling meniadakan pada rata-rata.

**Pembukaan acak.** Agen yang deterministik akan memainkan game yang sama berulang kali bila selalu mulai dari posisi awal. Maka setiap game dimulai dengan $m$ langkah acak (parameter `opening-plies`) yang diturunkan hanya dari pasangan (*seed*, `opening_id`). Pembukaan yang sama dipakai oleh kedua game dalam satu pasangan dan oleh semua pasangan agen. Jumlah game per pasangan agen adalah

$$N_{\text{game/pasangan}} = N_{\text{buka}} \times 2 \times N_{\text{seed}}.$$

**Reproduksibilitas.** Seed `reset()` setiap agen diturunkan dari (*seed*, `opening_id`, sisi, nama agen) dengan fungsi hash SHA-256 sehingga stabil lintas proses dan mesin. Hasil identik untuk jumlah proses paralel yang berbeda (diuji pada `tests/test_tournament.py`).

**Kegagalan agen.** Agen yang mengembalikan langkah ilegal atau melempar *exception* dicatat kalah (*forfeit*) pada game itu, dengan kolom `forfeit` dan `error` terisi, dan turnamen berlanjut. Jumlah forfeit pada turnamen akhir dilaporkan pada tabel parameter.

**Batas waktu.** Runner hanya meneruskan nilai `time_limit` dan `depth` ke agen dan tidak menegakkannya; agen membatasi diri sendiri.

**Parameter turnamen akhir.** Tabel berikut dihasilkan otomatis dari berkas meta turnamen (`results/<nama>.meta.json`) dengan `python -m experiments.report_tables --meta ...`. Jangan diketik tangan.

`[Tempel tabel "Parameter protokol turnamen" dari report/tabel_hasil.md]`

**Pembukaan yang berulang.** Banyaknya posisi pembukaan yang berbeda dibatasi oleh $m$. Pada pembukaan yang berulang, agen deterministik memainkan game yang identik, sehingga game itu bukan sampel baru dan interval kepercayaan menjadi lebih sempit daripada yang seharusnya. Runner mencetak peringatan bila ada pembukaan yang berulang, dan jumlah pembukaan yang berbeda dicatat pada baris "Pembukaan berbeda dari yang diminta" di tabel parameter. `[Tulis di sini nilai m yang dipilih dan jumlah pembukaan berbeda yang tercatat; bila ada duplikat, nyatakan.]`

### 3.5.2 Metrik dan Metode Statistik

**Win rate.** Untuk pasangan terurut (agen $i$ melawan agen $j$) dengan $w_{ij}$ kemenangan, $d_{ij}$ seri, dan $n_{ij}$ game (kedua sisi digabung), seri dihitung 0,5:

$$\hat p_{ij} = \frac{w_{ij} + \tfrac{1}{2} d_{ij}}{n_{ij}}.$$

Interval kepercayaan 95% memakai interval Wilson (Wilson, 1927) dengan $z = 1{,}96$:

$$\frac{\hat p + \frac{z^2}{2n}}{1 + \frac{z^2}{n}} \;\pm\; \frac{z}{1 + \frac{z^2}{n}} \sqrt{\frac{\hat p (1 - \hat p)}{n} + \frac{z^2}{4n^2}}.$$

Karena seri dihitung 0,5, rumus ini adalah pendekatan; seri membuat intervalnya sedikit lebih lebar dari kasus ideal.

**Rating Elo (Bradley-Terry).** Peluang agen $i$ mengalahkan agen $j$ dimodelkan sebagai (Bradley & Terry, 1952)

$$P(i \succ j) = \frac{\pi_i}{\pi_i + \pi_j},$$

dan $\pi$ diperkirakan dengan *maximum likelihood* melalui iterasi MM (Hunter, 2004):

$$\pi_i^{(t+1)} = \frac{W_i}{\sum_{j \neq i} \dfrac{n_{ij}}{\pi_i^{(t)} + \pi_j^{(t)}}},$$

dengan $W_i$ total poin agen $i$ (menang 1, seri 0,5) dan $n_{ij}$ jumlah game antara $i$ dan $j$. Setelah konvergen, $\pi$ dinormalkan agar $\sum_i \ln \pi_i = 0$ dan rating dinyatakan pada skala Elo (Elo, 1978):

$$R_i = 1500 + 400 \log_{10} \pi_i.$$

Dengan normalisasi itu, rata-rata rating seluruh agen tepat 1500. Rating hanya bermakna relatif terhadap agen lain pada turnamen yang sama. Selisih rating menentukan peluang menang:

$$P(i \succ j) = \frac{1}{1 + 10^{-(R_i - R_j)/400}}.$$

| Selisih Elo | 50 | 100 | 200 | 300 | 400 |
|---|---|---|---|---|---|
| Peluang menang agen yang lebih kuat (%) | 57,1 | 64,0 | 76,0 | 84,9 | 90,9 |

(Tabel di atas dihitung dari rumus, bukan hasil eksperimen. Sebagai pemeriksaan implementasi, data sintetis dengan win rate 75% menghasilkan selisih 190,8 = $400 \log_{10} 3$; lihat `tests/test_analyze.py`.)

**Kapan estimasi tidak ada.** MLE Bradley-Terry hanya ada bila graf "agen $i$ pernah mengalahkan agen $j$" terhubung kuat. Bila ada agen yang tidak pernah menang atau tidak pernah kalah, estimasi akan menuju tak hingga. Dalam kasus itu, analisis memakai penghalusan: setiap pasangan yang pernah bertemu diberi 0,5 poin tambahan untuk kedua arah, dan kolom `regularized` pada `results/elo.csv` bernilai `True`. Nilai Elo dan terutama batas intervalnya pada kasus itu bergantung pada nilai penghalusan, bukan semata pada data.

**Interval bootstrap untuk Elo.** Interval 95% diperoleh dari 1.000 resample *bootstrap* (Efron, 1979): game diambil dengan pengembalian sebanyak jumlah game, rating dihitung ulang, lalu persentil ke-2,5 dan ke-97,5 diambil. Mode bawaan meresampel game satu per satu. Mode kedua (`--bootstrap-unit opening`) meresampel seluruh game dari satu pembukaan sekaligus, dan dipakai sebagai analisis sensitivitas karena game yang berbagi pembukaan tidak sepenuhnya independen.

**Beban pencarian.** Dari `agent.metrics` dihitung rata-rata node per langkah, *cutoff* per langkah, dan kedalaman yang dicapai, masing-masing sebagai jumlah dibagi jumlah keputusan, hanya pada game yang agennya melaporkan metrik tersebut. Waktu per langkah diukur oleh runner (waktu dinding pemanggilan `choose_move`) sehingga tersedia untuk semua agen. `[Faktor percabangan efektif (EBF) disebut pada README sebagai metrik, tetapi belum diimplementasikan di experiments/analyze.py; putuskan apakah diperlukan sebelum bagian ini dianggap lengkap.]`

### 3.5.3 Hasil

> **BELUM ADA DATA.** Bagian ini diisi dari file di `results/` setelah turnamen akhir dijalankan. Jangan menulis angka dari ingatan atau dari uji asap.

Cara menghasilkan seluruh bahan bagian ini (setelah turnamen selesai; perintah lengkap ada di `docs/turnamen_final.md`):

```bash
python -m experiments.analyze results/<turnamen_akhir>.csv --out-dir results
python -m experiments.report_tables --results-dir results \
    --meta results/<turnamen_akhir>.meta.json --out report/tabel_hasil.md
```

Isi yang ditempel dari `report/tabel_hasil.md`:

- `[Tabel 3.5.1: Parameter protokol turnamen]`
- `[Tabel 3.5.2: Matriks win rate baris melawan kolom]`
- `[Tabel 3.5.3: Rincian pasangan agen dengan interval Wilson]`
- `[Tabel 3.5.4: Rating Elo dengan interval bootstrap]`
- `[Tabel 3.5.5: Beban pencarian per langkah]`

Gambar (dihasilkan otomatis): `results/figures/winrate_heatmap.png`, `results/figures/elo_bar.png`, `results/figures/nodes_per_move.png`.

Aturan penulisan narasi: setiap angka pada kalimat disalin dari tabel di atas, dan setiap klaim perbedaan menyebut interval kepercayaannya.

### 3.5.4 Pembahasan

> **Kerangka, belum berisi kesimpulan.** Tabel berikut menunjukkan pertanyaan yang harus dijawab dari data dan cara memutuskannya. Kolom keputusan adalah aturan analisis, bukan hasil.

| Pertanyaan (rumusan masalah) | Bahan di Bab 3.5.3 | Aturan keputusan |
|---|---|---|
| Seberapa besar Alpha-Beta mengurangi beban pencarian dibanding Minimax? (RM 2) | Tabel beban pencarian, `nodes_per_move.png` | Bandingkan node per langkah dengan menyebut kedalaman yang dicapai tiap agen; Alpha-Beta dengan tabel transposisi dan *iterative deepening* dapat mencapai kedalaman berbeda, sehingga perbandingan node pada kedalaman berbeda tidak setara. Keputusan Minimax dan Alpha-Beta pada kedalaman sama diuji terpisah pada uji kebenaran. |
| Apakah bobot hasil GA lebih kuat daripada bobot manual? (RM 3) | Win rate langsung Alpha-Beta vs GA, Elo kedua agen | Klaim "lebih kuat" hanya bila interval Wilson win rate langsung tidak memuat 0,5 **dan** interval bootstrap kedua Elo tidak tumpang tindih. Jika tidak, tulis bahwa perbedaan belum terbukti. |
| Bagaimana peringkat keseluruhan? (RM 4) | Tabel Elo, heatmap | Laporkan peringkat bersama intervalnya. Peringkat dua agen dengan interval tumpang tindih tidak boleh dinyatakan berbeda. |
| Apakah hasil dapat dipercaya? | Tabel parameter, kolom `forfeit`, `hit_move_cap`, `regularized` | Periksa: jumlah forfeit (idealnya nol, bila tidak nol jelaskan penyebabnya), game yang kena batas 300 langkah, apakah Elo diperoleh dengan penghalusan, jumlah pembukaan yang berbeda, dan kesesuaian interval bootstrap per game dengan per pembukaan. |

Pemeriksaan kewarasan (*sanity check*, bukan hipotesis hasil): agen pembanding dasar seharusnya tidak mengalahkan agen pencarian yang sah pada kedalaman yang memadai. Bila hal itu terjadi, curigai bug pada agen atau fungsi evaluasi sebelum menyimpulkan hal lain.

`[Tulis pembahasan setelah data ada. Sertakan penjelasan penyebab hanya bila didukung data atau pengamatan yang bisa ditunjukkan; hindari penjelasan spekulatif.]`

### 3.5.5 Ancaman Validitas dan Keterbatasan

1. **Rating bersifat relatif.** Elo hanya membandingkan agen yang ikut turnamen ini. Rating tidak menyatakan kekuatan absolut dan akan berubah bila agen ditambah atau dikurangi.
2. **Pembukaan acak pendek.** Posisi hasil $m$ langkah acak tidak mewakili distribusi posisi pada permainan nyata. Hasil dapat berbeda untuk nilai $m$ lain atau untuk game penuh dari posisi awal.
3. **Pembukaan berulang.** Jika banyak pembukaan yang sama, game yang identik pada agen deterministik membuat sampel efektif lebih kecil daripada jumlah game. Periksa tabel parameter.
4. **Ketergantungan antar game.** Pembukaan yang sama dipakai oleh seluruh pasangan agen dan oleh kedua game dalam satu pasangan. Bootstrap per game mengabaikan ketergantungan ini, dan arah pengaruhnya terhadap lebar interval bergantung pada agen (korelasi skor dalam satu pembukaan bisa positif maupun negatif). Karena itu interval per game dan per pembukaan keduanya dihitung dan dibandingkan sebagai analisis sensitivitas (kolom `bootstrap_unit` pada `elo.csv`). `[Tulis perbandingan keduanya dari data turnamen akhir.]`
5. **Penghalusan Elo.** Bila ada agen yang hampir tidak pernah kalah, batas atas interval Elo ditentukan oleh nilai penghalusan, bukan oleh data (kolom `regularized`).
6. **Pengukuran waktu.** Waktu per langkah adalah waktu dinding pada turnamen paralel. Beban mesin dan persaingan antar proses memengaruhinya, sehingga angka waktu lebih tepat dipakai untuk perbandingan relatif daripada nilai absolut. `[Bila waktu menjadi klaim utama, jalankan pengukuran waktu terpisah dengan satu proses.]`
7. **Satu kali pelatihan GA.** Interval pada tabel menggambarkan variasi karena pemilihan pembukaan, bukan variasi antar pelatihan Algoritma Genetika dengan seed berbeda. Kesimpulan tentang bobot GA berlaku untuk bobot yang dilatih, bukan untuk GA secara umum.
8. **Pengaman terminasi.** Batas 200 putaran tabur dan 300 langkah mengubah aturan pada kasus langka. Jumlah game yang kena batas 300 langkah dilaporkan (kolom `hit_move_cap`); batas 200 putaran tidak dicatat per game pada CSV. `[Tulis jumlah yang tercatat.]`
9. **Pengaturan agen.** Hasil berlaku untuk kedalaman, batas waktu, dan bobot yang diuji, bukan untuk setiap konfigurasi.
