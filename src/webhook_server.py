#!/usr/bin/env python3
"""
ACC WhatsApp Webhook Server
PT. Arunika Teknologi Global

Alur:
  WhatsApp -> Twilio -> Webhook (Flask)
    -> Langsung balas "Memproses..." ke WhatsApp
    -> Background thread: panggil AI
    -> Kirim hasil AI via Twilio API
"""
import os
import sys
import time
import logging
import threading
from pathlib import Path
from datetime import datetime

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
    from twilio.rest import Client as TwilioClient
    TWIML_OK = True
except ImportError:
    TWIML_OK = False

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

# ── ANSI ──────────────────────────────────────────────────────
os.system("")
def _c(t, code): return f"\033[{code}m{t}\033[0m"
def cyan(t):    return _c(t, "96")
def green(t):   return _c(t, "92")
def yellow(t):  return _c(t, "93")
def magenta(t): return _c(t, "95")
def dim(t):     return _c(t, "2")
def bold(t):    return _c(t, "1")
def red(t):     return _c(t, "91")

# ── Globals ───────────────────────────────────────────────────
_session_mgr = None
_acc_cfg     = {}
BAR          = "─" * 54

def get_session_mgr():
    global _session_mgr
    if _session_mgr is None:
        _session_mgr = SessionManager(ACC_HOME / "data")
    return _session_mgr

def get_acc_cfg():
    global _acc_cfg
    if not _acc_cfg and ACC_OK:
        try: _acc_cfg = _acc.load_config()
        except: pass
    return _acc_cfg


# ── Terminal spinner saat AI memproses ───────────────────────
class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, label: str):
        self.label   = label
        self._stop   = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._t0     = time.time()

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            elapsed = time.time() - self._t0
            frame   = self.FRAMES[i % len(self.FRAMES)]
            print(f"\r  {magenta(frame)}  {self.label}  {dim(f'{elapsed:.1f}s')}   ",
                  end="", flush=True)
            i += 1
            time.sleep(0.1)

    def start(self):
        self._thread.start()
        return self

    def stop(self, suffix: str = ""):
        self._stop.set()
        self._thread.join()
        elapsed = time.time() - self._t0
        print(f"\r  {green('✔')}  {self.label}  {dim(f'{elapsed:.1f}s')} {suffix}   ")


# ── Kirim pesan via Twilio API (untuk background reply) ───────
def send_whatsapp(to: str, body: str):
    """Kirim pesan balik via Twilio REST API (bukan TwiML)."""
    try:
        sid   = os.environ.get("TWILIO_ACCOUNT_SID", "")
        token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        from_ = os.environ.get("WA_FROM_NUMBER", "+14155238886")
        if not sid or not token:
            print(f"  {yellow('[!]')} TWILIO_ACCOUNT_SID/AUTH_TOKEN kosong di .env")
            return False
        client = TwilioClient(sid, token)
        to_wa  = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
        from_wa = f"whatsapp:{from_}" if not from_.startswith("whatsapp:") else from_
        client.messages.create(from_=from_wa, body=body, to=to_wa)
        return True
    except Exception as e:
        print(f"  {red('[!]')} Gagal kirim via Twilio API: {e}")
        return False


# ── AI engine ─────────────────────────────────────────────────
def call_ai(session, user_message: str) -> str:
    if not ACC_OK:
        return "[Modul ACC tidak termuat]"
    try:
        _acc.load_env()
        cfg      = get_acc_cfg()
        sysprompt = _acc.build_system_prompt(session.skill)
        return _acc.call_model_multi_turn(
            system_prompt  = sysprompt,
            user_message   = user_message,
            history        = session.history,
            cfg            = cfg,
            model_override = session.model_config,
        )
    except Exception as e:
        return f"Maaf, terjadi kesalahan: {e}"


# ── Log terminal ──────────────────────────────────────────────
def log_incoming(ts, name, phone, body, model_label, skill):
    skill_txt = f" | Skill: {skill}" if skill else ""
    print(f"\n{dim(BAR)}")
    print(f"{bold(cyan('PESAN MASUK'))}  {dim(ts)}")
    print(f"  {dim('Dari  :')} {bold(name)} {dim(f'({phone})')}")
    print(f"  {dim('Teks  :')} {body[:120]}")
    print(f"  {dim('Model :')} {cyan(model_label)}{dim(skill_txt)}")

