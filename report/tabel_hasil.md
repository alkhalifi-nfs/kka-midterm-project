<!-- Dihasilkan otomatis oleh experiments.report_tables dari results; jangan disunting tangan. -->

**Win rate baris melawan kolom (seri dihitung 0,5)**

| Baris \ Kolom | ga | alphabeta | minimax | alphabeta_h1 | minimax_h1 | greedy | random |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ga** | - | 51,2% | 51,2% | 52,8% | 52,8% | 94,6% | 97,8% |
| **alphabeta** | 48,8% | - | 50,0% | 50,5% | 50,5% | 93,8% | 97,3% |
| **minimax** | 48,8% | 50,0% | - | 50,5% | 50,5% | 93,8% | 97,3% |
| **alphabeta_h1** | 47,2% | 49,5% | 49,5% | - | 50,0% | 94,1% | 97,8% |
| **minimax_h1** | 47,2% | 49,5% | 49,5% | 50,0% | - | 94,1% | 97,8% |
| **greedy** | 5,4% | 6,2% | 6,2% | 5,9% | 5,9% | - | 80,5% |
| **random** | 2,2% | 2,7% | 2,7% | 2,2% | 2,2% | 19,5% | - |

**Rincian pasangan agen (interval Wilson 95%)**

| Agen (baris) | Lawan (kolom) | Game | Menang / Seri / Kalah | Win rate | Wilson 95% |
| --- | --- | ---: | :---: | ---: | :---: |
| ga | alphabeta | 600 | 300 / 14 / 286 | 51,2% | [47,2%; 55,1%] |
| ga | minimax | 600 | 300 / 14 / 286 | 51,2% | [47,2%; 55,1%] |
| ga | alphabeta_h1 | 600 | 312 / 10 / 278 | 52,8% | [48,8%; 56,8%] |
| ga | minimax_h1 | 600 | 312 / 10 / 278 | 52,8% | [48,8%; 56,8%] |
| ga | greedy | 600 | 565 / 5 / 30 | 94,6% | [92,5%; 96,1%] |
| ga | random | 600 | 585 / 3 / 12 | 97,8% | [96,2%; 98,7%] |
| alphabeta | ga | 600 | 286 / 14 / 300 | 48,8% | [44,9%; 52,8%] |
| alphabeta | minimax | 600 | 294 / 12 / 294 | 50,0% | [46,0%; 54,0%] |
| alphabeta | alphabeta_h1 | 600 | 299 / 8 / 293 | 50,5% | [46,5%; 54,5%] |
| alphabeta | minimax_h1 | 600 | 299 / 8 / 293 | 50,5% | [46,5%; 54,5%] |
| alphabeta | greedy | 600 | 562 / 2 / 36 | 93,8% | [91,6%; 95,5%] |
| alphabeta | random | 600 | 583 / 2 / 15 | 97,3% | [95,7%; 98,4%] |
| minimax | ga | 600 | 286 / 14 / 300 | 48,8% | [44,9%; 52,8%] |
| minimax | alphabeta | 600 | 294 / 12 / 294 | 50,0% | [46,0%; 54,0%] |
| minimax | alphabeta_h1 | 600 | 299 / 8 / 293 | 50,5% | [46,5%; 54,5%] |
| minimax | minimax_h1 | 600 | 299 / 8 / 293 | 50,5% | [46,5%; 54,5%] |
| minimax | greedy | 600 | 562 / 2 / 36 | 93,8% | [91,6%; 95,5%] |
| minimax | random | 600 | 583 / 2 / 15 | 97,3% | [95,7%; 98,4%] |
| alphabeta_h1 | ga | 600 | 278 / 10 / 312 | 47,2% | [43,2%; 51,2%] |
| alphabeta_h1 | alphabeta | 600 | 293 / 8 / 299 | 49,5% | [45,5%; 53,5%] |
| alphabeta_h1 | minimax | 600 | 293 / 8 / 299 | 49,5% | [45,5%; 53,5%] |
| alphabeta_h1 | minimax_h1 | 600 | 290 / 20 / 290 | 50,0% | [46,0%; 54,0%] |
| alphabeta_h1 | greedy | 600 | 562 / 5 / 33 | 94,1% | [91,9%; 95,7%] |
| alphabeta_h1 | random | 600 | 586 / 1 / 13 | 97,8% | [96,2%; 98,7%] |
| minimax_h1 | ga | 600 | 278 / 10 / 312 | 47,2% | [43,2%; 51,2%] |
| minimax_h1 | alphabeta | 600 | 293 / 8 / 299 | 49,5% | [45,5%; 53,5%] |
| minimax_h1 | minimax | 600 | 293 / 8 / 299 | 49,5% | [45,5%; 53,5%] |
| minimax_h1 | alphabeta_h1 | 600 | 290 / 20 / 290 | 50,0% | [46,0%; 54,0%] |
| minimax_h1 | greedy | 600 | 562 / 5 / 33 | 94,1% | [91,9%; 95,7%] |
| minimax_h1 | random | 600 | 586 / 1 / 13 | 97,8% | [96,2%; 98,7%] |
| greedy | ga | 600 | 30 / 5 / 565 | 5,4% | [3,9%; 7,5%] |
| greedy | alphabeta | 600 | 36 / 2 / 562 | 6,2% | [4,5%; 8,4%] |
| greedy | minimax | 600 | 36 / 2 / 562 | 6,2% | [4,5%; 8,4%] |
| greedy | alphabeta_h1 | 600 | 33 / 5 / 562 | 5,9% | [4,3%; 8,1%] |
| greedy | minimax_h1 | 600 | 33 / 5 / 562 | 5,9% | [4,3%; 8,1%] |
| greedy | random | 600 | 473 / 20 / 107 | 80,5% | [77,1%; 83,5%] |
| random | ga | 600 | 12 / 3 / 585 | 2,2% | [1,3%; 3,8%] |
| random | alphabeta | 600 | 15 / 2 / 583 | 2,7% | [1,6%; 4,3%] |
| random | minimax | 600 | 15 / 2 / 583 | 2,7% | [1,6%; 4,3%] |
| random | alphabeta_h1 | 600 | 13 / 1 / 586 | 2,2% | [1,3%; 3,8%] |
| random | minimax_h1 | 600 | 13 / 1 / 586 | 2,2% | [1,3%; 3,8%] |
| random | greedy | 600 | 107 / 20 / 473 | 19,5% | [16,5%; 22,9%] |

