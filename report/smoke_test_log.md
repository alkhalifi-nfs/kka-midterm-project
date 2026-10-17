# Laporan Smoke Test & Bug Fixing (Tugas T21)

**Tanggal Uji:** 18 Oktober 2026  
**PIC Integrasi:** Alvian  
**Cakupan:** Integrasi `Core Engine v1` dengan 4 Agen (`Random`, `Greedy`, `Minimax`, `Alpha-Beta`)

---

## 1. Ringkasan Hasil Smoke Test

Seluruh 6 skenario pengujian integrasi pada `tests/test_smoke.py` telah dijalankan menggunakan `pytest` dan lulus 100% (`6 passed`):

1. `test_smoke_01_random_vs_random` : **PASSED** (Total biji konsisten 98, terminasi normal).
2. `test_smoke_02_greedy_vs_random` : **PASSED** (Prioritas extra-turn dan capture berjalan baik).
3. `test_smoke_03_minimax_vs_greedy` : **PASSED** (Transisi non-alternating MAX->MAX berjalan akurat).
4. `test_smoke_04_alphabeta_vs_minimax` : **PASSED** (Pertandingan penuh selesai tanpa error).
5. `test_smoke_05_minimax_alphabeta_decision_equivalence` : **PASSED** (Keputusan langkah Model 1 == Model 2 pada berbagai state, dengan jumlah *nodes expanded* Alpha-Beta jauh lebih kecil).
6. `test_smoke_06_state_immutability_during_search` : **PASSED** (Pencarian rekursif tidak mengubah state asli).

---

## 2. Daftar Temuan Bug & Perbaikan (Bug Log & Fixes)

| ID Bug | Komponen | Deskripsi Masalah / Bug | Penyebab Utama (Root Cause) | Perbaikan (Fix) yang Diterapkan | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **BUG-01** | `tests/test_engine.py` | Kegagalan asersi `last_pit` pada uji lewati lumbung lawan (`test_07` & `test_08`). | Perhitungan jumlah biji uji (10 biji dari lubang 6 melewati lumbung 15 jatuh di indeks 1, bukan 0). | Menyesuaikan skenario uji menjadi 9 biji agar jatuh tepat di indeks pertama setelah melewati lumbung lawan. | **Fixed** |
| **BUG-02** | `Minimax` & `AlphaBeta` | Asumsi pergantian pemain otomatis (`!is_maximizing`) merusak evaluasi saat terjadi *Extra-Turn*. | Pada Congklak, jika biji terakhir mendarat di lumbung sendiri, pemain yang sama melangkah lagi (transisi `MAX -> MAX` atau `MIN -> MIN`). | Mengubah pengecekan status node di setiap rekursi menjadi dinamis berdasarkan state: `is_maximizing = (state.current_player == root_player)`. | **Fixed** |
| **BUG-03** | `Board.step()` & Kondisi Akhir | Potensi *deadlock* ketika pemain mendapat *Extra-Turn* dari biji terakhirnya, tetapi seluruh lubang di sisinya menjadi kosong. | Pemeriksaan terminal awal hanya mengecek apakah kedua sisi kosong sebelum mengecek ketersediaan langkah pemain berikutnya. | Menambahkan pengecekan `len(self.get_valid_moves(next_player)) == 0` di akhir `step()`, lalu otomatis menjalankan `sweep_remaining_seeds()`. | **Fixed** |
| **BUG-04** | Integrasi Paket (`pytest`) | `ModuleNotFoundError: No module named 'src'` saat skrip test dieksekusi langsung. | Direktori root belum terdaftar pada `sys.path` saat dijalankan via runner eksternal. | Menambahkan `__init__.py` di setiap modul dan konfigurasi `sys.path.insert` pada berkas pengujian. | **Fixed** |