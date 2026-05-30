#!/usr/bin/env python3
"""
Modul Research untuk ACC.
Pakai web_search tool resmi Anthropic untuk mencari informasi terkini.
Hasil ditampilkan, di-approve operator, lalu disimpan untuk dipakai
skill lain (proposal, surat, presentasi, dll.).
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))
RESEARCH_DIR = ACC_HOME / "data" / "research"

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


def banner(topic):
    if RICH:
        console.print(Panel.fit(
            f"[bold cyan]RESEARCH MODE[/bold cyan]\n"
            f"[dim]Web Search via Anthropic[/dim]\n\n"
            f"[yellow]Topik:[/yellow] {topic}",
            border_style="cyan", padding=(1, 2)))
    else:
        print("=" * 60)
        print(f"  RESEARCH - {topic}")
        print("=" * 60)


def status(msg, icon="-"):
    if RICH:
        console.print(f"  [cyan]{icon}[/cyan]  {msg}")
    else:
        print(f"  {icon}  {msg}")


def do_research(topic, max_searches=5, model=None):
    """Jalankan research via Anthropic web_search tool."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "ANTHROPIC_API_KEY belum diisi di data/.env"

    try:
        import anthropic
    except ImportError:
        return None, "Paket anthropic belum terpasang."

    client = anthropic.Anthropic(api_key=api_key)
    model = model or os.environ.get("ACC_PRIMARY_MODEL", "claude-sonnet-4-5")

    system_prompt = (
        "Kamu peneliti profesional. Lakukan riset mendalam tentang topik "
        "yang diberikan operator dengan menggunakan web_search.\n\n"
        "ATURAN:\n"
        "- Lakukan 2-5 pencarian web yang berbeda dari sudut pandang berbeda.\n"
        "- Verifikasi fakta penting dari beberapa sumber.\n"
        "- Bahasa Indonesia, gaya laporan profesional.\n"
        "- Sertakan sumber URL untuk setiap fakta.\n\n"
        "FORMAT JAWABAN AKHIR (dalam Markdown):\n"
        "# Ringkasan Eksekutif\n"
        "(3-5 baris paling penting)\n\n"
        "# Temuan Utama\n"
        "- Poin 1 dengan rujukan [n]\n"
        "- Poin 2 dengan rujukan [n]\n\n"
        "# Analisis & Implikasi\n"
        "(paragraf analisis)\n\n"
        "# Rekomendasi (jika relevan)\n"
        "(daftar saran konkret)\n\n"
        "# Sumber\n"
        "[1] judul - url\n"
        "[2] judul - url"
    )

    kwargs = {
        "model": model,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": f"Lakukan riset komprehensif tentang: {topic}"}],
        "tools": [{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": max_searches,
        }],
    }
    if "opus-4" not in model:
        kwargs["temperature"] = 0.3

    try:
        resp = client.messages.create(**kwargs)
    except Exception as e:
        return None, f"Error API: {e}"

    # Ekstrak text + sumber
    text_parts = []
    sources = []
    searches_done = []
    for block in resp.content:
        t = getattr(block, "type", "")
        if t == "text":
            text_parts.append(block.text)
        elif t == "server_tool_use":
            inp = getattr(block, "input", {}) or {}
            if inp.get("query"):
                searches_done.append(inp["query"])
        elif t == "web_search_tool_result":
            content = getattr(block, "content", []) or []
            for item in content:
                url = getattr(item, "url", None)
                title = getattr(item, "title", None)
                if url:
                    sources.append({"url": url, "title": title or url})

    full_text = "\n".join(text_parts).strip()
    return {
        "topic": topic,
        "model": model,
        "report": full_text,
        "sources": sources,
        "searches": searches_done,
        "timestamp": datetime.now().isoformat(),
    }, None


def show_report(result):
    if RICH:
        console.print()
        console.print(Panel(Markdown(result["report"]),
                            title=f"[bold]Hasil Research[/bold]",
                            border_style="green", padding=(1, 2)))
        if result["searches"]:
            t = Table(title="Pencarian yang dilakukan", show_header=False, border_style="dim")
            for i, q in enumerate(result["searches"], 1):
                t.add_row(f"[dim]{i}.[/dim]", q)
            console.print(t)
    else:
        print("\n" + "=" * 60)
        print("HASIL RESEARCH")
        print("=" * 60)
        print(result["report"])
        if result["searches"]:
            print("\nPencarian yang dilakukan:")
            for i, q in enumerate(result["searches"], 1):
                print(f"  {i}. {q}")


