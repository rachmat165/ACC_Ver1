#!/usr/bin/env python3
"""
WhatsApp Handler untuk Arunika Command Centre.
Support Twilio Sandbox & Production, dengan mode freeform & template.

Mode pesan:
  - FREEFORM: untuk reply dalam 24 jam setelah user kirim pesan
  - TEMPLATE: untuk inisiasi/notification, butuh content_sid yang sudah approved Meta

Cara pakai dari CLI:
  python src/whatsapp_handler.py send "+628112342165" "Halo, ini Arunika"
  python src/whatsapp_handler.py template "+628112342165" HXxxxx '{"1":"12/1","2":"3pm"}'
  python src/whatsapp_handler.py test

Cara pakai dari kode:
  from whatsapp_handler import send_message, send_template
  send_message("+628112342165", "Halo")
"""
import os
import sys
import json
from pathlib import Path

ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(ACC_HOME / "data" / ".env")
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


# ============ KONFIG ============
def get_config():
    """Ambil konfigurasi Twilio dari .env."""
    return {
        "provider": os.environ.get("WA_PROVIDER", "twilio").lower(),
        "account_sid": os.environ.get("TWILIO_ACCOUNT_SID", "").strip(),
        "auth_token": os.environ.get("TWILIO_AUTH_TOKEN", "").strip(),
        "from_number": os.environ.get("WA_FROM_NUMBER", "+14155238886").strip(),
        "default_template_sid": os.environ.get("WA_DEFAULT_TEMPLATE_SID", "").strip(),
        "sandbox": os.environ.get("WA_SANDBOX_MODE", "true").lower() == "true",
    }


def validate_config(cfg):
    """Cek konfigurasi lengkap. Return (ok, list_of_errors)."""
    errors = []
    if cfg["provider"] != "twilio":
        errors.append(f"Provider '{cfg['provider']}' belum didukung handler ini.")
    if not cfg["account_sid"]:
        errors.append("TWILIO_ACCOUNT_SID kosong di data/.env")
    elif not cfg["account_sid"].startswith("AC"):
        errors.append("TWILIO_ACCOUNT_SID tidak valid (harus diawali 'AC').")
    if not cfg["auth_token"]:
        errors.append("TWILIO_AUTH_TOKEN kosong di data/.env")
    if not cfg["from_number"]:
        errors.append("WA_FROM_NUMBER kosong di data/.env")
    return (len(errors) == 0, errors)


# ============ NORMALISASI NOMOR ============
def normalize_phone(num):
    """Normalisasi nomor ke format E.164 dengan prefix whatsapp:."""
    if not num:
        return None
    s = str(num).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if s.startswith("whatsapp:"):
        return s
    # 08xxx -> +628xxx (Indonesia)
    if s.startswith("0"):
        s = "+62" + s[1:]
    elif s.startswith("62") and not s.startswith("+"):
        s = "+" + s
    elif not s.startswith("+"):
        s = "+" + s
    return f"whatsapp:{s}"


# ============ KIRIM PESAN ============
def send_message(to, body, cfg=None):
    """Kirim pesan freeform (24-jam window).
    
    Returns: (success: bool, info: dict)
    """
    cfg = cfg or get_config()
    ok, errors = validate_config(cfg)
    if not ok:
        return False, {"error": "; ".join(errors)}
    
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException
    except ImportError:
        return False, {"error": "Paket 'twilio' belum terpasang. Jalankan: pip install twilio"}
    
    to_n = normalize_phone(to)
    from_n = cfg["from_number"]
    if not from_n.startswith("whatsapp:"):
        from_n = f"whatsapp:{from_n}"
    
    try:
        client = Client(cfg["account_sid"], cfg["auth_token"])
        msg = client.messages.create(from_=from_n, body=body, to=to_n)
        return True, {
            "sid": msg.sid,
            "to": to_n,
            "from": from_n,
            "status": msg.status,
        }
    except TwilioRestException as e:
        return False, {
            "error": f"Twilio error {e.code}: {e.msg}",
            "more_info": getattr(e, "more_info", ""),
        }
    except Exception as e:
        return False, {"error": str(e)}


