"""
wa_format - Konversi Markdown -> format WhatsApp yang rapi.

WhatsApp hanya kenal:
  *tebal*   _miring_   ~coret~   ```mono```
Tidak ada header (#), tidak ada tabel markdown (| |).

Fungsi utama: to_whatsapp(text) -> str
"""
import re

# Penanda sementara agar bold & italic tidak bentrok saat konversi
_B0, _B1 = "\x00", "\x01"   # placeholder untuk *tebal*


def _convert_table(rows: list[str]) -> str:
    """
    Ubah blok tabel markdown jadi list terbaca.

    | Metrik | Value | Status |
    |--------|-------|--------|
    | ROA | 3.1% | Baik |
      ->
    *ROA*
      Value: 3.1%
      Status: Baik
    """
    # Parse tiap baris jadi list sel
    def cells(line: str) -> list[str]:
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [c.strip() for c in line.split("|")]

    # Buang baris separator (|---|---|)
    def is_sep(line: str) -> bool:
        return bool(re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", line)) and "-" in line

    data_rows = [r for r in rows if not is_sep(r)]
    if not data_rows:
        return ""

    header = cells(data_rows[0])
    out_lines = []

    # Jika hanya header (tanpa data), tampilkan sebagai daftar tebal
    if len(data_rows) == 1:
        return " | ".join(header)

    for row in data_rows[1:]:
        c = cells(row)
        if not c or all(not x for x in c):
            continue
        label = c[0]
        out_lines.append(f"*{label}*")
        # Pasangkan kolom ke-2 dst dengan header-nya
        for i in range(1, len(c)):
            col_name = header[i] if i < len(header) else ""
            val = c[i]
            if col_name:
                out_lines.append(f"  {col_name}: {val}")
            else:
                out_lines.append(f"  {val}")
    return "\n".join(out_lines)


def _convert_inline(text: str) -> str:
    """Konversi bold/italic inline tanpa bentrok."""
    # 1. **tebal** -> placeholder (lindungi dulu)
    text = re.sub(r"\*\*(.+?)\*\*", rf"{_B0}\1{_B1}", text)
    # 2. __tebal__ -> placeholder juga
    text = re.sub(r"__(.+?)__", rf"{_B0}\1{_B1}", text)
    # 3. *miring* (markdown italic) -> _miring_ (WA italic)
    text = re.sub(r"(?<!\*)\*(?!\s)([^*\n]+?)(?<!\s)\*(?!\*)", r"_\1_", text)
    # 4. Kembalikan placeholder jadi *tebal* (WA bold)
    text = text.replace(_B0, "*").replace(_B1, "*")
    return text


def to_whatsapp(text: str) -> str:
    """Konversi teks markdown jadi format WhatsApp yang rapi."""
    if not text:
        return text

    lines = text.split("\n")
    out: list[str] = []
    table_buf: list[str] = []

    def flush_table():
        if table_buf:
            converted = _convert_table(table_buf)
            if converted:
                out.append(converted)
            table_buf.clear()

    for line in lines:
        stripped = line.strip()

        # ── Baris tabel (mengandung | dan bukan kosong) ────────
        if stripped.startswith("|") and stripped.count("|") >= 2:
            table_buf.append(line)
            continue
        else:
            flush_table()

        # ── Horizontal rule (--- *** ___) -> garis WA ─────────
        if re.match(r"^\s*([-*_])\1{2,}\s*$", stripped):
            out.append("──────────")
            continue

        # ── Header (# ## ###) -> *tebal* ──────────────────────
        m = re.match(r"^\s*#{1,6}\s+(.*)$", line)
        if m:
            header_text = m.group(1).strip()
            # Hapus bold ganda jika ada di dalam header
            header_text = re.sub(r"\*\*(.+?)\*\*", r"\1", header_text)
            out.append(f"*{header_text}*")
            continue

        # ── Bullet (- atau * di awal) -> • ────────────────────
        mb = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if mb:
            indent = mb.group(1)
            content = _convert_inline(mb.group(2))
            out.append(f"{indent}• {content}")
            continue

        # ── Baris biasa: konversi inline bold/italic ──────────
        out.append(_convert_inline(line))

    flush_table()

    result = "\n".join(out)
    # Rapikan: maksimal 2 newline berturut
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


if __name__ == "__main__":
    contoh = (
        "## 1. PT BPRS Amanah Ummah\n\n"
        "**Status:** Terdaftar & Sehat OJK\n"
        "**Aset:** Rp 1.4-1.6 Triliun\n\n"
        "### Kesehatan Finansial\n\n"
        "| Metrik | Value | Status |\n"
        "|--------|-------|--------|\n"
        "| ROA | 3.1% | Sangat Baik |\n"
        "| ROE | 22% | Excellent |\n\n"
        "---\n\n"
        "Ini *penting* dan **wajib** dibaca."
    )
    print(to_whatsapp(contoh))
