"""
Infrastruktur eksperimen Congklak-Master: registry agen, runner turnamen,
analisis Elo/win rate, dan pengambilan sampel posisi.

KONTRAK AGEN (dipakai runner turnamen)
--------------------------------------
Agen adalah objek dengan:
  - ``name: str``
  - ``choose_move(state, time_limit=None, depth=None) -> int``: mengembalikan
    indeks lubang legal. ``time_limit`` dalam detik (None = tanpa batas) dan
    ``depth`` batas kedalaman; agen yang tidak memakainya boleh mengabaikannya.
    Runner meneruskan SALINAN state, jadi agen boleh memutasinya.
Opsional (dibaca lewat getattr, tanpa dependensi keras):
  - ``reset(seed)``: dipanggil sekali per game sebelum langkah pertama dengan
    seed yang reproducible, agar agen stokastik dapat diulang persis.
  - ``metrics``: objek (atau dict) yang menjelaskan pemanggilan ``choose_move``
    TERAKHIR (bukan akumulasi), dengan atribut ``nodes``, ``cutoffs``,
    ``depth_reached``, ``elapsed`` (detik). Nama alternatif yang juga dikenali:
    ``nodes_expanded``, ``max_depth_reached``, ``execution_time_sec``.
"""
