# BAB 2: METODOLOGI

## 2.1 Formalisasi Permainan Congklak sebagai Masalah Pencarian Adversarial

Permainan Congklak didefinisikan secara matematis sebagai permainan *two-player*, *zero-sum*, *deterministic*, dengan informasi sempurna (*perfect information*) dan transisi giliran non-alternatif (*non-alternating turn transitions*). Secara formal, permainan ini direpresentasikan oleh tupel $\mathcal{G} = \langle \mathcal{S}, s_0, \mathcal{P}, \text{PLAYER}, \mathcal{A}, \mathcal{T}, \text{TERMINAL}, \mathcal{U} \rangle$.

---

### 1. Representasi Ruang Keadaan (*State Representation* - $\mathcal{S}$)
Papan permainan Congklak terdiri atas 14 lubang kecil (*pits*) dan 2 lumbung utama (*stores*), sehingga terdapat total 16 slot. Suatu keadaan permainan $s \in \mathcal{S}$ direpresentasikan sebagai pasangan terurut:

$$s = (\mathbf{b}, p)$$

di mana:
- $\mathbf{b} = [b_0, b_1, \dots, b_{15}] \in \mathbb{Z}_{\ge 0}^{16}$ adalah vektor 16 dimensi yang menyatakan jumlah biji pada setiap slot papan:
  - Indeks $i \in \{0, 1, \dots, 6\}$ menyatakan 7 lubang kecil milik **Pemain 0** ($P_0$).
  - Indeks $i = 7$ menyatakan lumbung utama (*store*) milik **Pemain 0**.
  - Indeks $i \in \{8, 9, \dots, 14\}$ menyatakan 7 lubang kecil milik **Pemain 1** ($P_1$).
  - Indeks $i = 15$ menyatakan lumbung utama (*store*) milik **Pemain 1**.
- $p \in \mathcal{P} = \{0, 1\}$ adalah indikator pemain aktif yang memegang giliran pada keadaan $s$, dengan fungsi $\text{PLAYER}(s) = p$.

**Keadaan Awal ($s_0$):**
Permainan dimulai oleh Pemain 0 ($p = 0$) dengan setiap lubang kecil berisi tepat 7 biji dan kedua lumbung kosong:

$$b_i = \begin{cases} 7, & \text{jika } i \in \{0, \dots, 6\} \cup \{8, \dots, 14\} \\ 0, & \text{jika } i \in \{7, 15\} \end{cases}$$

Setiap keadaan valid dalam ruang keadaan wajib memenuhi **hukum kekekalan jumlah biji** (*seed conservation invariant*):

$$\sum_{i=0}^{15} b_i = 98$$

---

### 2. Ruang Aksi Legal (*Action Space* - $\mathcal{A}$)
Himpunan indeks lubang milik pemain $p$ didefinisikan sebagai:

$$\text{Pits}(p) = \begin{cases} \{0, 1, 2, 3, 4, 5, 6\}, & \text{jika } p = 0 \\ \{8, 9, 10, 11, 12, 13, 14\}, & \text{jika } p = 1 \end{cases}$$

Lumbung milik pemain $p$ adalah $\text{Store}(0) = 7$ dan $\text{Store}(1) = 15$, sedangkan lumbung lawan adalah $\text{OppStore}(p) = \text{Store}(1 - p)$.

Fungsi aksi legal $\mathcal{A}(s)$ mengembalikan himpunan seluruh indeks lubang milik pemain aktif $p$ yang memiliki setidaknya satu biji:

$$\mathcal{A}(s) = \{ a \in \text{Pits}(p) \mid b_a > 0 \}$$

Karena setiap pemain memiliki 7 lubang kecil, faktor percabangan (*branching factor*) dari setiap simpul pencarian dibatasi oleh $0 \le |\mathcal{A}(s)| \le 7$.

---

### 3. Fungsi Transisi ($\mathcal{T}$) dan Dinamika Giliran Non-Alternatif
Fungsi transisi $\mathcal{T}: \mathcal{S} \times \mathcal{A} \to \mathcal{S}$ memetakan keadaan saat ini $s = (\mathbf{b}, p)$ dan aksi $a \in \mathcal{A}(s)$ menuju keadaan penerus $s' = (\mathbf{b}', p')$ melalui tahapan deterministik berikut. Seluruh tahapan a-c terjadi di dalam **satu** transisi $\mathcal{T}(s, a)$.

