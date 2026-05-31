"""
Bot Commands - ACC WhatsApp
Mirip Telegram bot: /command dengan menu interaktif teks.

Semua perintah yang tersedia:
  /start /halo       - Salam pembuka
  /menu /help        - Menu utama lengkap
  /status            - Status sesi aktif
  /model             - Tampilkan & ganti model AI
  /model <nama>      - Ganti ke model tertentu
  /skill             - Tampilkan & ganti skill
  /skill <nama>      - Aktifkan skill tertentu
  /skill off         - Nonaktifkan skill (mode umum)
  /skills            - Daftar semua skill
  /pdf               - Export respons terakhir ke PDF
  /pdf <teks>        - Buat konten baru lalu ke PDF
  /history           - Riwayat percakapan singkat
  /reset             - Reset percakapan
  /about             - Tentang ACC
"""
import os
from pathlib import Path
from datetime import datetime

# ── Katalog model yang tersedia ─────────────────────────────
MODELS: dict[str, dict] = {
    "claude-sonnet": {
        "label": "Claude Sonnet 4.5",
        "desc":  "Cepat & pintar (recommended)",
        "icon":  "🟣",
        "provider": "anthropic",
        "model":    "claude-sonnet-4-5",
    },
    "claude-opus": {
        "label": "Claude Opus 4.8",
        "desc":  "Paling pintar & detail",
        "icon":  "💜",
        "provider": "anthropic",
        "model":    "claude-opus-4-8",
    },
    "claude-haiku": {
        "label": "Claude Haiku 4.5",
        "desc":  "Tercepat & paling hemat",
        "icon":  "🔵",
        "provider": "anthropic",
        "model":    "claude-haiku-4-5-20251001",
    },
    "gpt4o": {
        "label": "GPT-4o",
        "desc":  "OpenAI GPT-4o",
        "icon":  "🟢",
        "provider": "openai",
        "model":    "gpt-4o",
    },
    "openrouter": {
        "label": "OpenRouter",
        "desc":  "100+ model via 1 key",
        "icon":  "🌐",
        "provider": "openrouter",
        "model":    "anthropic/claude-sonnet-4-5",
    },
    "local": {
        "label": "LM Studio Lokal",
        "desc":  "Model lokal gratis",
        "icon":  "💻",
        "provider": "lmstudio",
        "model":    "local-model",
    },
}

# Alias singkat untuk ganti model
MODEL_ALIASES: dict[str, str] = {
    "claude": "claude-sonnet",
    "sonnet": "claude-sonnet",
    "opus":   "claude-opus",
    "haiku":  "claude-haiku",
    "gpt":    "gpt4o",
    "gpt4":   "gpt4o",
    "or":     "openrouter",
    "local":  "local",
    "lokal":  "local",
    "lm":     "local",
    "lmstudio": "local",
}

LINE = "━" * 24


# ── Helper internal ──────────────────────────────────────────
def _skill_list(acc_home: Path) -> list[str]:
    d = acc_home / "agent" / "skills"
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.md"))


def _skill_desc(skill_name: str, acc_home: Path) -> str:
    """Baca baris pertama file skill sebagai deskripsi singkat."""
    path = acc_home / "agent" / "skills" / f"{skill_name}.md"
    if not path.exists():
        return ""
    try:
        lines = path.read_text("utf-8").splitlines()
        for line in lines:
            line = line.strip().lstrip("#").strip()
            if line and not line.startswith("---"):
                return line[:60]
    except Exception:
        pass
    return ""


