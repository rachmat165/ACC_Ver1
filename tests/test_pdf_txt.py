"""
TDD: Test untuk pdf_generator (PDF & TXT) — sanitasi Unicode & struktur.
"""
import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from pdf_generator import _pdf_safe, generate_pdf_from_text, generate_txt_from_text

_OUT = Path(tempfile.gettempdir()) / "acc_tests"
_OUT.mkdir(exist_ok=True)

SAMPLE = (
    "# Riset BPRS — Project AsSalam.ai\n\n"
    "## Konteks\n"
    "**Value:** Compliance-first → cost-efficient\n\n"
    "- Poin satu ★\n- Poin dua ✓\n"
    "Emoji 🚀 dan harga Rp 1.000.000 ± 10%\n"
    "URL: https://www.ojk.go.id/data-statistik/laporan-tahunan"
)


# ── Sanitasi Unicode ─────────────────────────────────────────
def test_emdash_jadi_strip():
    assert "—" not in _pdf_safe("teks — lain")
    assert "-" in _pdf_safe("teks — lain")

def test_emoji_dibuang():
    assert _pdf_safe("halo 🚀 dunia") == "halo  dunia"

def test_smart_quotes():
    assert _pdf_safe("“halo”") == '"halo"'

def test_panah_dan_simbol():
    out = _pdf_safe("A → B ± C")
    assert "→" not in out and "±" not in out


# ── Generate PDF ─────────────────────────────────────────────
def test_pdf_terbuat_dan_ada_isi():
    p = generate_pdf_from_text(SAMPLE, output_dir=_OUT, filename="t.pdf")
    f = Path(p)
    assert f.exists()
    assert f.stat().st_size > 500  # PDF valid biasanya > 500 byte

def test_pdf_tidak_crash_unicode():
    # Tidak boleh raise meski penuh Unicode/emoji
    txt = "★ → ± — “ ” 🚀 📊 • ‣ ≥ ≤ " * 20
    p = generate_pdf_from_text(txt, output_dir=_OUT, filename="t2.pdf")
    assert Path(p).exists()


# ── Generate TXT ─────────────────────────────────────────────
def test_txt_terbuat_dan_terbaca():
    p = generate_txt_from_text(SAMPLE, output_dir=_OUT, filename="t.txt")
    content = Path(p).read_text(encoding="utf-8")
    assert "Riset BPRS" in content
    assert "Poin satu" in content
    # Header perusahaan ada
    assert "Arunika" in content

def test_txt_ada_struktur_garis():
    p = generate_txt_from_text(SAMPLE, output_dir=_OUT, filename="t3.txt")
    content = Path(p).read_text(encoding="utf-8")
    assert "=" in content  # ada garis pemisah


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
