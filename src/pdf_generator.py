#!/usr/bin/env python3
"""
PDF Generator untuk Arunika Command Centre.
Menggunakan fpdf2 (pure Python, tidak butuh library sistem).

Install: pip install fpdf2

Cara pakai dari kode:
  from pdf_generator import generate_pdf_from_text
  path = generate_pdf_from_text("Isi dokumen...", judul="Laporan", output_dir=Path("data/output"))
"""
import os
import re
from pathlib import Path
from datetime import datetime


# Peta karakter Unicode -> latin-1 (font PDF standar hanya dukung latin-1)
_UNICODE_MAP = {
    "—": "-", "–": "-", "―": "-", "−": "-",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "…": "...", "•": "-", "·": "-", "‣": "-", "◦": "-",
    "→": "->", "←": "<-", "⇒": "=>", "⇐": "<=", "↔": "<->",
    "×": "x", "÷": "/", "±": "+/-",
    "≥": ">=", "≤": "<=", "≠": "!=", "≈": "~",
    "°": " derajat", "®": "(R)", "©": "(C)", "™": "(TM)",
    " ": " ", "​": "", " ": " ", "﻿": "",
    "‪": "", "‬": "", "★": "*", "☆": "*", "✓": "v", "✔": "v",
    "✗": "x", "✘": "x", "►": ">", "▶": ">", "●": "-", "○": "-",
}


def _pdf_safe(text: str) -> str:
    """Ubah karakter Unicode jadi latin-1 yang didukung font PDF.
    Emoji & simbol tak dikenal dibuang agar tidak crash."""
    if not text:
        return text
    for uni, ascii_eq in _UNICODE_MAP.items():
        text = text.replace(uni, ascii_eq)
    # Buang sisa karakter di luar latin-1 (mis. emoji)
    return text.encode("latin-1", "ignore").decode("latin-1")


def _strip_markdown(text: str) -> list[tuple[str, str]]:
    """
    Parse markdown sederhana, kembalikan list (style, text):
    style: 'h1', 'h2', 'h3', 'bold', 'bullet', 'normal'
    """
    result = []
    for line in text.split("\n"):
        stripped = line.rstrip()
        if stripped.startswith("### "):
            result.append(("h3", stripped[4:]))
        elif stripped.startswith("## "):
            result.append(("h2", stripped[3:]))
        elif stripped.startswith("# "):
            result.append(("h1", stripped[2:]))
        elif stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4:
            result.append(("bold", stripped[2:-2]))
        elif re.match(r"^[-*•]\s+", stripped):
            result.append(("bullet", re.sub(r"^[-*•]\s+", "", stripped)))
        elif stripped == "":
            result.append(("empty", ""))
        else:
            # Hapus bold/italic inline
            cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            cleaned = re.sub(r"\*(.+?)\*", r"\1", cleaned)
            cleaned = re.sub(r"_(.+?)_", r"\1", cleaned)
            result.append(("normal", cleaned))
    return result


def _render_table(pdf, headers: list[str], rows: list[list[str]]):
    """Render tabel asli di PDF (kolom rapi). Fallback ke teks bila gagal."""
    headers = [_pdf_safe(re.sub(r"\*\*?", "", h)) for h in headers]
    rows = [[_pdf_safe(re.sub(r"\*\*?", "", c)) for c in r] for r in rows]
    ncol = max([len(headers)] + [len(r) for r in rows]) if (headers or rows) else 0
    if ncol == 0:
        return

    # Samakan jumlah kolom tiap baris
    headers = (headers + [""] * ncol)[:ncol]
    rows = [(r + [""] * ncol)[:ncol] for r in rows]

    try:
        pdf.ln(2)
        with pdf.table(
            first_row_as_headings=True,
            headings_style=__import__("fpdf").fonts.FontFace(
                emphasis="BOLD", color=(255, 255, 255), fill_color=(40, 100, 180)
            ),
            cell_fill_color=(238, 242, 250),
            cell_fill_mode="ROWS",
            line_height=6,
            text_align="LEFT",
            width=pdf.epw,
        ) as table:
            r = table.row()
            for h in headers:
                r.cell(h)
            for data_row in rows:
                r = table.row()
                for c in data_row:
                    r.cell(c)
        pdf.ln(2)
    except Exception:
        # Fallback: render sebagai teks label:value
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(20, 20, 20)
        for data_row in rows:
            label = data_row[0] if data_row else ""
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, label)
            pdf.set_font("Helvetica", "", 10)
            for i in range(1, len(data_row)):
                col = headers[i] if i < len(headers) else ""
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 6, f"   {col}: {data_row[i]}")
        pdf.ln(2)