# ── Format pesan ────────────────────────────────────────────
def fmt_menu(acc_home: Path, session) -> str:
    skills = _skill_list(acc_home)
    model_info = MODELS.get(session.model_key, {})

    skill_lines = ""
    for s in skills:
        active_mark = " ✅" if s == session.skill else ""
        skill_lines += f"\n  /skill {s}{active_mark}"

    if not skill_lines:
        skill_lines = "\n  (belum ada skill)"

    model_active = model_info.get("label", session.model_key)
    skill_active = session.skill or "(mode umum)"

    return (
        f"🤖 *ARUNIKA COMMAND CENTRE*\n"
        f"PT. Arunika Teknologi Global\n"
        f"{LINE}\n\n"
        f"*Status aktif:*\n"
        f"  🧠 Model : {model_active}\n"
        f"  📚 Skill : {skill_active}\n\n"
        f"{LINE}\n"
        f"*📚 SKILL TERSEDIA:*"
        f"{skill_lines}\n\n"
        f"  /skills — lihat deskripsi lengkap\n"
        f"  /skill off — kembali ke mode umum\n\n"
        f"{LINE}\n"
        f"*🧠 GANTI MODEL AI:*\n"
        f"  /model — lihat semua pilihan\n"
        f"  /model claude-sonnet — Claude Sonnet 🟣\n"
        f"  /model claude-opus   — Claude Opus 💜\n"
        f"  /model claude-haiku  — Claude Haiku 🔵\n"
        f"  /model gpt4o         — GPT-4o 🟢\n"
        f"  /model local         — LM Studio 💻\n\n"
        f"{LINE}\n"
        f"*📄 DOKUMEN PDF:*\n"
        f"  /pdf          — export respons terakhir\n"
        f"  /pdf <teks>   — buat konten baru ke PDF\n\n"
        f"{LINE}\n"
        f"*⚙️ SESI & INFO:*\n"
        f"  /status   — info model & skill aktif\n"
        f"  /history  — riwayat percakapan singkat\n"
        f"  /reset    — mulai percakapan baru\n"
        f"  /about    — tentang ACC\n"
        f"  /help     — tampilkan menu ini\n\n"
        f"{LINE}\n"
        f"💬 Ketik pesan biasa untuk chat dengan AI"
    )


def fmt_model_menu(current_key: str) -> str:
    current = MODELS.get(current_key, {})
    lines = []
    for key, m in MODELS.items():
        mark = " ✅ *[AKTIF]*" if key == current_key else ""
        lines.append(f"{m['icon']} *{m['label']}*{mark}\n   /model {key} — {m['desc']}")

    return (
        f"🧠 *PILIH MODEL AI*\n"
        f"{LINE}\n"
        f"Aktif: *{current.get('label', current_key)}*\n\n"
        + "\n\n".join(lines)
        + f"\n\n{LINE}\n"
        f"Kirim */model <nama>* untuk ganti\n"
        f"Contoh: */model claude-haiku*"
    )


def fmt_skill_menu(acc_home: Path, current_skill: str | None) -> str:
    skills = _skill_list(acc_home)
    if not skills:
        return "❌ Belum ada skill tersedia di folder agent/skills/"

    lines = []
    for s in skills:
        mark = " ✅ *[AKTIF]*" if s == current_skill else ""
        desc = _skill_desc(s, acc_home)
        desc_text = f"\n   _{desc}_" if desc else ""
        lines.append(f"📌 /skill {s}{mark}{desc_text}")

    return (
        f"📚 *DAFTAR SKILL*\n"
        f"{LINE}\n"
        f"Aktif: *{current_skill or '(mode umum)'}*\n\n"
        + "\n\n".join(lines)
        + f"\n\n{LINE}\n"
        f"Kirim */skill <nama>* untuk aktifkan\n"
        f"Kirim */skill off* untuk mode umum"
    )


def fmt_status(session, acc_home: Path) -> str:
    model_info = MODELS.get(session.model_key, {})
    pairs = session.message_count()
    last = session.last_active[:16].replace("T", " ") if session.last_active else "-"
    reg = session.registered_at[:10] if session.registered_at else "-"

    return (
        f"📊 *STATUS SESI ANDA*\n"
        f"{LINE}\n"
        f"👤 Nama  : {session.name or 'Tidak diketahui'}\n"
        f"📱 No    : {session.phone}\n"
        f"📋 Plan  : {session.plan.upper()}\n"
        f"{LINE}\n"
        f"🧠 Model : *{model_info.get('label', session.model_key)}*\n"
        f"   Provider: {model_info.get('provider', '-')}\n"
        f"   Model   : {model_info.get('model', '-')}\n"
        f"📚 Skill  : *{session.skill or '(mode umum)'}*\n"
        f"{LINE}\n"
        f"💬 Riwayat     : {pairs} pesan\n"
        f"🕐 Terakhir    : {last}\n"
        f"📅 Terdaftar   : {reg}\n"
        f"{LINE}\n"
        f"/model — ganti model\n"
        f"/skill — ganti skill\n"
        f"/reset — reset sesi"
    )


