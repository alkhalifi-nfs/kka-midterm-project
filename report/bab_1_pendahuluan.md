# BAB 1: PENDAHULUAN

> **Status draf:** isian bertanda `[...]` harus dilengkapi atau disesuaikan sebelum dikumpulkan. Status verifikasi tiap sitasi ada di `report/referensi.md`. Bab ini sengaja tidak memuat angka hasil eksperimen; angka hasil hanya muncul di Bab 3.

## 1.1 Latar Belakang

Congklak adalah permainan papan tradisional dua pemain yang dikenal di Indonesia dan termasuk keluarga permainan *mancala* (Wikipedia, "Southeast Asian mancala"). Pemain mengambil seluruh biji dari salah satu lubang miliknya lalu menaburkannya satu per satu ke lubang berikutnya, dan hasil akhir sebuah langkah ditentukan oleh lubang tempat biji terakhir jatuh. Aturan rinci Congklak dilaporkan bervariasi antar sumber, misalnya jumlah biji awal serta perlakuan terhadap tembak dan lubang kosong `[sumber pembanding belum diperiksa langsung; lihat report/referensi.md]`. Karena itu proyek ini menetapkan satu varian secara eksplisit: papan 14 lubang kecil dan 2 lumbung, 7 biji di setiap lubang kecil (total 98 biji), dengan aturan giliran tambahan, menabur lanjutan, dan tembak sebagaimana tertulis pada `docs/rules.md` dan dirumuskan secara formal pada Bab 2.1.

Dari sudut pandang kecerdasan artifisial, varian ini adalah permainan dua pemain, *zero-sum*, deterministik, dan berinformasi sempurna, sehingga dapat diselesaikan dengan pencarian adversarial seperti Minimax dan *Alpha-Beta Pruning* (Russell & Norvig, edisi ke-4; Knuth & Moore, 1975). Dua ciri membuat Congklak berbeda dari permainan klasik yang berganti giliran pada setiap langkah. Pertama, biji terakhir yang jatuh di lumbung sendiri memberi giliran tambahan, sehingga simpul MAX dapat langsung diikuti simpul MAX lagi (Bab 2.1). Kedua, menabur lanjutan membuat satu langkah dapat berupa rangkaian beberapa putaran tabur, sehingga hasil sebuah langkah sulit diperkirakan tanpa menjalankannya. Faktor percabangan dibatasi paling banyak 7 per simpul, tetapi batas atas kasar ukuran ruang keadaan mencapai $\approx 3{,}62 \times 10^{18}$ (Bab 2.1), sehingga pencarian eksak hingga akhir permainan tidak diasumsikan layak dalam batas waktu per langkah. Pencarian dengan kedalaman terbatas dan fungsi evaluasi heuristik menjadi pendekatan yang wajar.

Efisiensi pencarian dapat ditingkatkan dengan beberapa teknik standar: pengurutan langkah (*move ordering*) agar pemangkasan lebih banyak terjadi, tabel transposisi untuk menghindari evaluasi ulang posisi yang sama, dan *iterative deepening* agar pencarian memanfaatkan batas waktu. Tabel transposisi memerlukan kunci posisi yang murah dihitung, dan *Zobrist hashing* adalah metode yang lazim dipakai untuk itu (Zobrist, 1970). Teknik-teknik serupa, termasuk pengurutan langkah dan tabel transposisi, dilaporkan pada penyelesaian Kalah, permainan mancala lain, untuk beberapa konfigurasi awal hingga 6 lubang dan 5 biji per lubang (Irving, Donkers & Uiterwijk, 2000). Pada pencarian berkedalaman terbatas, kualitas fungsi evaluasi menentukan kekuatan bermain, sedangkan menyusun bobot fitur evaluasi secara manual tidak mudah. Algoritma Genetika (Holland, 1975) dapat dipakai untuk mencari bobot tersebut melalui seleksi, persilangan, dan mutasi berdasarkan hasil permainan antar kandidat (*self-play*).

Berdasarkan hal tersebut, proyek ini membandingkan tiga model pada varian Congklak yang sama: (1) Minimax berkedalaman terbatas, (2) Alpha-Beta dengan *move ordering*, tabel transposisi (Zobrist), dan *iterative deepening*, serta (3) Alpha-Beta dengan bobot fungsi evaluasi hasil Algoritma Genetika. Agen Random dan Greedy ditambahkan sebagai pembanding dasar. Perbandingan dilakukan lewat turnamen otomatis yang dirancang agar adil dan dapat direproduksi: pembukaan acak yang sama dimainkan dua kali dengan sisi ditukar, peringkat dihitung dengan model Bradley-Terry yang dinyatakan dalam skala Elo, dan ketidakpastiannya dinyatakan dengan interval kepercayaan (Bab 3.5).

## 1.2 Rumusan Masalah

