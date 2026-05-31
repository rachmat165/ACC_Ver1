"""
TDD: Test untuk wa_format.to_whatsapp()
Konversi markdown -> format WhatsApp yang rapi.

WhatsApp formatting:
  *tebal*  (satu bintang)   _miring_   ~coret~   ```mono```
  Tidak ada header ##, tidak ada tabel markdown.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from wa_format import to_whatsapp


# ── Header markdown -> tebal WhatsApp ────────────────────────
def test_h1_jadi_tebal():
    assert to_whatsapp("# Judul Besar") == "*Judul Besar*"

def test_h2_jadi_tebal():
    assert to_whatsapp("## Sub Judul") == "*Sub Judul*"

def test_h3_jadi_tebal():
    assert to_whatsapp("### Bagian") == "*Bagian*"


# ── Bold markdown ** -> * (WhatsApp) ─────────────────────────
def test_bold_dobel_jadi_tunggal():
    assert to_whatsapp("**Status:** aktif") == "*Status:* aktif"

def test_bold_dengan_kurung():
    assert to_whatsapp("**CAR (Capital Adequacy Ratio):** 18%") \
        == "*CAR (Capital Adequacy Ratio):* 18%"

def test_dua_bold_dalam_satu_baris():
    assert to_whatsapp("**A** dan **B**") == "*A* dan *B*"


# ── Italic markdown * -> _ (WhatsApp) ────────────────────────
def test_italic_tunggal_jadi_underscore():
    # *miring* (markdown italic) -> _miring_ (WA italic)
    assert to_whatsapp("ini *penting* sekali") == "ini _penting_ sekali"

def test_bold_dan_italic_tidak_bentrok():
    # **tebal** dan *miring* dalam satu teks
    assert to_whatsapp("**tebal** lalu *miring*") == "*tebal* lalu _miring_"


# ── Bullet list ──────────────────────────────────────────────
def test_bullet_dash_jadi_titik():
    assert to_whatsapp("- item satu") == "• item satu"

def test_bullet_bintang_jadi_titik():
    assert to_whatsapp("* item dua") == "• item dua"

def test_bullet_indent_dipertahankan():
    out = to_whatsapp("  - sub item")
    assert "•" in out and "sub item" in out


# ── Numbered list dipertahankan ──────────────────────────────
def test_numbered_list_tetap():
    assert to_whatsapp("1. langkah pertama") == "1. langkah pertama"


# ── Horizontal rule --- -> garis WA ──────────────────────────
def test_hr_jadi_garis():
    out = to_whatsapp("---")
    assert "---" not in out  # tidak boleh tersisa markdown hr mentah
    assert out.strip() != ""  # diganti sesuatu (garis)


# ── Tabel markdown -> list terbaca ───────────────────────────
def test_tabel_dikonversi_tidak_ada_pipe_separator():
    md = (
        "| Kriteria | Amanah | Mitra |\n"
        "|----------|--------|-------|\n"
        "| Aset | 1.4T | 1.0T |\n"
        "| NPL | 1.5% | 1.0% |"
    )
    out = to_whatsapp(md)
    # Baris separator |---| tidak boleh muncul
    assert "---" not in out
    assert "|--" not in out
    # Data harus tetap ada
    assert "Aset" in out
    assert "1.4T" in out
    assert "Amanah" in out

def test_tabel_baris_data_punya_label():
    md = (
        "| Metrik | Nilai |\n"
        "|--------|-------|\n"
        "| ROA | 3.1% |"
    )
    out = to_whatsapp(md)
    # Label kolom & nilai harus terhubung jelas
    assert "ROA" in out
    assert "3.1%" in out


# ── Kombinasi & integritas konten ────────────────────────────
def test_emoji_dipertahankan():
    assert "🚀" in to_whatsapp("Peluncuran 🚀 sukses")

def test_teks_biasa_utuh():
    teks = "Halo, ini jawaban biasa tanpa format."
    assert to_whatsapp(teks) == teks

def test_tidak_ada_header_hash_tersisa():
    md = "## Judul\n\nIsi paragraf.\n\n### Sub\n\n- poin"
    out = to_whatsapp(md)
    assert "#" not in out

def test_tidak_ada_bold_dobel_tersisa():
    md = "**a** **b** **c**"
    out = to_whatsapp(md)
    assert "**" not in out


# ── Dokumen kompleks (mirip output asli BPRS) ────────────────
def test_dokumen_bprs_lengkap():
    md = (
        "## 1. PT BPRS Amanah Ummah\n\n"
        "**Status:** Terdaftar & Sehat OJK\n"
        "**Aset:** Rp 1.4-1.6 Triliun\n\n"
        "### Kesehatan Finansial\n\n"
        "| Metrik | Value | Status |\n"
        "|--------|-------|--------|\n"
        "| ROA | 3.1% | Sangat Baik |\n"
        "| ROE | 22% | Excellent |\n\n"
        "### Kontak\n"
        "- *Divisi:* Inovasi Digital\n"
        "- *Email:* cto@example.co.id"
    )
    out = to_whatsapp(md)
    assert "#" not in out
    assert "**" not in out
    assert "|--" not in out
    assert "ROA" in out and "3.1%" in out
    assert "Amanah Ummah" in out


if __name__ == "__main__":
    # Jalankan manual tanpa pytest
    import traceback
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in funcs:
        try:
            fn(); passed += 1
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception:
            failed += 1
            print(f"  ERROR {fn.__name__}")
            traceback.print_exc()
    print(f"\n  {passed} lulus, {failed} gagal dari {len(funcs)} test")
    sys.exit(1 if failed else 0)