def fmt_about() -> str:
    return (
        f"ℹ️ *ARUNIKA COMMAND CENTRE v1*\n"
        f"{LINE}\n"
        f"PT. Arunika Teknologi Global\n"
        f"📧 corsec@arunika2045.com\n"
        f"🌐 arunika2045.com\n\n"
        f"*Asisten AI pintar via WhatsApp*\n"
        f"untuk kebutuhan bisnis profesional:\n\n"
        f"  📊 Riset & analisis pasar\n"
        f"  📝 Proposal & laporan\n"
        f"  💰 Laporan keuangan PSAK\n"
        f"  📊 Presentasi visual\n"
        f"  ✉️  Surat penawaran\n\n"
        f"*Powered by:*\n"
        f"  🟣 Anthropic Claude\n"
        f"  🟢 OpenAI GPT-4o\n"
        f"  🌐 OpenRouter (100+ model)\n"
        f"  💻 LM Studio (model lokal)\n\n"
        f"{LINE}\n"
        f"© 2025 PT. Arunika Teknologi Global"
    )


def fmt_history(session) -> str:
    if not session.history:
        return "💬 Belum ada riwayat percakapan.\n\nKirim pesan pertama Anda!"

    recent = session.history[-6:]
    lines = []
    for msg in recent:
        role = "Anda" if msg["role"] == "user" else "ACC"
        content = msg["content"]
        preview = content[:100] + ("..." if len(content) > 100 else "")
        lines.append(f"*{role}:* {preview}")

    total = session.message_count()
    return (
        f"💬 *RIWAYAT (3 terakhir dari {total} pesan)*\n"
        f"{LINE}\n\n"
        + "\n\n".join(lines)
    )


def fmt_start(session) -> str:
    nama = f", *{session.name}*" if session.name else ""
    return (
        f"👋 Halo{nama}!\n\n"
        f"Selamat datang di *Arunika Command Centre* 🤖\n"
        f"PT. Arunika Teknologi Global\n\n"
        f"Saya asisten AI siap membantu untuk:\n"
        f"  📊 Riset & analisis\n"
        f"  📝 Proposal & laporan\n"
        f"  💰 Laporan keuangan\n"
        f"  📊 Presentasi\n"
        f"  ✉️  Surat penawaran\n\n"
        f"Ketik */menu* untuk lihat semua fitur.\n"
        f"Atau langsung kirim pertanyaan Anda! 💬"
    )


# ── Aksi command ────────────────────────────────────────────
def set_skill(skill_name: str, session, session_mgr, acc_home: Path) -> str:
    if skill_name.lower() in ("off", "none", "umum", "-", "0"):
        session.skill = None
        session_mgr.save(session)
        return (
            "✅ Skill dinonaktifkan.\n"
            "Mode umum aktif — saya siap menjawab segala topik."
        )

    available = _skill_list(acc_home)
    if skill_name not in available:
        opts = "\n".join(f"  • {s}" for s in available) or "  (tidak ada)"
        return (
            f"❌ Skill *{skill_name}* tidak ditemukan.\n\n"
            f"Skill tersedia:\n{opts}\n\n"
            f"Gunakan: /skill <nama>"
        )

    session.skill = skill_name
    session_mgr.save(session)
    desc = _skill_desc(skill_name, acc_home)
    desc_text = f"\n_{desc}_" if desc else ""
    return (
        f"✅ Skill *{skill_name}* diaktifkan!{desc_text}\n\n"
        f"Saya siap membantu topik *{skill_name}*.\n"
        f"Ketik pertanyaan atau topik Anda. 💬"
    )


def set_model(model_key: str, session, session_mgr) -> str:
    key = MODEL_ALIASES.get(model_key.lower(), model_key.lower())
    if key not in MODELS:
        opts = "\n".join(
            f"  /model {k} — {v['label']}" for k, v in MODELS.items()
        )
        return (
            f"❌ Model *{model_key}* tidak dikenal.\n\n"
            f"Pilihan:\n{opts}"
        )

    m = MODELS[key]
    session.model_key = key
    session.model_config = {"provider": m["provider"], "model": m["model"]}
    session_mgr.save(session)
    return (
        f"✅ Model berganti ke *{m['label']}*\n"
        f"{m['icon']} {m['desc']}\n\n"
        f"Percakapan selanjutnya menggunakan model ini."
    )