def generate_pdf_from_text(
    content: str,
    judul: str = None,
    output_dir: Path = None,
    filename: str = None,
    company_name: str = "PT. Arunika Teknologi Global",
    doc_type: str = None,
) -> str:
    """
    Generate PDF dari teks/markdown dengan tabel asli & layout per jenis dokumen.

    Args:
        content: Isi dokumen (markdown: #, ##, **, -, tabel |...|)
        judul: Judul dokumen (auto-detect dari konten jika kosong)
        output_dir: Folder output (default: cwd/data/output)
        filename: Nama file output (auto-generate jika kosong)
        company_name: Nama perusahaan untuk kop
        doc_type: 'surat'|'proposal'|'presentasi'|'umum' (auto-deteksi jika None)

    Returns:
        Path absolut file PDF yang dibuat
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError(
            "fpdf2 belum terpasang. Jalankan: pip install fpdf2"
        )

    # Deteksi jenis dokumen untuk penyesuaian layout
    if doc_type is None:
        try:
            from doc_utils import detect_doc_type
            doc_type = detect_doc_type(content)
        except Exception:
            doc_type = "umum"

    # Setup output dir
    if output_dir is None:
        output_dir = Path.cwd() / "data" / "output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Auto-detect judul dari baris pertama
    if not judul:
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if lines:
            first = lines[0]
            if first.startswith("# "):
                judul = first[2:]
            elif first.startswith("## "):
                judul = first[3:]
            else:
                judul = first[:60] + ("..." if len(first) > 60 else "")
        else:
            judul = "Dokumen Arunika"

    # Sanitasi semua teks agar aman untuk font PDF latin-1
    content      = _pdf_safe(content)
    judul        = _pdf_safe(judul)
    company_name = _pdf_safe(company_name)

    # Nama file
    if not filename:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = re.sub(r"[^a-zA-Z0-9\-_]", "_", judul[:30]).strip("_")
        filename = f"{ts}_{safe}.pdf"

    output_path = output_dir / filename

    # Buat PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 80, 160)
    pdf.cell(0, 10, company_name, ln=True, align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Dibuat: {datetime.now().strftime('%d %B %Y, %H:%M')}", ln=True, align="C")
    pdf.ln(4)

    # Garis pemisah
    pdf.set_draw_color(30, 80, 160)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Judul dokumen
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(0, 8, judul, align="C")
    pdf.ln(6)

    # Konten — proses baris demi baris, deteksi blok tabel
    from doc_utils import parse_md_table
    raw_lines = content.split("\n")
    i = 0
    n = len(raw_lines)

    def write_line(style, text):
        text = _pdf_safe(text)
        pdf.set_x(pdf.l_margin)
        if style == "empty":
            pdf.ln(3)
        elif style == "h1":
            pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(30, 80, 160)
            pdf.ln(2); pdf.multi_cell(0, 7, text); pdf.ln(1)
        elif style == "h2":
            pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(40, 100, 180)
            pdf.ln(1); pdf.multi_cell(0, 7, text); pdf.ln(1)
        elif style == "h3":
            pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, text)
        elif style == "bold":
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, text)
        elif style == "bullet":
            pdf.set_font("Helvetica", "", 10); pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, f"   - {text}")
        elif style == "hr":
            pdf.ln(1); pdf.set_draw_color(200, 200, 200); pdf.set_line_width(0.2)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
        else:
            pdf.set_font("Helvetica", "", 10); pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, text)

    while i < n:
        line = raw_lines[i]
        stripped = line.strip()

        # Blok tabel: kumpulkan baris berurutan yang mengandung |
        if stripped.startswith("|") and stripped.count("|") >= 2:
            block = []
            while i < n and raw_lines[i].strip().startswith("|"):
                block.append(raw_lines[i]); i += 1
            headers, rows = parse_md_table(block)
            if headers or rows:
                _render_table(pdf, headers, rows)
            continue

        # Horizontal rule (--- *** ___)
        if re.match(r"^\s*([-*_])\1{2,}\s*$", stripped):
            write_line("hr", ""); i += 1; continue

        # Markdown biasa → pakai _strip_markdown utk 1 baris
        for style, text in _strip_markdown(line):
            write_line(style, text)
        i += 1

    # Footer dengan nomor halaman
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f"Arunika Command Centre | {company_name}", align="C")

    pdf.output(str(output_path))
    return str(output_path)


def generate_txt_from_text(
    content: str,
    judul: str = None,
    output_dir: Path = None,
    filename: str = None,
    company_name: str = "PT. Arunika Teknologi Global",
) -> str:
    """
    Generate file TXT terstruktur dari teks/markdown.
    Markdown disederhanakan jadi teks rapi dengan garis & indentasi.

    Returns: Path absolut file TXT.
    """
    if output_dir is None:
        output_dir = Path.cwd() / "data" / "output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Auto-detect judul
    if not judul:
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if lines:
            first = lines[0]
            judul = re.sub(r"^#+\s*", "", first)[:60]
        else:
            judul = "Dokumen Arunika"

    if not filename:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = re.sub(r"[^a-zA-Z0-9\-_]", "_", judul[:30]).strip("_")
        filename = f"{ts}_{safe}.txt"

    output_path = output_dir / filename

    # Konversi markdown -> teks rapi
    W = 70  # lebar garis
    out = []
    out.append("=" * W)
    out.append(company_name.center(W))
    out.append(f"Dibuat: {datetime.now().strftime('%d %B %Y, %H:%M')} WIB".center(W))
    out.append("=" * W)
    out.append("")
    out.append(judul.center(W))
    out.append("-" * W)
    out.append("")

    for style, text in _strip_markdown(content):
        if style == "empty":
            out.append("")
        elif style == "h1":
            out.append("")
            out.append("=== " + text + " ===")
            out.append("=" * min(len(text) + 8, W))
        elif style == "h2":
            out.append("")
            out.append(">> " + text)
            out.append("-" * min(len(text) + 3, W))
        elif style == "h3":
            out.append("")
            out.append("  " + text)
        elif style == "bold":
            out.append("** " + text + " **")
        elif style == "bullet":
            out.append("   - " + text)
        else:
            out.append(text)

    out.append("")
    out.append("=" * W)
    out.append(f"Arunika Command Centre | {company_name}".center(W))
    out.append("=" * W)

    output_path.write_text("\n".join(out), encoding="utf-8")
    return str(output_path)


# ============ CLI ============
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        content = " ".join(sys.argv[1:])
    else:
        print("Masukkan teks (Ctrl+D atau Ctrl+Z untuk selesai):")
        content = sys.stdin.read()

    if not content.strip():
        print("Konten kosong.")
        sys.exit(1)

    try:
        path = generate_pdf_from_text(content)
        print(f"PDF disimpan: {path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
