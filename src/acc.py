#!/usr/bin/env python3
"""
Arunika Command Centre (ACC) - Agent Core
PT. Arunika Teknologi Global

Kerangka starter yang bisa langsung dijalankan:
  python src/acc.py menu   -> menu interaktif
  python src/acc.py chat   -> mode chat ke model
  python src/acc.py cron    -> jalankan tugas terjadwal yang jatuh tempo
  python src/acc.py doctor  -> cek konfigurasi & koneksi

Modul WhatsApp, generator dokumen, dan integrasi MCP penuh masih perlu
dilengkapi sesuai roadmap (lihat README.md).
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# ---------- Lokasi ----------
ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))
AGENT_DIR = ACC_HOME / "agent"
DATA_DIR = ACC_HOME / "data"
SKILLS_DIR = AGENT_DIR / "skills"

# ---------- Dependensi opsional ----------
try:
    import yaml
except ImportError:
    yaml = None
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def load_env():
    env_path = DATA_DIR / ".env"
    if load_dotenv and env_path.exists():
        load_dotenv(env_path)
    elif env_path.exists():
        # fallback manual parser
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def load_config():
    cfg_path = DATA_DIR / "config.yaml"
    if yaml and cfg_path.exists():
        return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return {}


def read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_system_prompt(skill: str = None) -> str:
    """Gabungkan SOUL + DESIGN + PROFIL + (skill terpilih) menjadi system prompt."""
    parts = [read_md(AGENT_DIR / "SOUL.md"), read_md(AGENT_DIR / "DESIGN.md")]
    # Sisipkan profil lembaga (jika sudah di-setup)
    try:
        from setup_profile import build_profile_context
        prof = build_profile_context()
        if prof:
            parts.append(prof)
    except Exception:
        pass
    if skill:
        sp = SKILLS_DIR / f"{skill}.md"
        if sp.exists():
            parts.append(read_md(sp))
    return "\n\n---\n\n".join(p for p in parts if p)


def list_skills():
    if not SKILLS_DIR.exists():
        return []
    return sorted(p.stem for p in SKILLS_DIR.glob("*.md"))


# ---------- Pemanggilan Model ----------
def _openai_compat_call(base_url: str, api_key: str, model: str,
                        system_prompt: str, messages: list, temperature: float,
                        max_tokens: int) -> str:
    """Panggil API yang kompatibel OpenAI (OpenAI, OpenRouter, LM Studio)."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    full_messages = [{"role": "system", "content": system_prompt}] + list(messages)
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=full_messages,
    )
    return resp.choices[0].message.content


def call_model(system_prompt: str, user_message: str, cfg: dict) -> str:
    """Panggil model AI (single turn). Gunakan call_model_multi_turn untuk chat berkelanjutan."""
    return call_model_multi_turn(system_prompt, user_message, [], cfg)


