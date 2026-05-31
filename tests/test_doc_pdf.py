"""
TDD: Test PDF dokumen formal (surat, proposal, presentasi) + tabel asli.
Fokus: tidak crash, output valid, doc_type benar.
"""
import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from pdf_generator import generate_pdf_from_text

_OUT = Path(tempfile.gettempdir()) / "acc_docpdf"
_OUT.mkdir(exist_ok=True)


SURAT = """SURAT PENAWARAN KERJASAMA

Kepada Yth,
Pimpinan BPRS Harta Insan Karimah (HIK)
di Tempat

Perihal: Penawaran Kerjasama Project AsSalam.ai

Dengan hormat,

Kami dari PT Arunika Teknologi Global bermaksud menawarkan kerjasama
dalam pengembangan Agentic AI for Syariah Banking System.

Demikian surat penawaran ini kami sampaikan.

Hormat kami,
Adang A. Kunandar
Direktur
"""

PROPOSAL = """PROPOSAL KERJASAMA PROJECT ASSALAM.AI

## Latar Belakang
Perbankan syariah membutuhkan otomasi cerdas.

## Tujuan
- Meningkatkan efisiensi operasional
- Compliance otomatis

## Ruang Lingkup
| Modul | Fungsi | Estimasi |
|-------|--------|----------|
| IDP Agent | Proses dokumen | 2 bulan |
| Risk Agent | Analisis risiko | 3 bulan |

## Anggaran Biaya
Total investasi Rp 500 juta.

## Penutup
Demikian proposal ini kami ajukan.
"""

PRESENTASI = """# AsSalam.ai - Agentic AI for Syariah Banking

## Agenda
- Pendahuluan
- Solusi
- Demo

---

# Slide 2: Masalah
Perbankan syariah lambat dalam underwriting.

---

# Slide 3: Solusi
AI agent otomatis & compliance-first.
"""


def _valid_pdf(path: str, min_size: int = 800) -> bool:
    p = Path(path)
    if not p.exists() or p.stat().st_size < min_size:
        return False
    # PDF harus diawali %PDF
    return p.read_bytes()[:4] == b"%PDF"


# ── Surat ────────────────────────────────────────────────────
def test_surat_pdf_valid():
    p = generate_pdf_from_text(SURAT, output_dir=_OUT, filename="surat.pdf")
    assert _valid_pdf(p)

def test_surat_doc_type_terdeteksi():
    from doc_utils import detect_doc_type
    assert detect_doc_type(SURAT) == "surat"


# ── Proposal (dengan tabel) ──────────────────────────────────
def test_proposal_pdf_valid():
    p = generate_pdf_from_text(PROPOSAL, output_dir=_OUT, filename="proposal.pdf")
    assert _valid_pdf(p)

def test_proposal_dengan_tabel_tidak_crash():
    # Tabel markdown di dalam proposal harus dirender tanpa error
    p = generate_pdf_from_text(PROPOSAL, output_dir=_OUT, filename="proposal2.pdf")
    assert _valid_pdf(p, min_size=1000)


# ── Presentasi ───────────────────────────────────────────────
def test_presentasi_pdf_valid():
    p = generate_pdf_from_text(PRESENTASI, output_dir=_OUT, filename="presentasi.pdf")
    assert _valid_pdf(p)


# ── Robustness: dokumen besar dengan Unicode & tabel ─────────
def test_dokumen_besar_unicode_tabel():
    big = (PROPOSAL + "\n") * 5 + "\nEmoji 🚀 — simbol ± → ★\n"
    big += "| X | Y |\n|---|---|\n| ★ | → |\n"
    p = generate_pdf_from_text(big, output_dir=_OUT, filename="big.pdf")
    assert _valid_pdf(p, min_size=1000)

def test_tabel_panjang_banyak_kolom():
    md = "| A | B | C | D | E |\n|---|---|---|---|---|\n"
    md += "\n".join("| %d | %d | %d | %d | %d |" % (i,i,i,i,i) for i in range(20))
    p = generate_pdf_from_text("# Data\n\n" + md, output_dir=_OUT, filename="tbl.pdf")
    assert _valid_pdf(p)


if __name__ == "__main__":
    import traceback
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in funcs:
        try:
            fn(); passed += 1; print(f"  PASS  {fn.__name__}")
        except Exception as e:
            failed += 1; print(f"  FAIL  {fn.__name__}: {e}")
            traceback.print_exc()
    print(f"\n  {passed} lulus, {failed} gagal dari {len(funcs)} test")
    sys.exit(1 if failed else 0)
