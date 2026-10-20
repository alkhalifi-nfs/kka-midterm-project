<!-- dibuat oleh experiments/search_bench.py dari results/positions_seed42_n500.json; heuristik h2; commit 1c5e391 -->

**Kesamaan langkah dan nilai dengan Minimax (Bab 3.2)**

| Kedalaman | Posisi | Alpha-Beta polos | + move ordering | + TT (tanpa ordering) | + ordering + TT | Model 2 lengkap (+ ID) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 |
| 2 | 500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 |
| 3 | 500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 |
| 4 | 500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 |
| 5 | 500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 |
| 6 | 500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 | langkah 500/500, nilai 500/500 |

Konfigurasi bertanda TT boleh berbeda dari Minimax karena entri TT dari pencarian yang lebih dalam dipakai ulang (lihat src/agents/alphabeta.py).

**Rata-rata node per posisi (persentase terhadap Minimax pada kedalaman yang sama)**

| Kedalaman | Minimax | Alpha-Beta polos | + move ordering | + TT (tanpa ordering) | + ordering + TT | Model 2 lengkap (+ ID) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 (100,0%) | 5 (100,0%) | 5 (100,0%) | 5 (100,0%) | 5 (100,0%) | 5 (100,0%) |
| 2 | 25 (100,0%) | 18 (73,7%) | 16 (62,5%) | 18 (73,7%) | 16 (62,5%) | 22 (89,4%) |
| 3 | 118 (100,0%) | 59 (49,7%) | 38 (32,2%) | 59 (49,7%) | 38 (32,2%) | 62 (52,8%) |
| 4 | 570 (100,0%) | 177 (31,1%) | 88 (15,4%) | 176 (30,9%) | 87 (15,3%) | 150 (26,3%) |
| 5 | 2795 (100,0%) | 525 (18,8%) | 195 (7,0%) | 519 (18,6%) | 192 (6,9%) | 330 (11,8%) |
| 6 | 13809 (100,0%) | 1513 (11,0%) | 424 (3,1%) | 1489 (10,8%) | 416 (3,0%) | 690 (5,0%) |

**Effective branching factor (EBF)**

| Kedalaman | Minimax | Alpha-Beta polos | + move ordering | + TT (tanpa ordering) | + ordering + TT | Model 2 lengkap (+ ID) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 4,29 | 4,29 | 4,29 | 4,29 | 4,29 | 4,29 |
| 2 | 4,41 | 3,69 | 3,34 | 3,69 | 3,34 | 4,13 |
| 3 | 4,51 | 3,48 | 2,94 | 3,48 | 2,94 | 3,56 |
| 4 | 4,60 | 3,34 | 2,74 | 3,34 | 2,73 | 3,19 |
| 5 | 4,66 | 3,25 | 2,61 | 3,24 | 2,60 | 2,94 |
| 6 | 4,71 | 3,18 | 2,52 | 3,17 | 2,51 | 2,76 |

**Transposition table: rata-rata TT hit dan isi TT per pencarian (maksimum)**

| Kedalaman | + TT (tanpa ordering) | + ordering + TT | Model 2 lengkap (+ ID) |
| --- | --- | --- | --- |
| 1 | 0,0 hit, 1 entri (1) | 0,0 hit, 1 entri (1) | 0,0 hit, 1 entri (1) |
| 2 | 0,0 hit, 5 entri (8) | 0,0 hit, 5 entri (8) | 0,0 hit, 5 entri (8) |
| 3 | 0,0 hit, 19 entri (53) | 0,0 hit, 15 entri (53) | 0,0 hit, 15 entri (53) |
| 4 | 0,3 hit, 60 entri (211) | 0,2 hit, 38 entri (210) | 0,2 hit, 38 entri (210) |
| 5 | 1,3 hit, 183 entri (710) | 0,7 hit, 87 entri (636) | 0,7 hit, 85 entri (633) |
| 6 | 4,4 hit, 541 entri (2354) | 1,8 hit, 191 entri (1728) | 2,1 hit, 177 entri (1763) |

**Rata-rata waktu per pencarian (milidetik; 1 worker, Windows-11-10.0.26200-SP0)**

| Kedalaman | Minimax | Alpha-Beta polos | + move ordering | + TT (tanpa ordering) | + ordering + TT | Model 2 lengkap (+ ID) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0,07 | 0,08 | 0,09 | 0,08 | 0,08 | 0,08 |
| 2 | 0,33 | 0,32 | 0,30 | 0,31 | 0,30 | 0,39 |
| 3 | 1,56 | 1,10 | 0,83 | 1,09 | 0,83 | 1,27 |
| 4 | 7,50 | 3,43 | 1,98 | 3,40 | 2,04 | 3,21 |
| 5 | 37,31 | 10,17 | 4,48 | 10,15 | 4,48 | 7,52 |
| 6 | 188,69 | 29,91 | 9,98 | 29,96 | 9,85 | 16,39 |
