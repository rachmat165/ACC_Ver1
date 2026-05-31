#!/usr/bin/env python3
"""
ACC WhatsApp Webhook Server - PT. Arunika Teknologi Global
Alur:
  1. Terima pesan WhatsApp dari Twilio (webhook POST)
  2. Bot commands → balas langsung via TwiML
  3. Query AI → balas KOSONG ke Twilio (<1 detik, hindari timeout 15s)
              → AI proses di background thread
              → Kirim hasil via Twilio REST API
"""
import os, sys, time, logging, threading, traceback
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
except ImportError:
    pass

try:
    import bot_commands as bot
    BOT_OK = True
except ImportError:
    BOT_OK = False

# ── ANSI ─────────────────────────────────────────────────────
os.system("")
def _c(t,c): return f"\033[{c}m{t}\033[0m"
def cyan(t):    return _c(t,"96")
def green(t):   return _c(t,"92")
def yellow(t):  return _c(t,"93")
def magenta(t): return _c(t,"95")
def dim(t):     return _c(t,"2")
def bold(t):    return _c(t,"1")
def red(t):     return _c(t,"91")

BAR = "─"*54
_session_mgr = None
_acc_cfg     = {}

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

# ── Spinner terminal ──────────────────────────────────────────
class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    def __init__(self, label):
        self.label = label
        self._stop = threading.Event()
        self._t    = threading.Thread(target=self._run, daemon=True)
        self._t0   = time.time()
    def _run(self):
        i = 0
        while not self._stop.is_set():
            e = time.time()-self._t0
            f = self.FRAMES[i % len(self.FRAMES)]
            print(f"\r  {magenta(f)}  {self.label}  {dim(f'{e:.1f}s')}   ", end="", flush=True)
            i += 1; time.sleep(0.1)
    def start(self):
        self._t.start(); return self
    def stop(self, suffix=""):
        self._stop.set(); self._t.join()
        e = time.time()-self._t0
        print(f"\r  {green('✔')}  {self.label}  {dim(f'{e:.1f}s')} {suffix}   ")

# ── Log ───────────────────────────────────────────────────────
def log_in(ts, name, phone, body, model, skill):
    s = f" | Skill: {skill}" if skill else ""
    print(f"\n{dim(BAR)}")
    print(f"{bold(cyan('PESAN MASUK'))}  {dim(ts)}")
    print(f"  {dim('Dari  :')} {bold(name)} {dim(f'({phone})')}")
    print(f"  {dim('Teks  :')} {body[:120]}")
    print(f"  {dim('Model :')} {cyan(model)}{dim(s)}")

def log_cmd(r): print(f"  {green('✔')} {dim('Perintah:')} {r[:80]}")

def log_err(msg):
    print(f"\n  {bold(red('ERROR'))} {msg}")

# ── Pecah pesan panjang jadi beberapa bagian (<1500 char) ────
WA_CHUNK = 1500   # aman di bawah batas Twilio 1600

def split_message(text: str, limit: int = WA_CHUNK) -> list[str]:
    """Pecah teks panjang di batas paragraf/kalimat agar rapi."""
    if len(text) <= limit:
        return [text]

    chunks, current = [], ""
    for para in text.split("\n"):
        # Paragraf sendiri lebih panjang dari limit → pecah per kalimat
        if len(para) > limit:
            for sentence in para.replace(". ", ".\n").split("\n"):
                if len(current) + len(sentence) + 1 > limit:
                    if current: chunks.append(current.strip())
                    current = sentence
                else:
                    current += ("\n" if current else "") + sentence
        else:
            if len(current) + len(para) + 1 > limit:
                chunks.append(current.strip())
                current = para
            else:
                current += ("\n" if current else "") + para
    if current.strip():
        chunks.append(current.strip())

    # Tambah penanda bagian (1/3) dst.
    total = len(chunks)
    if total > 1:
        chunks = [f"*[{i+1}/{total}]*\n{c}" for i, c in enumerate(chunks)]
    return chunks