def make_pdf(session, acc_home: Path) -> str:
    """Generate PDF dari respons AI terakhir di sesi."""
    try:
        from pdf_generator import generate_pdf_from_text
    except ImportError:
        return "❌ Modul PDF belum terpasang.\nJalankan: pip install fpdf2"

    last = session.last_ai_response()
    if not last:
        return (
            "❌ Belum ada respons untuk dijadikan PDF.\n\n"
            "Kirim pertanyaan dulu, lalu /pdf setelah menerima respons.\n"
            "Atau: /pdf <teks yang ingin dijadikan PDF>"
        )

    try:
        path = generate_pdf_from_text(last, output_dir=acc_home / "data" / "output")
        fname = Path(path).name
        webhook_url = os.environ.get("WA_WEBHOOK_URL", "").rstrip("/")
        if webhook_url:
            url = f"{webhook_url}/files/{fname}"
            return f"📄 *PDF Siap!*\n\nFile: {fname}\n🔗 {url}"
        return (
            f"📄 *PDF Disimpan*\n\n"
            f"File: {fname}\n"
            f"Lokasi: data/output/{fname}\n\n"
            f"_Isi WA_WEBHOOK_URL di .env agar PDF bisa diunduh langsung._"
        )
    except Exception as e:
        return f"❌ Gagal buat PDF: {e}"


# ── Entry point utama ────────────────────────────────────────
COMMAND_WORDS = {
    "/start", "/halo", "/hai", "/hi", "/hello",
    "/menu", "/help", "/bantuan",
    "/status",
    "/about",
    "/reset",
    "/history",
    "/skills",
    "/skill",
    "/model", "/models",
    "/pdf",
}


def handle(phone: str, name: str, body: str,
           session_mgr, acc_home: Path) -> str | None:
    """
    Proses pesan masuk dari WhatsApp.

    Return:
      str  → langsung kirim sebagai reply (tanpa AI)
      None → proses ke AI (dihandle oleh webhook_server)
    """
    session = session_mgr.get(phone, name)
    text = body.strip()
    lower = text.lower()

    # ── /start, halo ─────────────────────────────────────────
    if lower in ("/start", "start", "/halo", "halo", "/hai", "hai",
                 "/hi", "hi", "/hello", "hello"):
        return fmt_start(session)

    # ── /menu, /help ─────────────────────────────────────────
    if lower in ("/menu", "menu", "/help", "help", "/bantuan", "bantuan"):
        return fmt_menu(acc_home, session)

    # ── /status ──────────────────────────────────────────────
    if lower == "/status":
        return fmt_status(session, acc_home)

    # ── /about ───────────────────────────────────────────────
    if lower == "/about":
        return fmt_about()

    # ── /reset ───────────────────────────────────────────────
    if lower == "/reset":
        session_mgr.reset(phone)
        return (
            "✅ Sesi direset. Percakapan baru dimulai.\n\n"
            "Ketik pesan atau /menu untuk lihat panduan."
        )

    # ── /history ─────────────────────────────────────────────
    if lower == "/history":
        return fmt_history(session)

    # ── /skills ──────────────────────────────────────────────
    if lower == "/skills":
        return fmt_skill_menu(acc_home, session.skill)

    # ── /skill [nama] ────────────────────────────────────────
    if lower == "/skill":
        return fmt_skill_menu(acc_home, session.skill)

    if lower.startswith("/skill "):
        return set_skill(text[7:].strip(), session, session_mgr, acc_home)

    # ── /model [nama] ────────────────────────────────────────
    if lower in ("/model", "/models"):
        return fmt_model_menu(session.model_key)

    if lower.startswith("/model "):
        return set_model(text[7:].strip(), session, session_mgr)

    # ── /pdf [opsional teks] ─────────────────────────────────
    if lower == "/pdf":
        return make_pdf(session, acc_home)

    if lower.startswith("/pdf "):
        # Ada teks tambahan -> proses AI dulu, lalu PDF
        # Tandai pending agar webhook_server tahu harus generate PDF
        session.pending = "pdf"
        session_mgr.save(session)
        return None  # lanjut ke AI dengan body = teks setelah /pdf

    # ── Perintah tidak dikenal ───────────────────────────────
    if text.startswith("/"):
        return (
            f"❓ Perintah *{text.split()[0]}* tidak dikenal.\n\n"
            f"Kirim */menu* untuk melihat semua perintah."
        )

    # ── Pesan biasa → AI ─────────────────────────────────────
    return None


def extract_pdf_prompt(body: str) -> str:
    """Ambil teks setelah '/pdf '."""
    if body.strip().lower().startswith("/pdf "):
        return body.strip()[5:].strip()
    return body.strip()
