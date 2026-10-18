# Aturan Varian Congklak (Congklak-Master)

Dokumen ini adalah keputusan final tim. Engine (`src/engine/`) dan tes (`tests/`) mengikuti teks ini.

## 1. Papan & Biji
- 2 Pemain (Pemain 0 dan Pemain 1). Pemain 0 jalan pertama; turnamen menukar sisi.
- Papan 16 slot: indeks 0-6 lubang kecil Pemain 0, indeks 7 lumbung Pemain 0, indeks 8-14 lubang kecil Pemain 1, indeks 15 lumbung Pemain 1.
- Awal: 7 biji per lubang kecil (14 lubang), kedua lumbung kosong. Total biji di papan = 98 biji.
- Lubang seberang dari lubang `i` adalah `14 - i` (0↔14, 1↔13, ..., 6↔8).

## 2. Arah & Penaburan
- Giliran bergantian.
- Satu langkah: pilih lubang tidak kosong di sisi sendiri, ambil semua biji di dalamnya, lalu tabur satu per satu ke indeks yang naik (modulo 16), dimulai dari lubang berikutnya.
- Saat menabur, lumbung milik lawan selalu dilompati (skip).
- Lubang asal tidak dilompati: bila penaburan melingkar penuh, lubang asal (yang sudah dikosongkan) ikut menerima biji dan dianggap kosong sebelum biji itu jatuh.

## 3. Biji Terakhir Satu Putaran Tabur
Biji terakhir sebuah putaran tabur jatuh di salah satu dari empat kemungkinan berikut:

- **a) Lumbung sendiri (Giliran Tambahan / Extra Turn):** pemain yang sama jalan lagi.
- **b) Lubang yang sebelum biji itu jatuh sudah berisi, di sisi mana pun (Menabur Lanjutan / Relay):** ambil semua isi lubang itu (termasuk biji terakhir) dan tabur lagi mulai dari lubang berikutnya. Ulangi selama aturan ini berlaku.
- **c) Lubang di sisi sendiri yang sebelumnya kosong (Tembak / Capture):** bila lubang seberangnya berisi, biji terakhir dan seluruh isi lubang seberang masuk ke lumbung sendiri. Bila seberang kosong, tidak terjadi apa-apa. Giliran pindah ke lawan.
- **d) Lubang di sisi lawan yang sebelumnya kosong (Mati di Sisi Lawan):** berhenti, giliran pindah ke lawan.

## 4. Pengaman
- Maksimal 200 putaran tabur per giliran (putaran pertama dihitung). Bila putaran ke-200 berakhir di lubang berisi, giliran langsung pindah ke lawan tanpa tembak.
- Game dipaksa selesai bila `move_count` (jumlah langkah, termasuk langkah giliran tambahan) mencapai 300. Sisa biji disapu seperti akhir normal.

## 5. Akhir Permainan
- Setelah sebuah langkah, jika pemain yang berhak jalan berikutnya (bisa pemain yang sama pada giliran tambahan) tidak punya lubang berisi, game selesai.
- Sisa biji di lubang kecil disapu ke lumbung pemilik sisinya masing-masing.
- Pemenang = pemain dengan lumbung terbanyak. Skor 49-49 berarti seri.
- Tidak ada aturan "salah satu sisi kosong": game tidak berhenti hanya karena satu sisi habis, selama pemain yang berhak jalan berikutnya masih punya lubang berisi.
