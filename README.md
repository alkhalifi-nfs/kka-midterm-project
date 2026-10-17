# 🏆 Congklak-Master: Adversarial Search & Evolutionary AI

Proyek Ujian Tengah Semester (UTS) mata kuliah **Konsep Kecerdasan Artifisial (KKA)**. Proyek ini mengimplementasikan permainan tradisional Congklak berbasis Python, membandingkan tiga model AI (*Depth-Limited Minimax*, *Alpha-Beta Pruning + Transposition Table*, dan *Genetic Algorithm-Evolved Evaluation Function*), serta *automated tournament benchmark*.

---

## 👥 Tim & Pembagian Peran
- **Alvian** (PIC-01): Game Engine Architect & Repo Lead (Core Engine, Rules, Repo, CLI)
- **Ravy** (PIC-02): Model 1 Engineer & Problem Analyst (Minimax Non-Alternating, Bab 1 & 2.2)
- **Pisnur** (PIC-03): Model 2 Engineer & Method Lead (Alpha-Beta, Move Ordering, Zobrist TT, Bab 2.3 & 2.4)
- **Erzeth** (PIC-04): Model 3 Engineer & Training Lead (GA Self-Play, 6 Fitur Evaluasi, Bab 2.5 & 3.1-3.2)
- **Nafis** (PIC-05): Tournament & Evaluation Lead (Tournament Runner, Metrik Elo/EBF, Bab 3.3-3.5 & Bab 4)

---

## 📁 Struktur Repositori
- `src/` : Seluruh source code utama aplikasi (engine, agen AI, utilitas).
  - `src/engine/` : Logika papan congklak dan API state (`api.py`).
- `experiments/` : Skrip pelatihan GA, pengujian turnamen, dan verifikasi model.
- `results/` : Data log pertandingan, checkpoint model (.json/.npy), tabel CSV, dan grafik.
- `report/` : Berkas penyusunan naskah laporan akhir dan bahan presentasi PPT.

---

## 🌿 Aturan Branching & Git Workflow

Untuk menjaga kestabilan kode bersama, ikuti aturan Git berikut:

1. **Proteksi Branch `main`:**
   - Dilarang keras melakukan *direct push* ke branch `main`.
   - Branch `main` hanya berisi kode yang sudah diuji dan lolos review.

2. **Format Penamaan Branch:**
   Buat branch baru dari `main` dengan format:  
   `feat/<nama_anggota>-<nama_fitur>`
   - Contoh Alvian: `feat/alvian-core-engine`
   - Contoh Ravy: `feat/ravy-minimax`
   - Contoh Pisnur: `feat/pisnur-alphabeta`
   - Contoh Erzeth: `feat/erzeth-ga-training`
   - Contoh Nafis: `feat/nafis-tournament`

3. **Standar Pesan Commit:**
   Gunakan format `[tipe] pesan singkat`:
   - `[feat]` : Menambah fitur / implementasi baru
   - `[fix]`  : Memperbaiki bug logika
   - `[docs]` : Mengubah dokumentasi / laporan
   - `[test]` : Menambah unit test

4. **Pull Request (PR) & Code Review:**
   - Setelah tugas di branch selesai, buat Pull Request (PR) menuju `main`.
   - Wajib di-review minimal oleh 1 rekan tim sebelum di-merge.