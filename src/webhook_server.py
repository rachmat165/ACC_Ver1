#!/usr/bin/env python3
"""
ACC WhatsApp Webhook Server
PT. Arunika Teknologi Global

Alur: WhatsApp -> Twilio -> Webhook (Flask) -> Bot Commands / AI -> WhatsApp

Cara pakai:
  1. python src/webhook_server.py
  2. Terminal baru: ngrok http 5000
  3. Copy URL ngrok -> Twilio Console -> Sandbox settings
     Webhook URL: https://xxxx.ngrok.io/webhook/whatsapp
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# ── Setup path ──────────────────────────────────────────────
ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(ACC_HOME / "src"))

# ── Load env ────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(ACC_HOME / "data" / ".env")
except ImportError:
    pass

# ── Import dependensi opsional ──────────────────────────────
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

# ── Import modul ACC ────────────────────────────────────────
try:
    import acc as _acc
    ACC_OK = True
except ImportError:
    ACC_OK = False

try:
    from user_session import SessionManager
    SESSION_OK = True
except ImportError:
    SESSION_OK = False

try:
    import bot_commands as bot
    BOT_OK = True
except ImportError:
    BOT_OK = False


# ── ANSI color (Windows CMD perlu os.system('') dulu) ───────
os.system("")  # aktifkan ANSI escape di Windows

def _c(text, code): return f"\033[{code}m{text}\033[0m"
def cyan(t):    return _c(t, "96")
def green(t):   return _c(t, "92")
def yellow(t):  return _c(t, "93")
def magenta(t): return _c(t, "95")
def dim(t):     return _c(t, "2")
def bold(t):    return _c(t, "1")
def red(t):     return _c(t, "91")


# ── Globals ─────────────────────────────────────────────────
_session_mgr: SessionManager | None = None
_acc_cfg: dict = {}


def get_session_mgr() -> SessionManager:
    global _session_mgr
    if _session_mgr is None:
        _session_mgr = SessionManager(ACC_HOME / "data")
    return _session_mgr


def get_acc_cfg() -> dict:
    global _acc_cfg
    if not _acc_cfg and ACC_OK:
        try:
            _acc_cfg = _acc.load_config()
        except Exception:
            _acc_cfg = {}
    return _acc_cfg


# ── Terminal logging ─────────────────────────────────────────
BAR = "─" * 54

def log_incoming(ts: str, name: str, phone: str, body: str,
                 model_label: str, skill: str | None):
    skill_txt = f" | Skill: {skill}" if skill else ""
    print(f"\n{dim(BAR)}")
    print(f"{bold(cyan('PESAN MASUK'))}  {dim(ts)}")
    print(f"  {dim('Dari  :')} {bold(name)} {dim(f'({phone})')}")
    print(f"  {dim('Teks  :')} {body[:120]}")
    print(f"  {dim('Model :')} {cyan(model_label)}{dim(skill_txt)}")

def log_command(ts: str, reply: str):
    print(f"{bold(green('PERINTAH'))}  {dim('langsung')}")
    print(f"  {dim('Reply :')} {reply[:80]}")

def log_ai_start(model_label: str):
    print(f"{bold(magenta('AI PROSES'))}  {dim(f'via {model_label} ...')}", flush=True)

def log_ai_done(elapsed: float, length: int, preview: str):
    print(f"{bold(green('SELESAI'))}  {dim(f'{elapsed:.1f}s, {length} char')}")
    print(f"  {dim('Reply :')} {preview[:80]}")

def log_error(msg: str):
    print(f"{bold(red('ERROR'))}  {msg}")


# ── AI engine ────────────────────────────────────────────────
def call_ai(session, user_message: str) -> str:
    """Panggil AI engine dengan model dari sesi user."""
    if not ACC_OK:
        return "[Modul ACC tidak termuat. Periksa src/acc.py]"

    try:
        _acc.load_env()
        cfg = get_acc_cfg()
        sysprompt = _acc.build_system_prompt(session.skill)
        reply = _acc.call_model_multi_turn(
            system_prompt=sysprompt,
            user_message=user_message,
            history=session.history,
            cfg=cfg,
            model_override=session.model_config,
        )
        return reply
    except Exception as e:
        return f"[Error AI: {e}]"


# ── Flask app ────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.route("/", methods=["GET"])
    def index():
        mgr = get_session_mgr()
        return {
            "service": "ACC WhatsApp Webhook Server",
            "company": "PT. Arunika Teknologi Global",
            "status": "running",
            "sessions": mgr.active_count(),
            "time": datetime.now().isoformat(),
        }

    @app.route("/webhook/whatsapp", methods=["POST"])
    def whatsapp_webhook():
        phone = request.form.get("From", "").replace("whatsapp:", "")
        body  = request.form.get("Body", "").strip()
        name  = request.form.get("ProfileName", "").strip() or phone
        ts    = datetime.now().strftime("%H:%M:%S")

        if not body or not phone:
            return _twiml("")

        mgr = get_session_mgr()
        session = mgr.get(phone, name)
        model_label = bot.MODELS.get(session.model_key, {}).get("label", session.model_key) \
                      if BOT_OK else session.model_key

        log_incoming(ts, name, phone, body, model_label, session.skill)

        # ── Bot commands ──────────────────────────────────────
        if BOT_OK:
            # Tangani /pdf <prompt> — body diganti teks setelah /pdf
            is_pdf_prompt = body.strip().lower().startswith("/pdf ")
            if is_pdf_prompt:
                pdf_text = bot.extract_pdf_prompt(body)
                # Proses AI dulu dengan teks pdf_text
                log_ai_start(model_label)
                t0 = time.time()
                ai_reply = call_ai(session, pdf_text)
                elapsed = time.time() - t0
                mgr.add_message(phone, "user", pdf_text)
                mgr.add_message(phone, "assistant", ai_reply)
                # Buat PDF dari respons AI
                session = mgr.get(phone)  # refresh
                pdf_reply = bot.make_pdf(session, ACC_HOME)
                log_ai_done(elapsed, len(ai_reply), ai_reply)
                final = f"{ai_reply[:1000]}\n\n{pdf_reply}" if len(ai_reply) > 0 else pdf_reply
                if len(final) > 3800:
                    final = ai_reply[:2000] + "\n\n...\n\n" + pdf_reply
                return _twiml(final)

            # Perintah biasa
            cmd_reply = bot.handle(phone, name, body, mgr, ACC_HOME)
            if cmd_reply is not None:
                log_command(ts, cmd_reply)
                return _twiml(cmd_reply)

        # ── Chat biasa → AI ───────────────────────────────────
        log_ai_start(model_label)
        t0 = time.time()
        try:
            ai_reply = call_ai(session, body)
        except Exception as e:
            ai_reply = f"Maaf, terjadi kesalahan: {e}"
        elapsed = time.time() - t0

        # Simpan ke riwayat
        mgr.add_message(phone, "user", body)
        mgr.add_message(phone, "assistant", ai_reply)

        # Potong jika terlalu panjang (WA max ~4096)
        MAX = int(os.environ.get("WA_MAX_REPLY", 3800))
        if len(ai_reply) > MAX:
            ai_reply = ai_reply[:MAX] + "\n\n_[Dipotong. Kirim /pdf untuk versi lengkap]_"

        log_ai_done(elapsed, len(ai_reply), ai_reply)
        return _twiml(ai_reply)

    @app.route("/files/<path:filename>", methods=["GET"])
    def serve_file(filename):
        from flask import send_from_directory
        out = ACC_HOME / "data" / "output"
        out.mkdir(parents=True, exist_ok=True)
        return send_from_directory(str(out), filename)

    @app.route("/status", methods=["GET"])
    def status():
        mgr = get_session_mgr()
        return {
            "status": "ok",
            "sessions": mgr.active_count(),
            "users": mgr.all_users(),
            "time": datetime.now().isoformat(),
        }

    return app


def _twiml(text: str) -> Response:
    if TWIML_OK:
        resp = MessagingResponse()
        if text:
            resp.message(text)
        return Response(str(resp), mimetype="application/xml")
    safe = (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>'
    return Response(xml, mimetype="application/xml")


# ── Startup ──────────────────────────────────────────────────
def _progress(label: str, pct: int, width: int = 38):
    filled = int(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    print(f"\r  {cyan(bar)} {pct:3d}%  {dim(label)}", end="", flush=True)
    if pct >= 100:
        print()


def main():
    if not FLASK_OK:
        print(f"  {yellow('[!]')} Flask belum terpasang. Jalankan: pip install flask")
        sys.exit(1)

    port  = int(os.environ.get("ACC_WEBHOOK_PORT", 5000))
    debug = os.environ.get("ACC_DEBUG", "false").lower() == "true"

    print()
    print(f"  {bold(cyan('╔══════════════════════════════════════════════════╗'))}")
    print(f"  {bold(cyan('║   ACC WHATSAPP WEBHOOK SERVER                    ║'))}")
    print(f"  {bold(cyan('║   PT. Arunika Teknologi Global                   ║'))}")
    print(f"  {bold(cyan('╚══════════════════════════════════════════════════╝'))}")
    print()

    steps = [
        ("Memuat konfigurasi .env ...", 0.05),
        ("Inisialisasi session manager ...", 0.1),
        ("Memuat modul ACC ...", 0.1),
        ("Memuat bot commands ...", 0.05),
        ("Menyiapkan folder output ...", 0.05),
        ("Flask app siap ...", 0.05),
    ]
    for i, (label, delay) in enumerate(steps):
        pct = int((i + 1) / len(steps) * 100)
        _progress(label, pct)
        time.sleep(delay)

    # Init
    _acc.load_env() if ACC_OK else None
    get_acc_cfg()
    get_session_mgr()
    (ACC_HOME / "data" / "output").mkdir(parents=True, exist_ok=True)

    print()
    print(f"  {green('●')} Port        : {bold(str(port))}")
    print(f"  {green('●')} Sessions    : {dim(str(ACC_HOME / 'data' / 'sessions' / 'users.json'))}")
    print(f"  {green('●')} Output PDF  : {dim(str(ACC_HOME / 'data' / 'output'))}")
    print(f"  {green('●')} ACC module  : {green('OK') if ACC_OK else yellow('GAGAL')}")
    print(f"  {green('●')} Bot commands: {green('OK') if BOT_OK else yellow('GAGAL')}")
    print(f"  {green('●')} TwiML       : {green('OK') if TWIML_OK else yellow('fallback XML')}")
    print()
    print(f"  {dim('┌─ CARA CONNECT KE WHATSAPP ─────────────────────────┐')}")
    print(f"  {dim('│')} 1. Terminal baru: {cyan('ngrok http ' + str(port))}              {dim('│')}")
    print(f"  {dim('│')} 2. Copy URL: https://xxxx.ngrok.io               {dim('│')}")
    print(f"  {dim('│')} 3. Twilio Console -> Sandbox settings:           {dim('│')}")
    print(f"  {dim('│')}    {cyan('https://xxxx.ngrok.io/webhook/whatsapp')}      {dim('│')}")
    print(f"  {dim('│')} 4. Kirim /menu ke nomor sandbox Twilio           {dim('│')}")
    print(f"  {dim('└────────────────────────────────────────────────────┘')}")
    print()
    print(f"  {dim('Menunggu pesan... Ctrl+C untuk berhenti')}")
    print(f"  {dim(BAR)}\n")

    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    main()