def send_template(to, content_sid, variables=None, cfg=None):
    """Kirim pesan TEMPLATE (untuk inisiasi/notification).
    
    Args:
        to: nomor tujuan
        content_sid: SID template yg sudah approved (mis. HXb5b62...)
        variables: dict {"1": "value1", "2": "value2"} untuk isi placeholder
    """
    cfg = cfg or get_config()
    ok, errors = validate_config(cfg)
    if not ok:
        return False, {"error": "; ".join(errors)}
    
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException
    except ImportError:
        return False, {"error": "Paket 'twilio' belum terpasang."}
    
    to_n = normalize_phone(to)
    from_n = cfg["from_number"]
    if not from_n.startswith("whatsapp:"):
        from_n = f"whatsapp:{from_n}"
    
    payload = {"from_": from_n, "to": to_n, "content_sid": content_sid}
    if variables:
        if isinstance(variables, dict):
            payload["content_variables"] = json.dumps(variables)
        else:
            payload["content_variables"] = str(variables)
    
    try:
        client = Client(cfg["account_sid"], cfg["auth_token"])
        msg = client.messages.create(**payload)
        return True, {
            "sid": msg.sid,
            "to": to_n,
            "template": content_sid,
            "status": msg.status,
        }
    except TwilioRestException as e:
        return False, {
            "error": f"Twilio error {e.code}: {e.msg}",
            "hint": _twilio_error_hint(e.code),
        }
    except Exception as e:
        return False, {"error": str(e)}


def _twilio_error_hint(code):
    """Saran berdasarkan error code Twilio."""
    hints = {
        63016: "Nomor penerima belum 'join sandbox'. Suruh dia kirim 'join <kode>' ke +14155238886 lebih dulu.",
        63007: "Template tidak ditemukan / belum di-approve Meta.",
        63018: "Nomor pengirim WhatsApp belum aktif/terverifikasi.",
        21211: "Format nomor tujuan tidak valid (harus +<kode_negara><nomor>).",
        20003: "Auth Token salah. Cek TWILIO_AUTH_TOKEN di .env.",
    }
    return hints.get(code, "Cek dokumentasi: https://www.twilio.com/docs/api/errors/" + str(code))


# ============ WEBHOOK RECEIVER ============
def parse_incoming(form_data):
    """Parse webhook form data dari Twilio jadi dict yang berguna.
    
    Twilio webhook POST kirim x-www-form-urlencoded dengan field:
      From, To, Body, ProfileName, MessageSid, NumMedia, MediaUrl0..N
    """
    return {
        "from": form_data.get("From", "").replace("whatsapp:", ""),
        "to": form_data.get("To", "").replace("whatsapp:", ""),
        "body": form_data.get("Body", "").strip(),
        "sender_name": form_data.get("ProfileName", "").strip(),
        "message_sid": form_data.get("MessageSid", ""),
        "num_media": int(form_data.get("NumMedia", 0) or 0),
        "media_urls": [form_data.get(f"MediaUrl{i}", "") 
                       for i in range(int(form_data.get("NumMedia", 0) or 0))],
    }


# ============ CLI ============
def cli_send(args):
    if len(args) < 2:
        print('Pemakaian: send "<nomor>" "<pesan>"')
        return
    to, body = args[0], args[1]
    if RICH:
        with console.status(f"[cyan]Mengirim ke {to}...[/cyan]"):
            ok, info = send_message(to, body)
    else:
        print(f"Mengirim ke {to}...")
        ok, info = send_message(to, body)
    _print_result(ok, info)


def cli_template(args):
    if len(args) < 2:
        print('Pemakaian: template "<nomor>" "<content_sid>" [variables_json]')
        return
    to, sid = args[0], args[1]
    variables = json.loads(args[2]) if len(args) >= 3 else None
    if RICH:
        with console.status(f"[cyan]Mengirim template ke {to}...[/cyan]"):
            ok, info = send_template(to, sid, variables)
    else:
        print(f"Mengirim template ke {to}...")
        ok, info = send_template(to, sid, variables)
    _print_result(ok, info)