1. Bagaimana varian Congklak yang ditetapkan (papan 7 lubang per pemain, 7 biji per lubang, giliran tambahan, menabur lanjutan, tembak) dirumuskan sebagai masalah pencarian adversarial dengan transisi giliran non-alternatif?
2. Seberapa besar *Alpha-Beta Pruning* yang dilengkapi *move ordering*, tabel transposisi, dan *iterative deepening* mengurangi beban pencarian (jumlah simpul, waktu, kedalaman yang dicapai) dibandingkan Minimax pada pengaturan yang sebanding?
3. Apakah bobot fungsi evaluasi hasil Algoritma Genetika menghasilkan agen yang lebih kuat daripada fungsi evaluasi dengan bobot manual?
4. Bagaimana kekuatan relatif ketiga model dan kedua agen pembanding dapat diukur secara adil dan dapat direproduksi?

## 1.3 Tujuan

1. Merumuskan Congklak varian tersebut secara formal sebagai masalah pencarian adversarial dan mengimplementasikannya sebagai mesin permainan yang teruji (Bab 2.1).
2. Mengimplementasikan dan membandingkan efisiensi pencarian Minimax dan Alpha-Beta beserta teknik pendukungnya.
3. Melatih bobot fungsi evaluasi dengan Algoritma Genetika dan menguji pengaruhnya terhadap kekuatan bermain.
4. Membangun kerangka turnamen otomatis dan analisis statistik (win rate, rating Elo, interval kepercayaan) untuk membandingkan seluruh agen, serta melaporkan hasilnya secara terbuka dengan keterbatasannya (Bab 3.5).

## 1.4 Batasan Masalah

1. Hanya satu varian aturan yang dipakai, yaitu yang tertulis pada `docs/rules.md`. Hasil tidak otomatis berlaku untuk varian Congklak atau Kalah lain.
2. Permainan dua pemain dengan informasi sempurna. Agen tidak belajar atau menyesuaikan diri selama turnamen; bobot hasil Algoritma Genetika dibekukan setelah pelatihan `[konfirmasi dengan pemilik Bab 2.5]`.
3. Agen pencarian dibatasi kedalaman (dan/atau waktu per langkah) serta memakai fungsi evaluasi heuristik. Tidak ada klaim bahwa agen bermain optimal.
4. Dua pengaman terminasi dipakai: paling banyak 200 putaran tabur per giliran dan paling banyak 300 langkah per game. Kejadian game yang berakhir karena batas langkah dicatat pada data turnamen (kolom `hit_move_cap`).
5. Evaluasi memakai turnamen *round-robin* dengan jumlah pembukaan dan seed yang terbatas. Rating Elo bersifat relatif terhadap himpunan agen yang dipertandingkan, bukan rating absolut.
6. Implementasi dalam Python dengan pustaka numpy, pandas, matplotlib, dan pytest.

## 1.5 Manfaat

1. Memberikan rumusan formal yang eksplisit dan teruji untuk varian Congklak yang dipakai, termasuk ukuran ruang keadaan dan perilaku giliran non-alternatif.
2. Memberikan perbandingan terkontrol antara Minimax, Alpha-Beta dengan teknik pendukung, dan evaluasi hasil Algoritma Genetika pada permainan yang sama.
3. Menyediakan kerangka eksperimen yang dapat direproduksi (pembukaan acak berpasangan, seed tetap, berkas meta yang mencatat parameter dan versi kode) yang dapat dipakai ulang untuk agen lain.

## 1.6 Ketersediaan Kode dan Reproduksibilitas

Seluruh kode, tes, dan data hasil tersedia di repositori publik: **https://github.com/alkhalifi-nfs/kka-midterm-project**. Versi kode yang dipakai untuk hasil di laporan ini adalah commit `[isi: hash commit final]`. Langkah menjalankan tes dan turnamen ada pada `README.md` dan `docs/turnamen_final.md`. Setiap file turnamen di `results/` disertai berkas `.meta.json` yang mencatat parameter, jumlah pembukaan berbeda, versi Python dan numpy, serta hash commit tiap pemanggilan.

## 1.7 Sistematika Penulisan

`[Sesuaikan dengan struktur final laporan; judul bab di bawah belum terverifikasi terhadap pedoman tugas.]`

- **Bab 1 Pendahuluan** memuat latar belakang, rumusan masalah, tujuan, batasan, manfaat, dan ketersediaan kode.
- **Bab 2 Metodologi** memuat formalisasi permainan (2.1) serta rancangan model: Minimax (2.2), Alpha-Beta beserta *move ordering*, tabel transposisi Zobrist, dan *iterative deepening* (2.3 dan 2.4), dan fungsi evaluasi berparameter dengan Algoritma Genetika (2.5).
- **Bab 3 Hasil dan Pembahasan** memuat pelatihan Algoritma Genetika (3.1 dan 3.2), evaluasi model (3.3 dan 3.4), dan analisis hasil turnamen akhir (3.5).
- **Bab 4 Penutup** memuat kesimpulan dan saran.