def log_cmd(reply):
    print(f"  {green('✔')} {dim('Perintah:')} {reply[:80]}")

def log_sent(length):
    print(f"  {green('✔')} {dim('Terkirim:')} {length} karakter")


# ── Background AI worker ──────────────────────────────────────
def ai_worker(phone: str, name: str, body: str, session_mgr):
    """Jalankan AI di background, kirim hasil via Twilio API."""
    session     = session_mgr.get(phone, name)
    model_label = bot.MODELS.get(session.model_key, {}).get("label", session.model_key) \
                  if BOT_OK else session.model_key

    sp = Spinner(f"AI memproses ({model_label})").start()
    try:
        ai_reply = call_ai(session, body)
    except Exception as e:
        ai_reply = f"Maaf, terjadi kesalahan: {e}"
    sp.stop(f"→ {len(ai_reply)} char")

    # Simpan ke riwayat
    session_mgr.add_message(phone, "user", body)
    session_mgr.add_message(phone, "assistant", ai_reply)

    # Potong jika terlalu panjang
    MAX = 3800
    if len(ai_reply) > MAX:
        ai_reply = ai_reply[:MAX] + "\n\n_[Dipotong. Kirim /pdf untuk versi lengkap]_"

    # Kirim hasil ke WhatsApp via Twilio API
    ok = send_whatsapp(phone, ai_reply)
    log_sent(len(ai_reply)) if ok else None


def ai_worker_pdf(phone: str, name: str, pdf_prompt: str, session_mgr):
    """Generate AI + PDF, kirim link PDF ke WhatsApp."""
    session     = session_mgr.get(phone, name)
    model_label = bot.MODELS.get(session.model_key, {}).get("label", session.model_key) \
                  if BOT_OK else session.model_key

    sp = Spinner(f"AI generate PDF ({model_label})").start()
    try:
        ai_reply = call_ai(session, pdf_prompt)
    except Exception as e:
        ai_reply = f"Gagal generate konten: {e}"
    sp.stop()

    session_mgr.add_message(phone, "user", pdf_prompt)
    session_mgr.add_message(phone, "assistant", ai_reply)

    # Buat PDF
    session = session_mgr.get(phone)
    if BOT_OK:
        pdf_reply = bot.make_pdf(session, ACC_HOME)
    else:
        pdf_reply = "_PDF tidak tersedia_"

    result = f"{ai_reply[:1500]}\n\n{pdf_reply}" if len(ai_reply) > 0 else pdf_reply
    if len(result) > 3800:
        result = ai_reply[:2000] + "\n\n...\n\n" + pdf_reply

    send_whatsapp(phone, result)
    log_sent(len(result))


# ── Flask app ─────────────────────────────────────────────────
def create_app():
    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.route("/", methods=["GET"])
    def index():
        mgr = get_session_mgr()
        return {"service": "ACC Webhook", "status": "ok",
                "sessions": mgr.active_count(),
                "time": datetime.now().isoformat()}

    @app.route("/webhook/whatsapp", methods=["POST"])
    def whatsapp_webhook():
        phone = request.form.get("From", "").replace("whatsapp:", "")
        body  = request.form.get("Body", "").strip()
        name  = request.form.get("ProfileName", "").strip() or phone
        ts    = datetime.now().strftime("%H:%M:%S")

        if not body or not phone:
            return _twiml("")

        mgr     = get_session_mgr()
        session = mgr.get(phone, name)
        model_label = bot.MODELS.get(session.model_key, {}).get("label", session.model_key) \
                      if BOT_OK else session.model_key

        log_incoming(ts, name, phone, body, model_label, session.skill)

        # ── Bot commands (langsung, tanpa AI) ──────────────────
        if BOT_OK:
            is_pdf_prompt = body.strip().lower().startswith("/pdf ")
            if is_pdf_prompt:
                pdf_prompt = bot.extract_pdf_prompt(body)
                ack = f"⏳ *Membuat PDF...*\n\nTopik: _{pdf_prompt[:80]}_\nHarap tunggu sebentar."
                threading.Thread(
                    target=ai_worker_pdf,
                    args=(phone, name, pdf_prompt, mgr),
                    daemon=True
                ).start()
                log_cmd(ack)
                return _twiml(ack)

            cmd_reply = bot.handle(phone, name, body, mgr, ACC_HOME)
            if cmd_reply is not None:
                log_cmd(cmd_reply)
                return _twiml(cmd_reply)

        # ── Chat biasa: panggil AI secara SINKRON ──────────────
        # Twilio timeout = 15 detik. Claude Haiku biasanya < 10 detik.
        sp = Spinner(f"AI ({model_label})").start()
        t0 = time.time()
        try:
            ai_reply = call_ai(session, body)
        except Exception as e:
            ai_reply = f"Maaf, terjadi kesalahan: {e}"
        elapsed = time.time() - t0
        sp.stop(f"→ {len(ai_reply)} char")

        # Simpan riwayat
        mgr.add_message(phone, "user", body)
        mgr.add_message(phone, "assistant", ai_reply)

        # Potong jika terlalu panjang
        MAX = 3800
        if len(ai_reply) > MAX:
            ai_reply = ai_reply[:MAX] + "\n\n_[Dipotong. Kirim /pdf untuk versi lengkap]_"

        log_sent(len(ai_reply))
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
        return {"status": "ok", "sessions": mgr.active_count(),
                "users": mgr.all_users(), "time": datetime.now().isoformat()}

    return app