#### a. Penaburan Biji (*Sowing*)
Satu putaran tabur dari lubang $a$ mengambil seluruh $k = b_a$ biji (sehingga $b_a \leftarrow 0$), lalu mendistribusikannya satu per satu secara berlawanan arah jarum jam (indeks meningkat secara modular $\pmod{16}$), dengan melewati lumbung lawan $\text{OppStore}(p)$. Misalkan $i_{\text{last}}$ adalah indeks slot tempat biji ke-$k$ (biji terakhir) dijatuhkan, dan $c_{\text{before}}$ adalah isi slot tersebut tepat sebelum biji terakhir itu jatuh.

#### b. Menabur Lanjutan (*Relay Sowing*)
Apabila $i_{\text{last}} \neq \text{Store}(p)$ dan $c_{\text{before}} > 0$ (biji terakhir jatuh di lubang yang sebelumnya sudah berisi, di sisi mana pun), maka seluruh isi lubang $i_{\text{last}}$ (termasuk biji terakhir tersebut) diambil dan ditabur lagi mulai dari lubang berikutnya, sebagai putaran tabur baru dengan aturan penaburan yang sama. Proses ini diulang hingga salah satu kondisi berikut terjadi:

- biji terakhir sebuah putaran jatuh di $\text{Store}(p)$ (berhenti, giliran tambahan);
- biji terakhir jatuh di lubang yang sebelumnya kosong (berhenti, lanjut ke aturan tembak atau pindah giliran);
- jumlah putaran tabur dalam giliran tersebut mencapai batas pengaman $R_{\max} = 200$ (putaran pertama dihitung). Bila putaran ke-$R_{\max}$ berakhir di lubang yang sebelumnya berisi, giliran langsung berpindah ke lawan tanpa tembak.

Notasi $\mathbf{b}'$ pada tahap berikutnya menyatakan isi papan setelah putaran tabur terakhir selesai, dan $i_{\text{last}}$ adalah lubang terakhir dari putaran terakhir tersebut.

#### c. Aturan Tembak (*Capture*)
Apabila putaran terakhir berakhir di lubang kecil sisi sendiri yang sebelumnya kosong ($i_{\text{last}} \in \text{Pits}(p)$ dan $b'_{i_{\text{last}}} = 1$), serta lubang lawan yang tepat berhadapan di seberangnya $i_{\text{opp}} = 14 - i_{\text{last}}$ tidak kosong ($b'_{i_{\text{opp}}} > 0$), maka dilakukan penembakan:

$$b'_{\text{Store}(p)} \leftarrow b'_{\text{Store}(p)} + b'_{i_{\text{last}}} + b'_{i_{\text{opp}}}$$

$$b'_{i_{\text{last}}} \leftarrow 0, \quad b'_{i_{\text{opp}}} \leftarrow 0$$

Bila lubang seberang kosong, atau biji terakhir jatuh di lubang kosong sisi lawan, tidak terjadi penembakan dan giliran berpindah.

#### d. Transisi Giliran (*Turn Transition*)
Berbeda dengan permainan adversarial standar (seperti Catur atau Tic-Tac-Toe) yang selalu berganti giliran pada setiap kedalaman pohon (*strictly alternating*), Congklak memiliki mekanisme **Giliran Tambahan (*Extra-Turn*)**:

$$p' = \begin{cases} p, & \text{jika } i_{\text{last}} = \text{Store}(p) \quad \text{(Giliran Tambahan)} \\ 1 - p, & \text{jika } i_{\text{last}} \neq \text{Store}(p) \quad \text{(Pindah Giliran)} \end{cases}$$

Implikasi krusial terhadap algoritma pencarian pohon (*Minimax* dan *Alpha-Beta Pruning*) adalah sebuah simpul $\text{MAX}$ dapat bertransisi langsung menuju simpul $\text{MAX}$ lainnya ($\text{MAX} \to \text{MAX}$), demikian pula $\text{MIN} \to \text{MIN}$. Perpindahan semacam ini hanya terjadi melalui giliran tambahan, termasuk bila lumbung sendiri tercapai di ujung rantai menabur lanjutan. Sebaliknya, menabur lanjutan tidak menambah simpul perantara pada pohon: seluruh rangkaian putaran tabur berlangsung di dalam satu transisi $\mathcal{T}(s, a)$, sehingga ia hanya membuat biaya komputasi setiap transisi lebih besar dan hasil sebuah langkah lebih sulit diperkirakan tanpa menjalankannya.

---

### 4. Kondisi Terminal ($\text{TERMINAL}$) dan Fungsi Utilitas ($\mathcal{U}$)
Misalkan $p$ adalah pemain yang berhak jalan berikutnya setelah sebuah langkah (pemain lawan, atau pemain yang sama bila memperoleh giliran tambahan). Suatu keadaan $s = (\mathbf{b}, p)$ dinyatakan sebagai keadaan akhir ($\text{TERMINAL}(s) = \text{True}$) apabila pemain yang berhak jalan tidak memiliki lubang berisi:

$$\text{TERMINAL}(s) \iff \sum_{i \in \text{Pits}(p)} b_i = 0 \iff \mathcal{A}(s) = \emptyset$$

Dengan demikian, kosongnya sisi pemain yang tidak berhak jalan bukan kondisi akhir: permainan berlanjut selama pemain yang berhak jalan masih memiliki lubang berisi.

Saat kondisi terminal tercapai, dilakukan penyapuan bersih (*sweep*) seluruh sisa biji di lubang kecil ke lumbung pemiliknya masing-masing:

$$b_{\text{Store}(0)} \leftarrow b_{\text{Store}(0)} + \sum_{i=0}^{6} b_i, \quad b_{\text{Store}(1)} \leftarrow b_{\text{Store}(1)} + \sum_{j=8}^{14} b_j$$

**Pengaman terminasi.** Dua pengaman menjamin setiap permainan berakhir: (i) paling banyak $R_{\max} = 200$ putaran tabur dalam satu giliran, sebagaimana dijelaskan pada tahap b; dan (ii) permainan dipaksa berakhir bila jumlah langkah $m$ (setiap aksi yang dijalankan, termasuk aksi giliran tambahan) mencapai 300, kemudian sisa biji disapu seperti pada akhir normal. Penghitung langkah $m$ berada di luar tupel $s = (\mathbf{b}, p)$; implementasi menyimpannya terpisah sebagai `move_count` dan tidak mengikutkannya dalam kunci keadaan.

Fungsi utilitas $\mathcal{U}(s)$ pada keadaan terminal dari sudut pandang Pemain 0 didefinisikan sebagai selisih perolehan biji akhir di lumbung:

$$\mathcal{U}(s) = b_7 - b_{15}$$

Permainan dimenangkan oleh Pemain 0 jika $\mathcal{U}(s) > 0$, dimenangkan oleh Pemain 1 jika $\mathcal{U}(s) < 0$, dan berakhir seri (*draw*) jika $\mathcal{U}(s) = 0$ (yakni $b_7 = b_{15} = 49$).

---

### 5. Kompleksitas dan Ukuran Ruang Keadaan (*State-Space Complexity*)
Secara kombinatorika, distribusi $N = 98$ biji identik ke dalam $M = 16$ slot papan yang dapat dibedakan merupakan masalah *stars and bars* (kombinasi dengan pengulangan). Jumlah konfigurasi distribusi biji yang mungkin memenuhi persamaan $\sum_{i=0}^{15} b_i = 98$ dengan $b_i \ge 0$ adalah:

$$\binom{N + M - 1}{M - 1} = \binom{98 + 16 - 1}{16 - 1} = \binom{113}{15} \approx 1,81 \times 10^{18} \text{ konfigurasi papan}$$

(nilai eksak $\binom{113}{15} = 1.809.960.172.844.903.640$, dihitung dengan `math.comb`).

Dengan memperhitungkan 2 kemungkinan giliran pemain aktif ($p \in \{0, 1\}$), batas atas ukuran ruang keadaan (*state-space bound*) dari varian Congklak (7 lubang, 7 biji) adalah:

$$|\mathcal{S}| \le 2 \times \binom{113}{15} \approx 3,62 \times 10^{18} \text{ keadaan}$$

Angka ini hanyalah batas atas yang kasar: banyak konfigurasi di dalamnya tidak dapat dicapai dari $s_0$ melalui aturan permainan, sehingga ukuran ruang keadaan yang benar-benar terjangkau lebih kecil dan tidak dihitung di sini.

Sebagai pembanding, Kalah varian tertentu (misalnya 6 lubang dengan 4 biji per lubang) telah diselesaikan secara eksak oleh Irving, Donkers & Uiterwijk (2000) dalam *ICGA Journal* [sitasi perlu diverifikasi]. Pada Congklak $(7, 7)$, batas atas ruang keadaan berskala $\sim 10^{18}$, faktor percabangan $b \le 7$, dan satu langkah dapat menempuh banyak putaran tabur akibat menabur lanjutan. Karena itu pencarian eksak hingga akhir permainan tidak diasumsikan layak dalam batas waktu nyata per langkah. Hal inilah yang mendasari kebutuhan akan pemangkasan pohon pencarian (*Alpha-Beta Pruning* dengan *Transposition Table*) serta optimasi fungsi evaluasi heuristik berbasis algoritma evolusioner (*Genetic Algorithm*).
