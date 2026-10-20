<!-- Dihasilkan otomatis oleh experiments.report_tables dari results/rq3; jangan disunting tangan. -->

**Win rate baris melawan kolom (seri dihitung 0,5)**

| Baris \ Kolom | ga | alphabeta | minimax |
| --- | :---: | :---: | :---: |
| **ga** | - | 50,5% | 57,4% |
| **alphabeta** | 49,5% | - | 56,4% |
| **minimax** | 42,6% | 43,6% | - |

**Rincian pasangan agen (interval Wilson 95%)**

| Agen (baris) | Lawan (kolom) | Game | Menang / Seri / Kalah | Win rate | Wilson 95% |
| --- | --- | ---: | :---: | ---: | :---: |
| ga | alphabeta | 600 | 300 / 6 / 294 | 50,5% | [46,5%; 54,5%] |
| ga | minimax | 600 | 341 / 7 / 252 | 57,4% | [53,4%; 61,3%] |
| alphabeta | ga | 600 | 294 / 6 / 300 | 49,5% | [45,5%; 53,5%] |
| alphabeta | minimax | 600 | 336 / 5 / 259 | 56,4% | [52,4%; 60,3%] |
| minimax | ga | 600 | 252 / 7 / 341 | 42,6% | [38,7%; 46,6%] |
| minimax | alphabeta | 600 | 259 / 5 / 336 | 43,6% | [39,7%; 47,6%] |

**Rating Elo Bradley-Terry (rata-rata antar agen 1500; CI bootstrap 95%, 1000 resample per game)**

| Peringkat | Agen | Elo | CI bootstrap 95% | Game | Skor |
| ---: | --- | ---: | :---: | ---: | ---: |
| 1 | ga | 1518,5 | [1504,9; 1531,6] | 1200 | 54,0% |
| 2 | alphabeta | 1513,8 | [1500,4; 1526,4] | 1200 | 53,0% |
| 3 | minimax | 1467,8 | [1454,2; 1480,9] | 1200 | 43,1% |

**Parameter protokol turnamen**

| Parameter | Nilai |
| --- | --- |
| Agen | minimax, alphabeta, ga |
| Pasangan agen (round-robin tanpa self-play) | 3 |
| Pembukaan per seed | 100 |
| Seed | 42, 123, 2026 |
| Langkah acak pembukaan | 6 |
| Game per pasangan agen (pembukaan x 2 sisi x seed) | 600 |
| Total game yang direncanakan | 1800 |
| Pembukaan berbeda dari yang diminta | 299 dari 300 |
| Batas kedalaman yang diteruskan ke agen | 0 |
| Batas waktu per langkah (detik) | 0,10 |
| Batas langkah per game / putaran tabur per giliran | 300 / 200 |
| Jumlah pemanggilan (termasuk --resume) | 1 |
| Game dimainkan (jumlah semua pemanggilan) | 1800 |
| Kalah forfeit (jumlah semua pemanggilan) | 0 |
| Commit kode per pemanggilan | d6bbbb7dc8 |
| Lingkungan | Python 3.12.10, numpy 2.5.4 |

**Beban pencarian per langkah**

| Agen | Game | Keputusan | Node/langkah | Cutoff/langkah | Kedalaman rata-rata | Waktu/langkah (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ga | 1200 | 17471 | 2080,1 | 719,5 | 14,66 | 94,831 |
| alphabeta | 1200 | 17292 | 2043,4 | 706,3 | 14,88 | 93,534 |
| minimax | 1200 | 14570 | 3143,1 | 0,0 | 5,38 | 90,603 |