def _twiml(text: str) -> Response:
    if TWIML_OK:
        resp = MessagingResponse()
        if text:
            resp.message(text)
        return Response(str(resp), mimetype="application/xml")
    safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Message>{safe}</Message></Response>',
        mimetype="application/xml"
    )


# ── Startup ───────────────────────────────────────────────────
def _pbar(label, pct, w=38):
    filled = int(pct/100*w)
    bar = "█"*filled + "░"*(w-filled)
    print(f"\r  {cyan(bar)} {pct:3d}%  {dim(label)}", end="", flush=True)
    if pct >= 100: print()

def main():
    if not FLASK_OK:
        print("  Flask belum terpasang: pip install flask"); sys.exit(1)

    port  = int(os.environ.get("ACC_WEBHOOK_PORT", 5000))
    debug = os.environ.get("ACC_DEBUG","false").lower() == "true"

    print()
    print(f"  {bold(cyan('╔══════════════════════════════════════════════════╗'))}")
    print(f"  {bold(cyan('║   ACC WHATSAPP WEBHOOK SERVER                    ║'))}")
    print(f"  {bold(cyan('║   PT. Arunika Teknologi Global                   ║'))}")
    print(f"  {bold(cyan('╚══════════════════════════════════════════════════╝'))}")
    print()

    steps = [
        ("Memuat konfigurasi .env",      0.05),
        ("Inisialisasi session manager", 0.10),
        ("Memuat modul ACC",             0.10),
        ("Memuat bot commands",          0.05),
        ("Menyiapkan folder output",     0.05),
        ("Flask app siap",               0.05),
    ]
    for i, (label, delay) in enumerate(steps):
        _pbar(label + " ...", int((i+1)/len(steps)*100))
        time.sleep(delay)

    _acc.load_env() if ACC_OK else None
    get_acc_cfg()
    get_session_mgr()
    (ACC_HOME/"data"/"output").mkdir(parents=True, exist_ok=True)

    print()
    print(f"  {green('●')} Port        : {bold(str(port))}")
    print(f"  {green('●')} Sessions    : {dim(str(ACC_HOME/'data'/'sessions'/'users.json'))}")
    print(f"  {green('●')} Output PDF  : {dim(str(ACC_HOME/'data'/'output'))}")
    print(f"  {green('●')} ACC module  : {green('OK') if ACC_OK else red('GAGAL')}")
    print(f"  {green('●')} Bot commands: {green('OK') if BOT_OK else red('GAGAL')}")
    print(f"  {green('●')} TwiML       : {green('OK') if TWIML_OK else yellow('fallback')}")
    print(f"  {green('●')} Mode reply  : {cyan('ASYNC')} {dim('(langsung balas + AI di background)')}")
    print()
    print(f"  {dim('Menunggu pesan... Ctrl+C untuk berhenti')}")
    print(f"  {dim(BAR)}\n")

    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)

if __name__ == "__main__":
    main()