def call_model_multi_turn(system_prompt: str, user_message: str,
                          history: list, cfg: dict) -> str:
    """
    Panggil model AI dengan riwayat percakapan (multi-turn).

    Args:
        system_prompt: System prompt / instruksi AI
        user_message: Pesan terbaru dari pengguna
        history: List {"role": "user"|"assistant", "content": str} — riwayat sebelumnya
        cfg: config.yaml dict

    Provider yang didukung (set di config.yaml -> provider.active):
        anthropic  — Claude via Anthropic API (ANTHROPIC_API_KEY)
        openai     — GPT via OpenAI API (OPENAI_API_KEY)
        openrouter — 100+ model via OpenRouter (OPENROUTER_API_KEY)
        lmstudio   — Model lokal via LM Studio (LM_STUDIO_BASE_URL)
    """
    provider = (cfg.get("provider", {}) or {}).get("active", "anthropic")
    temperature = (cfg.get("provider", {}) or {}).get("temperature", 0.4)
    max_tokens = (cfg.get("provider", {}) or {}).get("max_tokens", 4096)

    # Gabungkan history + pesan baru
    messages = list(history) + [{"role": "user", "content": user_message}]

    # ── Anthropic (Claude) ──────────────────────────────────────────────
    if provider == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            model = os.environ.get("ACC_PRIMARY_MODEL", "claude-sonnet-4-5")
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": messages,
            }
            if "opus-4" not in model:
                kwargs["temperature"] = temperature
            resp = client.messages.create(**kwargs)
            return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        except Exception as e:
            return f"[Gagal memanggil Anthropic: {e}]"

    # ── OpenAI (GPT) ────────────────────────────────────────────────────
    if provider == "openai" and os.environ.get("OPENAI_API_KEY"):
        try:
            model = os.environ.get("ACC_FALLBACK_MODEL", "gpt-4o")
            return _openai_compat_call(
                base_url="https://api.openai.com/v1",
                api_key=os.environ["OPENAI_API_KEY"],
                model=model,
                system_prompt=system_prompt,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            return f"[Gagal memanggil OpenAI: {e}]"

    # ── OpenRouter (100+ model via 1 API key) ───────────────────────────
    if provider == "openrouter" and os.environ.get("OPENROUTER_API_KEY"):
        try:
            model = os.environ.get(
                "OPENROUTER_MODEL",
                (cfg.get("provider", {}) or {}).get("openrouter_model", "anthropic/claude-sonnet-4-5"),
            )
            base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            return _openai_compat_call(
                base_url=base_url,
                api_key=os.environ["OPENROUTER_API_KEY"],
                model=model,
                system_prompt=system_prompt,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            return f"[Gagal memanggil OpenRouter: {e}]"

    # ── LM Studio (model lokal di komputer) ─────────────────────────────
    if provider == "lmstudio":
        try:
            base_url = os.environ.get(
                "LM_STUDIO_BASE_URL",
                (cfg.get("provider", {}) or {}).get("lmstudio_base_url", "http://localhost:1234/v1"),
            )
            model = os.environ.get(
                "LM_STUDIO_MODEL",
                (cfg.get("provider", {}) or {}).get("lmstudio_model", "local-model"),
            )
            api_key = os.environ.get("LM_STUDIO_API_KEY", "lm-studio")
            return _openai_compat_call(
                base_url=base_url,
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            return f"[Gagal memanggil LM Studio: {e}]"

    return (f"[Provider '{provider}' tidak aktif atau API key kosong]. "
            "Periksa data/.env dan provider.active di data/config.yaml.")


def save_session(role: str, text: str):
    day = datetime.now().strftime("%Y-%m-%d")
    f = DATA_DIR / "sessions" / f"{day}.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": datetime.now().isoformat(), "role": role, "text": text},
                            ensure_ascii=False) + "\n")


# ---------- Perintah ----------
def cmd_doctor():
    load_env()
    cfg = load_config()
    print("=== ACC Doctor ===")
    print(f"ACC_HOME      : {ACC_HOME}")
    print(f"YAML tersedia : {bool(yaml)}")
    print(f"dotenv        : {bool(load_dotenv)}")
    print(f"Provider aktif: {(cfg.get('provider', {}) or {}).get('active', '-')}")
    keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY",
            "LM_STUDIO_BASE_URL", "LM_STUDIO_MODEL", "GEMINI_API_KEY"]
    for k in keys:
        print(f"  {k:22}: {'terisi' if os.environ.get(k) else 'kosong'}")
    print(f"Skill tersedia: {', '.join(list_skills()) or '(tidak ada)'}")
    mcp = DATA_DIR / "mcp.json"
    if mcp.exists():
        servers = json.loads(mcp.read_text()).get("mcpServers", {})
        on = [n for n, v in servers.items() if v.get("enabled")]
        print(f"MCP aktif     : {', '.join(on) or '(tidak ada yang enabled)'}")


def cmd_chat(skill=None):
    load_env()
    cfg = load_config()
    skills = list_skills()
    if skill is None:
        print("Skill tersedia:", ", ".join(skills))
        skill = input("Pilih skill (kosong=umum): ").strip() or None
    sysprompt = build_system_prompt(skill)
    print(f"\n🛸 Arunika siap{f' [skill: {skill}]' if skill else ''}. Ketik 'exit' untuk keluar.\n")
    while True:
        try:
            msg = input("Anda > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSampai jumpa.")
            break
        if msg.lower() in ("exit", "quit", "keluar"):
            break
        if not msg:
            continue
        save_session("user", msg)
        reply = call_model(sysprompt, msg, cfg)
        save_session("assistant", reply)
        print(f"\nArunika > {reply}\n")


