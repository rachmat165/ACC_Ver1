"""
doc_utils - Utilitas dokumen untuk ACC.
- detect_doc_type: klasifikasi surat / proposal / presentasi / umum
- parse_md_table: ekstrak header & baris dari tabel markdown
- get_public_base_url: URL publik (tunnel) untuk link download
"""
import os
import re
from pathlib import Path


# ── Deteksi jenis dokumen ────────────────────────────────────
_SURAT_KW = [
    "kepada yth", "perihal:", "dengan hormat", "hormat kami",
    "surat penawaran", "no. surat", "nomor surat", "lampiran:",
]
_PROPOSAL_KW = [
    "proposal", "latar belakang", "ruang lingkup", "anggaran",
    "rencana anggaran", "tujuan kegiatan", "metodologi", "rab",
]
_PRESENTASI_KW = [
    "slide", "agenda", "## agenda", "presentasi", "deck",
]


def detect_doc_type(text: str) -> str:
    """Kembalikan: 'surat' | 'proposal' | 'presentasi' | 'umum'."""
    if not text:
        return "umum"
    low = text.lower()

    surat_score     = sum(1 for k in _SURAT_KW if k in low)
    proposal_score  = sum(1 for k in _PROPOSAL_KW if k in low)
    # Presentasi: banyak pemisah slide '---' atau kata 'slide'
    hr_count        = len(re.findall(r"^\s*---\s*$", text, re.MULTILINE))
    slide_kw        = sum(1 for k in _PRESENTASI_KW if k in low)
    presentasi_score = slide_kw + (1 if hr_count >= 2 else 0)

    # Surat paling spesifik → prioritas bila ada penanda kuat
    if surat_score >= 2:
        return "surat"
    if proposal_score >= 2:
        return "proposal"
    if presentasi_score >= 2:
        return "presentasi"
    # Skor tunggal: ambil tertinggi
    best = max(
        ("surat", surat_score),
        ("proposal", proposal_score),
        ("presentasi", presentasi_score),
        key=lambda x: x[1],
    )
    return best[0] if best[1] >= 2 else "umum"


# ── Parse tabel markdown ─────────────────────────────────────
def _is_separator(line: str) -> bool:
    """Baris pemisah tabel: |---|---| atau |:--|--:|."""
    return bool(re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", line)) and "-" in line


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_md_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """
    Parse baris-baris tabel markdown.
    Return (headers, rows). Baris separator |---| dibuang.
    """
    data = [l for l in lines if l.strip().startswith("|") and l.count("|") >= 2]
    data = [l for l in data if not _is_separator(l)]
    if not data:
        return ([], [])
    headers = _cells(data[0])
    rows = [_cells(l) for l in data[1:]]
    # Buang baris kosong total
    rows = [r for r in rows if any(c for c in r)]
    return (headers, rows)


# ── Base URL publik untuk link download ──────────────────────
def get_public_base_url(acc_home: Path) -> str | None:
    """
    Ambil URL publik (tunnel) untuk link download file.
    Prioritas:
      1. ENV WA_WEBHOOK_URL
      2. data/tunnel_url.txt (ditulis tunnel.py saat aktif)
    """
    env_url = os.environ.get("WA_WEBHOOK_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    f = Path(acc_home) / "data" / "tunnel_url.txt"
    if f.exists():
        url = f.read_text(encoding="utf-8").strip()
        if url:
            return url.rstrip("/")
    return None


def save_public_base_url(acc_home: Path, url: str):
    """Simpan URL publik tunnel agar webhook bisa membuat link download."""
    f = Path(acc_home) / "data" / "tunnel_url.txt"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(url.strip().rstrip("/"), encoding="utf-8")
