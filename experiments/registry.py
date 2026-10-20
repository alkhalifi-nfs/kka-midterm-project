"""
Registry agen: pemetaan nama -> pabrik agen dengan lazy import.

Modul agen diimpor hanya saat dibutuhkan, jadi agen yang tidak bisa dibuat
(misalnya `ga` sebelum results/ga_weights.json ada) cukup dilewati dengan
peringatan, bukan error.

Spesifikasi agen (string) yang diterima ``--agents`` pada turnamen:
  - ``random``                      nama terdaftar di AGENT_SPECS
  - ``alias=paket.modul:Kelas``     memasang kelas apa pun tanpa menyunting registry;
                                    ``alias`` menjadi nama agen di CSV
  - ``paket.modul:Kelas``           sama, nama agen = seluruh string itu
Pabrik dipanggil tanpa argumen dan harus menghasilkan objek yang memenuhi
kontrak agen (lihat experiments/__init__.py). Nama tidak terdaftar tanpa titik
dua dianggap salah ketik dan menghasilkan ValueError.

Spesifikasi dipecahkan ulang di dalam proses worker, sehingga berfungsi pada
metode start multiprocessing apa pun (fork, forkserver, spawn).
"""

import importlib
import sys
from typing import Callable, Dict, List, Optional, Tuple

# Nama -> daftar kandidat "modul:Kelas" menurut prioritas; kandidat pertama yang
# bisa diimpor dipakai. Agen lain bisa dipasang tanpa menyunting daftar ini lewat
# spesifikasi "alias=modul:Kelas".
AGENT_SPECS: Dict[str, List[str]] = {
    "random": ["src.agents.baseline:RandomAgent"],
    "greedy": ["src.agents.baseline:GreedyAgent"],
    "minimax": ["src.agents.minimax:MinimaxAgent"],          # Model 1 dengan H2
    "minimax_h1": ["src.agents.minimax:MinimaxH1Agent"],     # Model 1 dengan H1
    "alphabeta": ["src.agents.alphabeta:AlphaBetaAgent"],    # Model 2 dengan H2
    "alphabeta_h1": ["src.agents.alphabeta:AlphaBetaH1Agent"],  # Model 2 dengan H1
    "ga": ["src.agents.ga:GAAgent"],
}


def warn(message: str) -> None:
    sys.stderr.write(f"[PERINGATAN] {message}\n")
    sys.stderr.flush()


def parse_agent_spec(spec: str) -> Tuple[str, List[str]]:
    """
    Mengurai spesifikasi menjadi (nama_agen, daftar_kandidat "modul:Kelas").
    Melempar ValueError bila nama tidak terdaftar dan bukan spesifikasi modul:Kelas.
    """
    spec = spec.strip()
    if "=" in spec:
        alias, target = (part.strip() for part in spec.split("=", 1))
        if not alias or ":" not in target:
            raise ValueError(f"Spesifikasi agen tidak valid: {spec!r} (format alias=modul:Kelas)")
        return alias, [target]
    if ":" in spec:
        return spec, [spec]
    if spec in AGENT_SPECS:
        return spec, list(AGENT_SPECS[spec])
    raise ValueError(
        f"Agen tidak dikenal: {spec!r}. Terdaftar: {', '.join(AGENT_SPECS)}. "
        f"Atau pakai format alias=modul:Kelas."
    )


def agent_name(spec: str) -> str:
    """Nama agen (identitas di CSV) dari sebuah spesifikasi."""
    return parse_agent_spec(spec)[0]


def _load_candidate(candidate: str) -> Callable:
    module_name, _, attr = candidate.partition(":")
    module = importlib.import_module(module_name)
    try:
        return getattr(module, attr)
    except AttributeError:
        raise ImportError(f"modul {module_name!r} ada, tetapi tidak punya {attr!r}") from None


def resolve_factory(spec: str, quiet: bool = False) -> Optional[Callable]:
    """
    Pabrik agen untuk `spec`, atau None (disertai peringatan kecuali quiet=True)
    bila tidak ada kandidat yang bisa diimpor.
    """
    name, candidates = parse_agent_spec(spec)
    problems = []
    for candidate in candidates:
        try:
            return _load_candidate(candidate)
        except ImportError as exc:
            problems.append(f"{candidate}: {exc}")
    if not quiet:
        warn(f"agen {name!r} dilewati, belum tersedia ({'; '.join(problems)})")
    return None


def make_agent(spec: str):
    """Membuat satu instance agen baru. Melempar ImportError bila belum tersedia."""
    factory = resolve_factory(spec, quiet=True)
    if factory is None:
        name, candidates = parse_agent_spec(spec)
        raise ImportError(f"agen {name!r} belum tersedia (kandidat: {', '.join(candidates)})")
    return factory()


def usable_specs(specs: List[str]) -> List[str]:
    """
    Menyaring `specs`: yang belum tersedia atau gagal dibuat dilewati dengan
    peringatan. Nama yang tidak dikenal (ValueError) tetap dilempar.
    """
    usable = []
    for spec in specs:
        factory = resolve_factory(spec)  # ValueError untuk nama tak dikenal; peringatan bila belum ada
        if factory is None:
            continue
        try:
            factory()
        except Exception as exc:  # noqa: BLE001 - agen apa pun boleh gagal dibuat
            warn(f"agen {agent_name(spec)!r} dilewati, gagal dibuat: {type(exc).__name__}: {exc}")
            continue
        usable.append(spec)
    return usable


def default_specs() -> List[str]:
    """Semua nama terdaftar yang saat ini benar-benar tersedia."""
    return usable_specs(list(AGENT_SPECS))