# ── Kirim via Twilio REST API ─────────────────────────────────
def send_wa(to: str, body: str) -> bool:
    """Kirim pesan WhatsApp via Twilio REST API. Otomatis pecah jika panjang."""
    try:
        sid   = os.environ.get("TWILIO_ACCOUNT_SID","").strip()
        token = os.environ.get("TWILIO_AUTH_TOKEN","").strip()
        from_ = os.environ.get("WA_FROM_NUMBER","+14155238886").strip()

        if not sid or not token:
            log_err("TWILIO_ACCOUNT_SID atau TWILIO_AUTH_TOKEN kosong di data/.env!")
            return False
        if not sid.startswith("AC"):
            log_err(f"TWILIO_ACCOUNT_SID tidak valid (harus mulai 'AC'): {sid[:10]}")
            return False

        to_wa   = f"whatsapp:{to}"    if not to.startswith("whatsapp:")    else to
        from_wa = f"whatsapp:{from_}" if not from_.startswith("whatsapp:") else from_

        client = TwilioClient(sid, token)
        parts  = split_message(body)
        print(f"  {dim('To    :')} {to}  {dim(f'({len(parts)} bagian, {len(body)} char)')}")

        for idx, part in enumerate(parts):
            msg = client.messages.create(from_=from_wa, body=part, to=to_wa)
            print(f"  {green('✔')} Bagian {idx+1}/{len(parts)} terkirim — SID: {msg.sid[:12]}...")
            # Jeda antar pesan agar urutan terjaga di WhatsApp
            if idx < len(parts) - 1:
                time.sleep(1.2)
        return True

    except Exception as e:
        log_err(f"REST API gagal: {e}")
        traceback.print_exc()
        return False

# ── AI engine ─────────────────────────────────────────────────
def call_ai(session, msg: str) -> str:
    if not ACC_OK:
        return "[Modul ACC tidak termuat. Periksa src/acc.py]"
    try:
        _acc.load_env()
        return _acc.call_model_multi_turn(
            system_prompt  = _acc.build_system_prompt(session.skill),
            user_message   = msg,
            history        = session.history,
            cfg            = get_acc_cfg(),
            model_override = session.model_config,
        )
    except Exception as e:
        return f"Maaf, terjadi kesalahan internal: {e}"

# ── Background worker ─────────────────────────────────────────
def ai_worker(phone: str, name: str, body: str, mgr):
    """Proses AI di background, kirim hasil via REST API."""
    try:
        session = mgr.get(phone, name)
        model   = bot.MODELS.get(session.model_key,{}).get("label", session.model_key) \
                  if BOT_OK else session.model_key

        sp = Spinner(f"AI ({model})").start()
        reply = call_ai(session, body)
        sp.stop(f"→ {len(reply)} char")

        mgr.add_message(phone, "user",      body)
        mgr.add_message(phone, "assistant", reply)

        # Jawaban sangat panjang → tawarkan PDF (hemat pesan WA)
        if len(reply) > 6000:
            reply += ("\n\n💡 _Jawaban panjang. Kirim /pdf untuk versi PDF rapi "
                      "yang bisa diunduh._")

        print(f"  {dim('Mengirim hasil via REST API...')}")
        send_wa(phone, reply)

    except Exception as e:
        log_err(f"ai_worker crash: {e}")
        traceback.print_exc()
        try:
            send_wa(phone, f"Maaf, terjadi kesalahan: {e}")
        except: pass

def ai_worker_pdf(phone: str, name: str, prompt: str, mgr):
    try:
        session = mgr.get(phone, name)
        model   = bot.MODELS.get(session.model_key,{}).get("label", session.model_key) \
                  if BOT_OK else session.model_key
        sp = Spinner(f"AI PDF ({model})").start()
        ai_reply = call_ai(session, prompt)
        sp.stop()
        mgr.add_message(phone, "user",      prompt)
        mgr.add_message(phone, "assistant", ai_reply)
        session = mgr.get(phone)
        pdf_msg = bot.make_pdf(session, ACC_HOME) if BOT_OK else "_PDF tidak tersedia_"
        result  = f"{ai_reply[:2000]}\n\n{pdf_msg}" if ai_reply else pdf_msg
        send_wa(phone, result[:3800])
    except Exception as e:
        log_err(f"ai_worker_pdf crash: {e}")
        traceback.print_exc()

# ── TwiML helper ─────────────────────────────────────────────
def _twiml(text: str = "") -> Response:
    if TWIML_OK:
        resp = MessagingResponse()
        if text:
            resp.message(text)
        return Response(str(resp), mimetype="application/xml")
    safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    body = f"<Message>{safe}</Message>" if text else ""
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>',
        mimetype="application/xml"
    )

