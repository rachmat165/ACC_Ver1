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


def generate_pdf_from_text(
    content: str,
    judul: str = None,
    output_dir: Path = None,
    filename: str = None,
    company_name: str = "PT. Arunika Teknologi Global",
) -> str:
    """
    Generate PDF dari teks/markdown.

    Args:
        content: Isi dokumen (mendukung markdown sederhana)
        judul: Judul dokumen (auto-detect dari konten jika kosong)
        output_dir: Folder output (default: cwd/data/output)
        filename: Nama file output (auto-generate jika kosong)
        company_name: Nama perusahaan untuk header

    Returns:
        Path absolut file PDF yang dibuat
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError(
            "fpdf2 belum terpasang. Jalankan: pip install fpdf2"
        )

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

    # Konten
    parsed = _strip_markdown(content)
    for style, text in parsed:
        if style == "empty":
            pdf.ln(3)
        elif style == "h1":
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 80, 160)
            pdf.ln(2)
            pdf.multi_cell(0, 7, text)
            pdf.ln(1)
        elif style == "h2":
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(40, 100, 180)
            pdf.ln(1)
            pdf.multi_cell(0, 7, text)
            pdf.ln(1)
        elif style == "h3":
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, text)
        elif style == "bold":
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, text)
        elif style == "bullet":
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(6)  # indent
            pdf.multi_cell(0, 6, f"• {text}")
        else:  # normal
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, text)

    # Footer
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
    out.append(judul.upper().center(W))
    out.append("-" * W)
    out.append("")

    for style, text in _strip_markdown(content):
        if style == "empty":
            out.append("")
        elif style == "h1":
            out.append("")
            out.append("#" * 3 + " " + text.upper())
            out.append("=" * min(len(text) + 4, W))
        elif style == "h2":
            out.append("")
            out.append(">> " + text.upper())
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