def cmd_cron():
    """Jalankan job yang jatuh tempo. Gunakan croniter bila tersedia."""
    load_env()
    sched = DATA_DIR / "schedule.yaml"
    if not (yaml and sched.exists()):
        print("schedule.yaml / PyYAML tidak tersedia.")
        return
    jobs = (yaml.safe_load(sched.read_text(encoding="utf-8")) or {}).get("jobs", [])
    now = datetime.now()
    try:
        from croniter import croniter
    except ImportError:
        print("croniter belum terpasang; menampilkan daftar job saja.")
        for j in jobs:
            print(f"  - {j['id']}: {j.get('cron')} -> {j.get('action')}")
        return
    due = []
    for j in jobs:
        expr = j.get("cron")
        if not expr:
            continue
        itr = croniter(expr, now)
        prev = itr.get_prev(datetime)
        # jatuh tempo jika kejadian sebelumnya dalam 1 menit terakhir
        if (now - prev).total_seconds() < 60:
            due.append(j)
    if not due:
        print(f"[{now:%H:%M}] Tidak ada job jatuh tempo.")
        return
    cfg = load_config()
    for j in due:
        print(f"[{now:%H:%M}] Menjalankan: {j['id']}")
        sysprompt = build_system_prompt(j.get("skill"))
        out = call_model(sysprompt, j.get("action", ""), cfg)
        save_session("cron:" + j["id"], out)
        print(out[:500])