**Rating Elo Bradley-Terry (rata-rata antar agen 1500; CI bootstrap 95%, 1000 resample per game)**

| Peringkat | Agen | Elo | CI bootstrap 95% | Game | Skor |
| ---: | --- | ---: | :---: | ---: | ---: |
| 1 | ga | 1675,6 | [1662,1; 1688,5] | 3600 | 66,7% |
| 2 | alphabeta | 1663,4 | [1651,5; 1676,9] | 3600 | 65,2% |
| 3 | minimax | 1663,4 | [1651,5; 1676,9] | 3600 | 65,2% |
| 4 | alphabeta_h1 | 1659,5 | [1646,8; 1672,2] | 3600 | 64,7% |
| 5 | minimax_h1 | 1659,5 | [1646,1; 1671,4] | 3600 | 64,7% |
| 6 | greedy | 1199,0 | [1181,6; 1216,3] | 3600 | 18,3% |
| 7 | random | 979,6 | [953,7; 1006,1] | 3600 | 5,3% |

**Parameter protokol turnamen**

| Parameter | Nilai |
| --- | --- |
| Agen | random, greedy, minimax, minimax_h1, alphabeta, alphabeta_h1, ga |
| Pasangan agen (round-robin tanpa self-play) | 21 |
| Pembukaan per seed | 100 |
| Seed | 42, 123, 2026 |
| Langkah acak pembukaan | 6 |
| Game per pasangan agen (pembukaan x 2 sisi x seed) | 600 |
| Total game yang direncanakan | 12600 |
| Pembukaan berbeda dari yang diminta | 299 dari 300 |
| Batas kedalaman yang diteruskan ke agen | 4 |
| Batas waktu per langkah (detik) | tanpa batas |
| Batas langkah per game / putaran tabur per giliran | 300 / 200 |
| Jumlah pemanggilan (termasuk --resume) | 1 |
| Game dimainkan (jumlah semua pemanggilan) | 12600 |
| Kalah forfeit (jumlah semua pemanggilan) | 0 |
| Commit kode per pemanggilan | 307fb3beef |
| Lingkungan | Python 3.12.10, numpy 2.5.4 |

**Beban pencarian per langkah**

| Agen | Game | Keputusan | Node/langkah | Cutoff/langkah | Kedalaman rata-rata | Waktu/langkah (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ga | 3600 | 54408 | 129,6 | 28,7 | 3,93 | 8,705 |
| alphabeta | 3600 | 54681 | 124,7 | 27,9 | 3,91 | 8,332 |
| minimax | 3600 | 54681 | 568,7 | 0,0 | 4,00 | 24,382 |
| alphabeta_h1 | 3600 | 52960 | 124,4 | 27,9 | 3,91 | 7,264 |
| minimax_h1 | 3600 | 52960 | 566,1 | 0,0 | 4,00 | 17,766 |
| greedy | 3600 | 24190 | 3,6 | 0,0 | 1,00 | 0,093 |
| random | 3600 | 29259 | - | - | - | 0,011 |