def cli_test():
    """Test konfigurasi Twilio tanpa mengirim pesan."""
    cfg = get_config()
    if RICH:
        t = Table(show_header=False, border_style="dim")
        t.add_column("k", style="dim"); t.add_column("v")
        for k, v in cfg.items():
            disp = v if k != "auth_token" else (v[:6] + "..." if v else "[red](kosong)[/red]")
            t.add_row(str(k), str(disp) if disp else "[red](kosong)[/red]")
        console.print(Panel(t, title="[bold]Konfigurasi WhatsApp[/bold]",
                            border_style="cyan"))
    else:
        print("Konfigurasi:")
        for k, v in cfg.items():
            disp = v if k != "auth_token" else (v[:6] + "..." if v else "(kosong)")
            print(f"  {k}: {disp}")
    
    ok, errors = validate_config(cfg)
    if not ok:
        msg = "Konfigurasi tidak lengkap:\n" + "\n".join("  - " + e for e in errors)
        if RICH:
            console.print(Panel(msg, title="[red]Belum Siap[/red]", border_style="red"))
        else:
            print("\n" + msg)
        return
    
    # Ping API Twilio (verifikasi credential)
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException
    except ImportError:
        print("\n[X] Paket 'twilio' belum terpasang. Jalankan: pip install twilio")
        return
    
    try:
        if RICH:
            with console.status("[cyan]Memeriksa kredensial Twilio...[/cyan]"):
                client = Client(cfg["account_sid"], cfg["auth_token"])
                acc = client.api.accounts(cfg["account_sid"]).fetch()
        else:
            client = Client(cfg["account_sid"], cfg["auth_token"])
            acc = client.api.accounts(cfg["account_sid"]).fetch()
        
        msg = (f"Status akun  : {acc.status}\n"
               f"Friendly name: {acc.friendly_name}\n"
               f"Tipe akun    : {acc.type}\n"
               f"Sandbox mode : {cfg['sandbox']}\n"
               f"Nomor kirim  : {cfg['from_number']}")
        if RICH:
            console.print(Panel(msg, title="[bold green]✓ Twilio Terhubung[/bold green]",
                                border_style="green"))
            console.print("\n[dim]Sandbox: penerima harus kirim 'join <kode>' ke +14155238886 dulu.[/dim]")
        else:
            print("\n[OK] Twilio terhubung")
            print(msg)
    except TwilioRestException as e:
        msg = f"Twilio error {e.code}: {e.msg}\n{_twilio_error_hint(e.code)}"
        if RICH:
            console.print(Panel(msg, title="[red]Gagal[/red]", border_style="red"))
        else:
            print(f"\n[X] {msg}")
    except Exception as e:
        if RICH:
            console.print(Panel(str(e), title="[red]Error[/red]", border_style="red"))
        else:
            print(f"\n[X] {e}")


def _print_result(ok, info):
    if RICH:
        if ok:
            t = Table(show_header=False, border_style="dim")
            t.add_column("k", style="dim"); t.add_column("v")
            for k, v in info.items():
                t.add_row(str(k), str(v))
            console.print(Panel(t, title="[bold green]✓ Terkirim[/bold green]",
                                border_style="green"))
        else:
            err = info.get("error", "Unknown error")
            hint = info.get("hint", "")
            msg = err + (f"\n\n[yellow]Saran:[/yellow] {hint}" if hint else "")
            console.print(Panel(msg, title="[red]✗ Gagal[/red]", border_style="red"))
    else:
        if ok:
            print("[OK] Terkirim")
            for k, v in info.items():
                print(f"  {k}: {v}")
        else:
            print(f"[X] {info.get('error', 'Unknown')}")
            if info.get("hint"):
                print(f"    Saran: {info['hint']}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "send":
        cli_send(args[1:])
    elif cmd == "template":
        cli_template(args[1:])
    elif cmd == "test":
        cli_test()
    else:
        print(f"Perintah tidak dikenal: {cmd}")
        print("Gunakan: send | template | test")


if __name__ == "__main__":
    main()
