# kka-midterm-project

# 🏆 Congklak-Master: Adversarial Search & Evolutionary AI

Repositori ini memuat implementasi *engine* permainan tradisional Congklak berbasis Python dengan optimasi **Numba**, perbandingan tiga model kecerdasan buatan (*Modified Depth-Limited Minimax*, *Alpha-Beta Pruning dengan Move Ordering & Zobrist Transposition Table*, dan *Genetic Algorithm-Evolved Evaluation Function*), serta *automated tournament benchmark harness*.

Proyek ini disusun untuk memenuhi tugas besar Ujian Tengah Semester (UTS) mata kuliah **Kecerdasan Komputasional dan Aplikasinya (KKA)**.

---

## 👥 Tim Pengembang & Pembagian Peran

| Anggota | Kode PIC | Peran Utama | Fokus Implementasi |
| :--- | :---: | :--- | :--- |
| **Alvian** | PIC-01 | *Game Engine Architect & Repo Lead* | Core Engine (Numba), aturan varian, repositori, dan CLI |
| **Ravy** | PIC-02 | *Model 1 Engineer & Problem Analyst* | Depth-Limited Minimax (Multi-turn handling) & Laporan Bab 1 |
| **Pisnur** | PIC-03 | *Model 2 Engineer & Method Lead* | Alpha-Beta Pruning, Move Ordering, Zobrist Hashing TT |
| **Erzeth** | PIC-04 | *Model 3 Engineer & Training Lead* | 6 Fitur Papan, Genetic Algorithm Self-Play Weight Tuning |
| **Nafis** | PIC-05 | *Tournament & Metrics Lead* | Automated Tournament Runner, Metrik Elo/EBF, Bab 3-4 |

---

## 📁 Struktur Repositori

- `src/engine/` : Logika aturan permainan Congklak (16 slot: 14 lubang + 2 lumbung, estafet, tembak, extra-turn).
- `src/agents/` : Implementasi agen bot (Minimax, AlphaBeta+TT, GA-Agent).
- `experiments/` : Skrip pelatihan GA, verifikasi ekuivalensi, dan turnamen round-robin.
- `results/` : Log performa, tabel CSV hasil turnamen, dan grafik komparasi.
- `report/` : Dokumen laporan akhir PDF dan slide presentasi.

---

## ⚙️ Instalasi & Persiapan Lingkungan

1. **Clone Repositori:**
   ```bash
   git clone [https://github.com/](https://github.com/)<username>/congklak-master.git
   cd congklak-master
   ```

2. **Buat Virtual Environment:**
   ```bash
   python -m venv venv
   # Linux / macOS:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   ```

3. **Install Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Panduan Berkontribusi (Branching Workflow)

1. Jangan melakukan *commit/push* langsung ke `main`.
2. Buat branch baru dari `main` sesuai fitur yang dikerjakan:
   ```bash
   git checkout -b feat/<nama>-<nama-tugas>
   ```
3. Lakukan pengujian unit sebelum push:
   ```bash
   pytest tests/
   ```
4. Buka Pull Request (PR) ke `main` dan minta review ke reviewer yang ditugaskan.