def save_research(result, approved=False):
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() else "-" for c in result["topic"].lower())[:50].strip("-")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"{stamp}_{slug}"
    # Markdown
    md_path = RESEARCH_DIR / f"{base}.md"
    md_content = (
        f"# Research: {result['topic']}\n\n"
        f"- Waktu: {result['timestamp']}\n"
        f"- Model: {result['model']}\n"
        f"- Status: {'✓ APPROVED' if approved else '○ DRAFT'}\n\n"
        f"---\n\n"
        f"{result['report']}\n"
    )
    md_path.write_text(md_content, encoding="utf-8")
    # JSON (untuk dipakai skill lain)
    json_path = RESEARCH_DIR / f"{base}.json"
    json_path.write_text(json.dumps({**result, "approved": approved},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path


def use_in_skill(result, skill_name):
    """Bangun pesan yang siap dipakai sebagai input ke skill lain."""
    sources_text = "\n".join(f"- {s['title']}: {s['url']}" for s in result.get("sources", []))
    return (
        f"Berikut hasil research yang sudah disetujui operator. "
        f"Gunakan sebagai dasar fakta untuk menyusun {skill_name}.\n\n"
        f"## TOPIK\n{result['topic']}\n\n"
        f"## HASIL RESEARCH\n{result['report']}\n\n"
        f"## SUMBER\n{sources_text}\n"
    )


def interactive():
    """Mode interaktif: tanya topik, jalankan, tampilkan, tanya approve."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ACC_HOME / "data" / ".env")
    except Exception:
        pass

    if RICH:
        topic = Prompt.ask("\n[bold]Topik research[/bold]")
    else:
        topic = input("\nTopik research > ").strip()
    if not topic:
        print("Topik kosong.")
        return

    banner(topic)
    status("Menjalankan web search via Anthropic...", "🔎")

    if RICH:
        with console.status("[cyan]Mencari & menyusun laporan...[/cyan]", spinner="dots"):
            result, err = do_research(topic)
    else:
        result, err = do_research(topic)

    if err:
        if RICH:
            console.print(Panel(err, title="[red]Error[/red]", border_style="red"))
        else:
            print(f"\n[ERROR] {err}")
        return

    show_report(result)

    if RICH:
        approved = Confirm.ask("\n[bold]Setujui hasil research ini?[/bold]", default=True)
    else:
        approved = input("\nSetujui hasil research? (y/n) [y] > ").strip().lower() != "n"

    md_path, json_path = save_research(result, approved=approved)
    status(f"Tersimpan: {md_path.name}", "✓")

    if not approved:
        status("Status: DRAFT (tidak digunakan otomatis).", "○")
        return

    # Tanya: mau langsung pakai untuk skill apa?
    if RICH:
        console.print("\n[bold]Pakai hasil ini untuk membuat:[/bold]")
        console.print("  [1] Proposal kerja sama")
        console.print("  [2] Surat penawaran")
        console.print("  [3] Presentasi visual")
        console.print("  [4] Laporan kerja")
        console.print("  [0] Tidak, simpan saja")
        choice = Prompt.ask("Pilih", choices=["0", "1", "2", "3", "4"], default="0")
    else:
        print("\nPakai hasil ini untuk:")
        print("  [1] Proposal  [2] Surat penawaran  [3] Presentasi  [4] Laporan  [0] Skip")
        choice = input("Pilih > ").strip()

    skill_map = {"1": "proposal", "2": "surat-penawaran",
                 "3": "presentasi-visual", "4": "laporan-kerja"}
    if choice not in skill_map:
        return

    skill = skill_map[choice]
    status(f"Menyusun {skill} berdasarkan research...", "→")

    # Panggil acc.call_model langsung dengan skill terpilih
    try:
        from acc import build_system_prompt, load_config, call_model, save_session
        cfg = load_config()
        sys_prompt = build_system_prompt(skill)
        user_msg = use_in_skill(result, skill)
        if RICH:
            with console.status(f"[cyan]Arunika menyusun {skill}...[/cyan]", spinner="dots"):
                reply = call_model(sys_prompt, user_msg, cfg)
        else:
            reply = call_model(sys_prompt, user_msg, cfg)
        save_session("user", f"[research->{skill}] {topic}")
        save_session("assistant", reply)
        if RICH:
            console.print(Panel(Markdown(reply), title=f"[bold]Hasil {skill}[/bold]",
                                border_style="green", padding=(1, 2)))
        else:
            print("\n" + "=" * 60)
            print(reply)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    interactive()
