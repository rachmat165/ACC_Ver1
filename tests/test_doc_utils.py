"""
TDD: Test untuk doc_utils — deteksi jenis dokumen, parse tabel, base URL publik.
"""
import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from doc_utils import detect_doc_type, parse_md_table, get_public_base_url


# ── Deteksi jenis dokumen ────────────────────────────────────
def test_deteksi_surat():
    t = ("Kepada Yth,\nPimpinan BPRS HIK\nPerihal: Penawaran Kerjasama\n"
         "Dengan hormat,\nKami dari PT Arunika...")
    assert detect_doc_type(t) == "surat"

def test_deteksi_surat_penawaran():
    assert detect_doc_type("SURAT PENAWARAN\n\nKepada Yth Bapak") == "surat"

def test_deteksi_proposal():
    t = ("PROPOSAL KERJASAMA\n\n## Latar Belakang\n...\n## Tujuan\n"
         "## Anggaran Biaya\n## Penutup")
    assert detect_doc_type(t) == "proposal"

def test_deteksi_presentasi():
    t = ("# Slide 1: Pendahuluan\n## Agenda\n- Poin\n---\n# Slide 2\n")
    assert detect_doc_type(t) == "presentasi"

def test_deteksi_umum():
    assert detect_doc_type("Ini jawaban biasa tentang cuaca hari ini.") == "umum"


# ── Parse tabel markdown ─────────────────────────────────────
def test_parse_tabel_header_dan_baris():
    md = (
        "| Metrik | Nilai | Status |\n"
        "|--------|-------|--------|\n"
        "| ROA | 3.1% | Baik |\n"
        "| ROE | 22% | Bagus |"
    )
    headers, rows = parse_md_table(md.split("\n"))
    assert headers == ["Metrik", "Nilai", "Status"]
    assert rows[0] == ["ROA", "3.1%", "Baik"]
    assert rows[1] == ["ROE", "22%", "Bagus"]
    assert len(rows) == 2

def test_parse_tabel_buang_separator():
    md = ["| A | B |", "|---|---|", "| 1 | 2 |"]
    headers, rows = parse_md_table(md)
    assert headers == ["A", "B"]
    assert ["1", "2"] in rows
    # Baris separator tidak boleh jadi data
    assert not any("-" in c for r in rows for c in r if c)


# ── Base URL publik (untuk link download) ───────────────────
def test_base_url_dari_file(tmp_path=None):
    d = Path(tempfile.mkdtemp())
    (d / "data").mkdir()
    (d / "data" / "tunnel_url.txt").write_text("https://abc.trycloudflare.com", "utf-8")
    assert get_public_base_url(d) == "https://abc.trycloudflare.com"

def test_base_url_kosong_jika_tidak_ada():
    d = Path(tempfile.mkdtemp())
    (d / "data").mkdir()
    assert get_public_base_url(d) in (None, "")

def test_base_url_strip_trailing_slash():
    d = Path(tempfile.mkdtemp())
    (d / "data").mkdir()
    (d / "data" / "tunnel_url.txt").write_text("https://abc.trycloudflare.com/\n", "utf-8")
    assert get_public_base_url(d) == "https://abc.trycloudflare.com"


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
