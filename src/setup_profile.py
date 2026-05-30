#!/usr/bin/env python3
"""
Setup Profil Lembaga untuk ACC.
Sekali isi, semua dokumen (surat, proposal, dll) otomatis memakai data ini.
"""
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML belum terpasang. Jalankan: pip install pyyaml")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))
PROFILE_FILE = ACC_HOME / "data" / "profile.yaml"


def ask(label, default="", required=False):
    """Tanya input dengan default. Jika RICH ada, pakai Prompt rich."""
    if RICH:
        while True:
            val = Prompt.ask(f"  {label}", default=default if default else None) or ""
            if required and not val.strip():
                console.print("    [red]Wajib diisi.[/red]")
                continue
            return val.strip()
    else:
        prompt = f"  {label}"
        if default:
            prompt += f" [{default}]"
        prompt += " > "
        while True:
            val = input(prompt).strip() or default
            if required and not val:
                print("    Wajib diisi.")
                continue
            return val


def section(title):
    if RICH:
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
        console.print("[dim]" + "─" * 50 + "[/dim]")
    else:
        print(f"\n{title}")
        print("─" * 50)


def load_existing():
    if PROFILE_FILE.exists():
        try:
            return yaml.safe_load(PROFILE_FILE.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
    return {}


def main():
    if RICH:
        console.print(Panel.fit(
            "[bold cyan]SETUP PROFIL LEMBAGA[/bold cyan]\n"
            "[dim]Sekali isi, semua dokumen otomatis pakai data ini[/dim]",
            border_style="cyan", padding=(1, 2)))
    else:
        print("=" * 50)
        print("  SETUP PROFIL LEMBAGA")
        print("=" * 50)

    existing = load_existing()
    if existing.get("nama"):
        if RICH:
            t = Table(show_header=False, border_style="dim")
            t.add_column("k", style="dim"); t.add_column("v")
            for k, v in existing.items():
                if isinstance(v, dict):
                    v = ", ".join(f"{kk}: {vv}" for kk, vv in v.items() if vv)
                t.add_row(str(k), str(v) if v else "[dim](kosong)[/dim]")
            console.print(Panel(t, title="Profil saat ini", border_style="yellow"))
            if not Confirm.ask("Ubah profil?", default=False):
                console.print("[green]Tidak ada perubahan.[/green]")
                return
        else:
            print("\nProfil saat ini:")
            for k, v in existing.items():
                print(f"  {k}: {v}")
            if input("\nUbah profil? (y/n) > ").strip().lower() != "y":
                return

    profile = dict(existing)
    e = lambda k, d="": profile.get(k, d) if isinstance(profile.get(k), str) else d

    # ── Identitas ──
    section("1. Identitas Lembaga")
    profile["tipe"] = ask("Tipe (PT/CV/Yayasan/Lembaga/UMKM/Pribadi)", e("tipe", "PT"), required=True)
    profile["nama"] = ask("Nama lengkap", e("nama"), required=True)
    profile["nama_singkat"] = ask("Nama singkat/akronim", e("nama_singkat"))
    profile["tagline"] = ask("Tagline (opsional)", e("tagline"))
    profile["bidang"] = ask("Bidang usaha/kegiatan", e("bidang"))

    # ── Pimpinan ──
    section("2. Pimpinan")
    profile["pimpinan_nama"] = ask("Nama pimpinan", e("pimpinan_nama"))
    profile["pimpinan_jabatan"] = ask("Jabatan", e("pimpinan_jabatan", "Direktur Utama"))

    # ── Alamat ──
    section("3. Alamat")
    al = profile.get("alamat", {}) if isinstance(profile.get("alamat"), dict) else {}
    alamat = {}
    alamat["jalan"] = ask("Alamat jalan", al.get("jalan", ""))
    alamat["kota"] = ask("Kota", al.get("kota", ""))
    alamat["provinsi"] = ask("Provinsi", al.get("provinsi", ""))
    alamat["kode_pos"] = ask("Kode pos", al.get("kode_pos", ""))
    alamat["negara"] = ask("Negara", al.get("negara", "Indonesia"))
    profile["alamat"] = alamat

    # ── Kontak ──
    section("4. Kontak")
    ko = profile.get("kontak", {}) if isinstance(profile.get("kontak"), dict) else {}
    kontak = {}
    kontak["email"] = ask("Email", ko.get("email", ""))
    kontak["telepon"] = ask("Telepon kantor", ko.get("telepon", ""))
    kontak["whatsapp"] = ask("WhatsApp", ko.get("whatsapp", ""))
    kontak["website"] = ask("Website", ko.get("website", ""))
    profile["kontak"] = kontak

    # ── Legal ──
    section("5. Legalitas (opsional)")
    le = profile.get("legal", {}) if isinstance(profile.get("legal"), dict) else {}
    legal = {}
    legal["npwp"] = ask("NPWP", le.get("npwp", ""))
    legal["nib"] = ask("NIB/SIUP", le.get("nib", ""))
    legal["akta_pendirian"] = ask("Akta pendirian", le.get("akta_pendirian", ""))
    profile["legal"] = legal

    # ── Visi/Misi ──
    section("6. Visi & Misi (opsional)")
    profile["visi"] = ask("Visi (1 kalimat)", e("visi"))
    profile["misi"] = ask("Misi (1 kalimat)", e("misi"))

    # ── Branding ──
    section("7. Branding (opsional)")
    br = profile.get("branding", {}) if isinstance(profile.get("branding"), dict) else {}
    branding = {}
    branding["logo_path"] = ask("Path file logo (opsional)", br.get("logo_path", ""))
    branding["warna_primer"] = ask("Warna primer (hex)", br.get("warna_primer", "#4F46E5"))
    branding["warna_aksen"] = ask("Warna aksen (hex)", br.get("warna_aksen", "#F59E0B"))
    profile["branding"] = branding

    # ── Simpan ──
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(
        "# Profil Lembaga ACC - dipakai otomatis di semua dokumen\n"
        + yaml.safe_dump(profile, allow_unicode=True, sort_keys=False),
        encoding="utf-8"
    )

    if RICH:
        console.print(Panel(
            f"[green]Profil tersimpan di:[/green]\n{PROFILE_FILE}\n\n"
            f"[dim]Setiap surat/proposal/laporan akan otomatis pakai data ini.[/dim]",
            title="[bold green]✓ Berhasil[/bold green]", border_style="green"))
    else:
        print(f"\n✓ Profil tersimpan di: {PROFILE_FILE}")


def build_profile_context():
    """Bangun string konteks profil untuk diinjeksikan ke system prompt."""
    if not PROFILE_FILE.exists():
        return ""
    try:
        p = yaml.safe_load(PROFILE_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return ""
    if not p.get("nama"):
        return ""
    al = p.get("alamat", {}) or {}
    ko = p.get("kontak", {}) or {}
    le = p.get("legal", {}) or {}
    lines = [
        "# PROFIL PENGIRIM (gunakan otomatis di setiap surat/proposal/laporan)",
        f"Nama       : {p.get('tipe', '')} {p.get('nama', '')}".strip(),
    ]
    if p.get("tagline"): lines.append(f"Tagline    : {p['tagline']}")
    if p.get("bidang"):  lines.append(f"Bidang     : {p['bidang']}")
    if p.get("pimpinan_nama"):
        lines.append(f"Pimpinan   : {p['pimpinan_nama']} ({p.get('pimpinan_jabatan', '')})")
    addr = ", ".join(filter(None, [al.get("jalan"), al.get("kota"), al.get("provinsi"), al.get("kode_pos"), al.get("negara")]))
    if addr: lines.append(f"Alamat     : {addr}")
    if ko.get("email"):    lines.append(f"Email      : {ko['email']}")
    if ko.get("telepon"):  lines.append(f"Telepon    : {ko['telepon']}")
    if ko.get("whatsapp"): lines.append(f"WhatsApp   : {ko['whatsapp']}")
    if ko.get("website"):  lines.append(f"Website    : {ko['website']}")
    if le.get("npwp"):     lines.append(f"NPWP       : {le['npwp']}")
    if p.get("visi"):      lines.append(f"Visi       : {p['visi']}")
    if p.get("misi"):      lines.append(f"Misi       : {p['misi']}")
    lines.append("")
    lines.append("INSTRUKSI: Gunakan profil di atas sebagai identitas pengirim di "
                 "kop surat, tanda tangan, footer, dan bagian identitas dokumen "
                 "TANPA menanyakan ulang ke operator.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
