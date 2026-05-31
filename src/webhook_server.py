#!/usr/bin/env python3
"""
ACC WhatsApp Webhook Server
PT. Arunika Teknologi Global

Alur: WhatsApp -> Twilio -> Webhook (Flask di Drive E:) -> ACC AI -> WhatsApp

Cara pakai:
  1. python src/webhook_server.py
  2. Expose via ngrok: ngrok http 5000
  3. Copy URL ngrok ke Twilio Console -> WhatsApp Sandbox -> Webhook URL
     Format: https://<ngrok-url>/webhook/whatsapp

Perintah khusus dari WhatsApp:
  /pdf <teks>      -> generate PDF dari respons AI, kirim balik link
  /skill <nama>    -> gunakan skill tertentu (riset, proposal, laporan-kerja, dll)
  /skills          -> lihat daftar skill tersedia
  /reset           -> reset sesi percakapan
  /help            -> tampilkan panduan
"""
import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(ACC_HOME / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(ACC_HOME / "data" / ".env")
except ImportError:
    pass

try:
    from flask import Flask, request, Response
    FLASK_OK = True
except ImportError:
    FLASK_OK = False

try:
    from twilio.twiml.messaging_response import MessagingResponse
    TWIML_OK = True
except ImportError:
    TWIML_OK = False

# Session per nomor HP (simpan riwayat percakapan dalam memori)
# Format: {phone: {"messages": [...], "skill": str|None, "last_activity": datetime}}
_sessions: dict = defaultdict(lambda: {"messages": [], "skill": None, "last_activity": None})
_session_lock = threading.Lock()
MAX_HISTORY = 10  # maksimal pesan per sesi yang disimpan


# ============ SESSION ============
def get_session(phone: str) -> dict:
    with _session_lock:
        s = _sessions[phone]
        s["last_activity"] = datetime.now()
        return s


def reset_session(phone: str):
    with _session_lock:
        _sessions[phone] = {"messages": [], "skill": None, "last_activity": datetime.now()}


def add_to_history(phone: str, role: str, content: str):
    with _session_lock:
        s = _sessions[phone]
        s["messages"].append({"role": role, "content": content})
        # Potong riwayat jika melebihi batas
        if len(s["messages"]) > MAX_HISTORY * 2:
            s["messages"] = s["messages"][-(MAX_HISTORY * 2):]


# ============ AI ENGINE ============
def call_acc_ai(phone: str, user_message: str, skill: str = None) -> str:
    """Panggil ACC AI engine dengan riwayat percakapan."""
    try:
        from acc import load_env, load_config, build_system_prompt, call_model_multi_turn
        load_env()
        cfg = load_config()
    except ImportError:
        try:
            import acc
            acc.load_env()
            cfg = acc.load_config()
            sysprompt = acc.build_system_prompt(skill)
            session = get_session(phone)
            reply = acc.call_model(sysprompt, user_message, cfg)
            add_to_history(phone, "user", user_message)
            add_to_history(phone, "assistant", reply)
            return reply
        except Exception as e:
            return f"[Error memanggil AI: {e}]"

    try:
        sysprompt = build_system_prompt(skill)
        session = get_session(phone)
        reply = call_model_multi_turn(sysprompt, user_message, session["messages"], cfg)
        add_to_history(phone, "user", user_message)
        add_to_history(phone, "assistant", reply)
        return reply
    except Exception as e:
        return f"[Error: {e}]"


# ============ PERINTAH KHUSUS ============
HELP_TEXT = """*Arunika Command Centre*
Perintah yang tersedia:

/skill <nama> - Ganti skill aktif
/skills - Lihat daftar skill
/pdf - Simpan respons terakhir ke PDF
/reset - Reset percakapan
/help - Panduan ini

Kirim pesan biasa untuk chat dengan Arunika.
Contoh: _Buatkan proposal untuk klien baru_"""


def handle_special_command(phone: str, body: str) -> str | None:
    """Return reply jika perintah khusus, None jika bukan."""
    lower = body.strip().lower()

    if lower in ("/help", "help", "bantuan"):
        return HELP_TEXT

    if lower == "/reset":
        reset_session(phone)
        return "Sesi direset. Percakapan baru dimulai."

    if lower == "/skills":
        try:
            from acc import list_skills
            skills = list_skills()
            if skills:
                return "Skill tersedia:\n" + "\n".join(f"• {s}" for s in skills)
            return "Belum ada skill terdaftar."
        except Exception:
            return "Tidak bisa membaca daftar skill."

    if lower.startswith("/skill "):
        skill_name = body.strip()[7:].strip()
        if skill_name:
            skills_dir = ACC_HOME / "agent" / "skills"
            if (skills_dir / f"{skill_name}.md").exists():
                with _session_lock:
                    _sessions[phone]["skill"] = skill_name
                return f"Skill *{skill_name}* aktif. Silakan mulai percakapan."
            else:
                try:
                    from acc import list_skills
                    avail = ", ".join(list_skills())
                except Exception:
                    avail = "(tidak bisa dibaca)"
                return f"Skill '{skill_name}' tidak ditemukan.\nTersedia: {avail}"

    if lower.startswith("/pdf"):
        return handle_pdf_command(phone, body[4:].strip())

    return None


def handle_pdf_command(phone: str, extra_prompt: str) -> str:
    """Generate PDF dari respons AI terakhir atau dari prompt baru."""
    try:
        from pdf_generator import generate_pdf_from_text
    except ImportError:
        return "Modul PDF belum tersedia. Pastikan fpdf2 terpasang: pip install fpdf2"

    # Ambil respons terakhir dari sesi atau generate baru
    session = get_session(phone)
    messages = session.get("messages", [])

    if extra_prompt:
        # Generate konten baru dulu
        content = call_acc_ai(phone, extra_prompt, session.get("skill"))
    elif messages:
        # Pakai respons terakhir assistant
        last_ai = next((m["content"] for m in reversed(messages)
                        if m["role"] == "assistant"), None)
        if not last_ai:
            return "Belum ada respons untuk dijadikan PDF. Kirim prompt dulu."
        content = last_ai
    else:
        return "Belum ada konten. Kirim prompt dulu atau gunakan: /pdf <permintaan>"

    try:
        pdf_path = generate_pdf_from_text(content, output_dir=ACC_HOME / "data" / "output")
        # Kirim konfirmasi + info file (Twilio media butuh public URL)
        filename = Path(pdf_path).name
        webhook_host = os.environ.get("WA_WEBHOOK_URL", "").rstrip("/")
        if webhook_host:
            pdf_url = f"{webhook_host}/files/{filename}"
            return f"PDF siap: {pdf_url}\n\nFile: {filename}"
        else:
            return (f"PDF disimpan: data/output/{filename}\n\n"
                    f"Set WA_WEBHOOK_URL di .env agar PDF bisa dikirim langsung via WhatsApp.")
    except Exception as e:
        return f"Gagal buat PDF: {e}"


# ============ FLASK APP ============
def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    @app.route("/", methods=["GET"])
    def index():
        return "ACC WhatsApp Webhook Server aktif.", 200

    @app.route("/webhook/whatsapp", methods=["POST"])
    def whatsapp_webhook():
        """Terima pesan masuk dari Twilio, proses, kirim balik."""
        from_number = request.form.get("From", "").replace("whatsapp:", "")
        body = request.form.get("Body", "").strip()
        sender_name = request.form.get("ProfileName", "").strip() or from_number

        if not body:
            return _twiml_reply("")

        print(f"[{datetime.now():%H:%M:%S}] Dari {sender_name} ({from_number}): {body[:80]}")

        # Cek perintah khusus
        special = handle_special_command(from_number, body)
        if special is not None:
            print(f"  -> Perintah khusus: {special[:60]}")
            return _twiml_reply(special)

        # Chat biasa dengan AI
        session = get_session(from_number)
        skill = session.get("skill")

        # Indikator skill aktif
        skill_info = f" [skill: {skill}]" if skill else ""
        print(f"  -> Memanggil AI{skill_info}...")

        try:
            reply = call_acc_ai(from_number, body, skill)
        except Exception as e:
            reply = f"Maaf, terjadi kesalahan: {e}"

        # Potong jika terlalu panjang (WhatsApp max ~4096 karakter)
        if len(reply) > 3800:
            reply = reply[:3800] + "\n\n_[Respons dipotong. Gunakan /pdf untuk versi lengkap]_"

        print(f"  -> Reply ({len(reply)} char): {reply[:60]}...")
        return _twiml_reply(reply)

    @app.route("/files/<path:filename>", methods=["GET"])
    def serve_file(filename):
        """Serve file output (PDF dll) agar bisa diakses via URL publik."""
        from flask import send_from_directory
        output_dir = ACC_HOME / "data" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        return send_from_directory(str(output_dir), filename)

    @app.route("/status", methods=["GET"])
    def status():
        """Cek status server dan sesi aktif."""
        with _session_lock:
            active = len([s for s in _sessions.values()
                          if s.get("messages")])
        return {
            "status": "ok",
            "active_sessions": active,
            "time": datetime.now().isoformat(),
        }

    return app


def _twiml_reply(text: str) -> Response:
    """Bungkus teks sebagai TwiML response untuk Twilio."""
    if TWIML_OK:
        resp = MessagingResponse()
        if text:
            resp.message(text)
        return Response(str(resp), mimetype="application/xml")
    # Fallback: TwiML manual tanpa library
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{safe}</Message></Response>"""
    return Response(xml, mimetype="application/xml")


# ============ MAIN ============
def main():
    if not FLASK_OK:
        print("[X] Flask belum terpasang. Jalankan: pip install flask")
        sys.exit(1)

    port = int(os.environ.get("ACC_WEBHOOK_PORT", 5000))
    debug = os.environ.get("ACC_DEBUG", "false").lower() == "true"

    print("=" * 55)
    print("  ACC WHATSAPP WEBHOOK SERVER")
    print("  PT. Arunika Teknologi Global")
    print("=" * 55)
    print(f"  Port          : {port}")
    print(f"  Output dir    : {ACC_HOME / 'data' / 'output'}")
    print()
    print("  LANGKAH SELANJUTNYA:")
    print("  1. Buka terminal baru, jalankan: ngrok http 5000")
    print("  2. Copy URL ngrok (https://xxxx.ngrok.io)")
    print("  3. Buka Twilio Console -> Messaging -> Sandbox settings")
    print("  4. Tempel URL + /webhook/whatsapp di field webhook")
    print("     Contoh: https://xxxx.ngrok.io/webhook/whatsapp")
    print("  5. Kirim pesan WhatsApp ke sandbox Twilio")
    print("=" * 55)
    print()

    # Pastikan folder output ada
    (ACC_HOME / "data" / "output").mkdir(parents=True, exist_ok=True)

    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
