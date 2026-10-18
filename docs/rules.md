# Aturan Varian Congklak (Congklak-Master)

## 1. Papan & Biji
- 2 Pemain (Pemain 0 dan Pemain 1).
- 14 lubang kecil (7 lubang per pemain, masing-masing berisi 7 biji di awal).
- 2 lumbung induk (Lumbung 0 untuk Pemain 0 di indeks 7, Lumbung 1 untuk Pemain 1 di indeks 15).
- Total biji di papan = 98 biji.

## 2. Arah & Putaran
- Putaran berjalan berlawanan arah jarum jam (indeks modular menaik 0 sampai 15).
- Saat menabur, lumbung milik lawan selalu dilewati (skip).

## 3. Aturan Khusus
- **Giliran Tambahan (Extra Turn):** Jika biji terakhir jatuh di lumbung sendiri, pemain yang sama mendapat giliran melangkah lagi.
- **Tembak (Capture):** Jika biji terakhir jatuh di lubang sisi sendiri yang tadinya kosong, dan lubang lawan di seberangnya ada isinya, maka biji terakhir dan seluruh biji lawan di seberang diambil lalu dimasukkan ke lumbung sendiri.
- **Mati di Sisi Lawan:** Jika biji terakhir jatuh di lubang kosong sisi lawan, giliran langsung berpindah ke lawan.

## 4. Akhir Permainan
- Game selesai saat salah satu pemain tidak punya langkah legal lagi di gilirannya.
- Sisa biji di lubang kecil dimasukkan ke lumbung pemiliknya masing-masing.
- Pemenang ditentukan dari jumlah biji terbanyak di lumbung.