def cmd_heal(spec=None):
    """Jalankan Self-Healing Code Loop (mode otomatis penuh)."""
    if spec is None:
        print()
        print("=" * 50)
        print("  SELF-HEALING CODE LOOP")
        print("  Mode otomatis: Generate -> Test -> Fix -> Deploy")
        print("=" * 50)
        print("Contoh spek:")
        print("  - Buat fungsi hitung PPN 11% beserta testnya")
        print("  - Buat parser CSV ke dict dengan validasi header")
        print("  - Buat fungsi konversi tanggal Indonesia ke ISO")
        print()
        spec = input("Spek tugas > ").strip()
    if not spec:
        print("Spek kosong, batal.")
        return
    try:
        from self_healing import self_healing_loop
    except Exception as e:
        print(f"Tidak bisa memuat self_healing: {e}")
        return
    workdir = ACC_HOME / "build" / ("tugas-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    # auto_approve_deploy=True -> tidak ada konfirmasi tengah jalan
    self_healing_loop(spec, workdir, max_iter=5, auto_approve_deploy=True)
    print()
    input("Tekan Enter untuk kembali ke menu...")


def cmd_research():
    """Jalankan modul Research dengan web search."""
    research_path = ACC_HOME / "src" / "research.py"
    if not research_path.exists():
        print()
        print("=" * 60)
        print("  [X] File src/research.py belum ada di folder ini.")
        print("=" * 60)
        print("  Anda perlu update folder ACC dari zip terbaru.")
        print("  File yang harus ada:")
        print("    - src/research.py")
        print("    - src/setup_profile.py")
        print("    - data/profile.yaml")
        print("  Salin ketiga file itu dari zip terbaru ke USB Anda.")
        print("=" * 60)
        input("\nTekan Enter untuk kembali ke menu...")
        return
    try:
        # Pastikan src/ ada di path
        src_dir = str(ACC_HOME / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        from research import interactive
        interactive()
    except ImportError as e:
        print(f"\n[X] Gagal import: {e}")
        print("    Pastikan paket 'anthropic' & 'rich' terpasang.")
        input("\nTekan Enter untuk kembali...")
    except Exception as e:
        print(f"\n[X] Error: {e}")
        input("\nTekan Enter untuk kembali...")


def cmd_profile():
    """Setup profil lembaga."""
    profile_script = ACC_HOME / "src" / "setup_profile.py"
    if not profile_script.exists():
        print()
        print("=" * 60)
        print("  [X] File src/setup_profile.py belum ada.")
        print("=" * 60)
        print("  Update folder ACC dari zip terbaru.")
        print("=" * 60)
        input("\nTekan Enter untuk kembali...")
        return
    try:
        import subprocess
        subprocess.run([sys.executable, str(profile_script)], cwd=str(ACC_HOME))
    except Exception as e:
        print(f"Error: {e}")
        input("\nTekan Enter untuk kembali...")


def cmd_selftest():
    """Verifikasi semua modul & konfigurasi bisa jalan."""
    print()
    print("=" * 60)
    print("  ACC SELF-TEST")
    print("=" * 60)
    checks = []

    # 1. Folder dasar
    for d in ["src", "data", "agent", "agent/skills"]:
        p = ACC_HOME / d
        checks.append((f"Folder {d}/", p.exists()))

    # 2. File inti
    for f in ["src/acc.py", "src/self_healing.py", "src/setup_profile.py",
              "src/research.py", "src/setup_whatsapp.py",
              "data/.env", "data/config.yaml", "data/profile.yaml",
              "agent/SOUL.md", "agent/HEARTBEAT.md", "agent/DESIGN.md"]:
        p = ACC_HOME / f
        checks.append((f"File {f}", p.exists()))

    # 3. Paket Python penting
    for pkg in ["yaml", "dotenv", "anthropic", "rich"]:
        try:
            __import__(pkg)
            ok = True
        except ImportError:
            ok = False
        checks.append((f"Paket {pkg}", ok))

    # 4. Import modul ACC internal
    src_dir = str(ACC_HOME / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    for mod in ["self_healing", "setup_profile", "research", "setup_whatsapp"]:
        try:
            __import__(mod)
            ok = True
            err = ""
        except Exception as e:
            ok = False
            err = str(e)[:60]
        checks.append((f"Import {mod}", ok, err))

    # 5. API key
    load_env()
    for k in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
        v = os.environ.get(k, "")
        checks.append((f"ENV {k}", bool(v.strip()),
                       "(kosong)" if not v.strip() else f"{v[:8]}..."))

    # 6. Profil lembaga
    try:
        from setup_profile import build_profile_context
        prof = build_profile_context()
        checks.append(("Profil lembaga terisi", bool(prof)))
    except Exception as e:
        checks.append(("Profil lembaga terisi", False, str(e)[:40]))

    # 7. Skills
    skills = list_skills()
    checks.append((f"Skill terdeteksi ({len(skills)})", len(skills) > 0,
                   ", ".join(skills[:3]) + ("..." if len(skills) > 3 else "")))

    # Render hasil
    try:
        from rich.console import Console
        from rich.table import Table
        c = Console()
        t = Table(show_header=True, header_style="bold cyan")
        t.add_column("Cek", style="white")
        t.add_column("Status", justify="center")
        t.add_column("Catatan", style="dim")
        ok_count = 0
        for row in checks:
            name = row[0]; ok = row[1]
            note = row[2] if len(row) > 2 else ""
            status = "[green]OK[/green]" if ok else "[red]X[/red]"
            if ok: ok_count += 1
            t.add_row(name, status, note)
        c.print(t)
        c.print(f"\n[bold]Skor: {ok_count}/{len(checks)} ({100*ok_count//len(checks)}%)[/bold]")
        if ok_count == len(checks):
            c.print("[bold green]Semua siap. ACC bisa dipakai penuh.[/bold green]")
        else:
            c.print("[yellow]Ada item belum siap (lihat baris dengan X di atas).[/yellow]")
    except ImportError:
        ok_count = 0
        for row in checks:
            name = row[0]; ok = row[1]; note = row[2] if len(row) > 2 else ""
            print(f"  [{'OK' if ok else ' X'}] {name:<35} {note}")
            if ok: ok_count += 1
        print(f"\nSkor: {ok_count}/{len(checks)}")

    input("\nTekan Enter untuk kembali ke menu...")


def cmd_whatsapp():
    """Test kirim WhatsApp via Twilio."""
    wa_path = ACC_HOME / "src" / "whatsapp_handler.py"
    if not wa_path.exists():
        print("\n[X] src/whatsapp_handler.py belum ada.")
        input("Tekan Enter...")
        return
    src_dir = str(ACC_HOME / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    try:
        import whatsapp_handler as wa
    except ImportError as e:
        print(f"\n[X] Gagal import: {e}")
        print("    Pastikan 'twilio' & 'rich' terpasang.")
        input("Tekan Enter...")
        return

    print("""
============================================
  WHATSAPP - Test Twilio
============================================
  [1] Test koneksi (tidak kirim pesan)
  [2] Kirim pesan freeform (24-jam window)
  [3] Kirim template (untuk inisiasi)
  [0] Kembali
""")
    c = input("Pilih > ").strip()
    if c == "1":
        wa.cli_test()
    elif c == "2":
        to = input("Nomor tujuan (mis. 08112342165) > ").strip()
        if not to:
            return
        body = input("Isi pesan > ").strip()
        if not body:
            return
        ok, info = wa.send_message(to, body)
        wa._print_result(ok, info)
    elif c == "3":
        to = input("Nomor tujuan > ").strip()
        if not to:
            return
        sid = input("Content SID template (HX...) > ").strip()
        if not sid:
            return
        var_raw = input('Variables JSON (mis. {"1":"12/1","2":"3pm"}) atau kosong > ').strip()
        variables = None
        if var_raw:
            try:
                variables = json.loads(var_raw)
            except Exception:
                print("JSON tidak valid, dibatalkan.")
                return
        ok, info = wa.send_template(to, sid, variables)
        wa._print_result(ok, info)
    input("\nTekan Enter untuk kembali...")


def cmd_menu():
    load_env()
    while True:
        # Status profil
        try:
            src_dir = str(ACC_HOME / "src")
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            from setup_profile import build_profile_context
            prof_status = "OK terisi" if build_profile_context() else "X BELUM"
        except Exception:
            prof_status = "X modul belum ada"
        # Status API key
        api_status = "OK" if os.environ.get("ANTHROPIC_API_KEY", "").strip() else "X kosong"
        print(f"""
============================================
  ARUNIKA COMMAND CENTRE
  Profil Lembaga : {prof_status}
  API Key        : {api_status}
============================================
  [1] Chat dengan Arunika
  [2] Pilih skill & chat
  [3] Research (web search + approve + pakai)
  [4] Self-Healing Code Loop (Generate-Test-Fix-Deploy)
  [5] Jalankan tugas terjadwal (cron sekali)
  [6] Doctor (cek konfigurasi)
  [7] Daftar skill
  [8] Setup Profil Lembaga
  [9] Self-Test (cek semua modul siap)
  [A] WhatsApp - Test kirim pesan (Twilio)
  [0] Keluar
""")
        c = input("Pilih > ").strip()
        if c == "1":
            cmd_chat(skill=None)
        elif c == "2":
            cmd_chat()
        elif c == "3":
            cmd_research()
        elif c == "4":
            cmd_heal()
        elif c == "5":
            cmd_cron()
        elif c == "6":
            cmd_doctor()
        elif c == "7":
            print("Skill:", ", ".join(list_skills()))
            input("\nTekan Enter...")
        elif c == "8":
            cmd_profile()
        elif c == "9":
            cmd_selftest()
        elif c.upper() == "A":
            cmd_whatsapp()
        elif c == "0":
            print("Sampai jumpa.")
            break


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "menu"
    if cmd == "menu":
        cmd_menu()
    elif cmd == "chat":
        cmd_chat()
    elif cmd == "cron":
        cmd_cron()
    elif cmd == "doctor":
        cmd_doctor()
    elif cmd == "heal":
        spec = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        cmd_heal(spec)
    elif cmd == "setup-whatsapp":
        try:
            import subprocess
            subprocess.run([sys.executable, "src/setup_whatsapp.py"], cwd=ACC_HOME)
        except Exception as e:
            print(f"Error: {e}")
    elif cmd == "research":
        cmd_research()
    elif cmd == "profile" or cmd == "setup-profile":
        cmd_profile()
    elif cmd == "selftest" or cmd == "test":
        cmd_selftest()
    else:
        print(f"Perintah tidak dikenal: {cmd}")
        print("Gunakan: menu | chat | cron | doctor | heal | research | profile | selftest | setup-whatsapp")


if __name__ == "__main__":
    main()