# ── Flask app ─────────────────────────────────────────────────
def create_app():
    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.route("/", methods=["GET"])
    def index():
        return {"service":"ACC Webhook","status":"ok",
                "sessions": get_session_mgr().active_count(),
                "time": datetime.now().isoformat()}

    @app.route("/webhook/whatsapp", methods=["POST"])
    def whatsapp_webhook():
        phone = request.form.get("From","").replace("whatsapp:","")
        body  = request.form.get("Body","").strip()
        name  = request.form.get("ProfileName","").strip() or phone
        ts    = datetime.now().strftime("%H:%M:%S")

        if not body or not phone:
            return _twiml()

        mgr     = get_session_mgr()
        session = mgr.get(phone, name)
        model   = bot.MODELS.get(session.model_key,{}).get("label", session.model_key) \
                  if BOT_OK else session.model_key

        log_in(ts, name, phone, body, model, session.skill)

        # ── Bot commands → langsung TwiML ──────────────────────
        if BOT_OK:
            if body.strip().lower().startswith("/pdf "):
                prompt = bot.extract_pdf_prompt(body)
                threading.Thread(target=ai_worker_pdf,
                                 args=(phone, name, prompt, mgr),
                                 daemon=True).start()
                ack = f"⏳ *Membuat PDF...*\nTopik: _{prompt[:60]}_\nSedang diproses..."
                log_cmd(ack)
                return _twiml(ack)

            cmd = bot.handle(phone, name, body, mgr, ACC_HOME)
            if cmd is not None:
                log_cmd(cmd)
                return _twiml(cmd)

        # ── Query AI → balas "Memproses" dulu, AI di background ──
        print(f"  {dim('→ Background AI thread dimulai...')}")
        threading.Thread(target=ai_worker,
                         args=(phone, name, body, mgr),
                         daemon=True).start()

        skill_txt = f"\nSkill: _{session.skill}_" if session.skill else ""
        ack = (f"⏳ *Sedang memproses...*\n"
               f"🧠 {model}{skill_txt}\n\n"
               f"_Mohon tunggu, jawaban menyusul dalam beberapa detik..._")
        log_cmd("[ACK] Memproses...")
        # Pesan ini muncul cepat (<1s), jawaban lengkap menyusul via REST API
        return _twiml(ack)

    @app.route("/files/<path:fn>", methods=["GET"])
    def serve_file(fn):
        from flask import send_from_directory
        out = ACC_HOME/"data"/"output"
        out.mkdir(parents=True, exist_ok=True)
        return send_from_directory(str(out), fn)

    @app.route("/status", methods=["GET"])
    def status():
        mgr = get_session_mgr()
        return {"status":"ok","sessions":mgr.active_count(),
                "users":mgr.all_users(),"time":datetime.now().isoformat()}

    return app

# ── Startup ───────────────────────────────────────────────────
def _pbar(label, pct, w=38):
    f = int(pct/100*w)
    bar = "█"*f + "░"*(w-f)
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

    for i,(label,delay) in enumerate([
        ("Memuat .env",          0.05),
        ("Session manager",      0.10),
        ("Modul ACC",            0.10),
        ("Bot commands",         0.05),
        ("Folder output",        0.05),
        ("Flask siap",           0.05),
    ]):
        _pbar(label+" ...", int((i+1)/6*100)); time.sleep(delay)

    if ACC_OK: _acc.load_env()
    get_acc_cfg(); get_session_mgr()
    (ACC_HOME/"data"/"output").mkdir(parents=True, exist_ok=True)

    # Tampilkan credential check
    sid   = os.environ.get("TWILIO_ACCOUNT_SID","")
    token = os.environ.get("TWILIO_AUTH_TOKEN","")
    print()
    print(f"  {green('●')} Port     : {bold(str(port))}")
    print(f"  {green('●')} ACC      : {green('OK') if ACC_OK   else red('GAGAL')}")
    print(f"  {green('●')} Bot      : {green('OK') if BOT_OK   else red('GAGAL')}")
    print(f"  {green('●')} TwiML    : {green('OK') if TWIML_OK else red('GAGAL')}")
    print(f"  {green('●')} Twilio   : SID={cyan(sid[:10]+'...' if sid else 'KOSONG!')}  "
          f"Token={'OK' if token else red('KOSONG!')}")
    print(f"  {green('●')} Mode     : {cyan('ASYNC')} {dim('(kosong → AI background → REST API)')}")
    print()
    print(f"  {dim(BAR)}")
    print(f"  {dim('Menunggu pesan WhatsApp... Ctrl+C untuk berhenti')}")
    print(f"  {dim(BAR)}\n")

    create_app().run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)

if __name__ == "__main__":
    main()
