"""
TDD: Test alur bot commands — model bernomor, format, skill, sesi.
"""
import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import bot_commands as bot
from user_session import SessionManager

ACC_HOME = Path(__file__).resolve().parent.parent

def _mgr():
    return SessionManager(Path(tempfile.mkdtemp()))


# ── Model bernomor ───────────────────────────────────────────
def test_model_menu_muncul_bernomor():
    mgr = _mgr()
    out = bot.handle("+621", "T", "/model", mgr, ACC_HOME)
    assert "1." in out and "2." in out and "PILIH MODEL" in out

def test_pilih_model_angka_3_haiku():
    mgr = _mgr()
    bot.handle("+621", "T", "/model", mgr, ACC_HOME)
    bot.handle("+621", "T", "3", mgr, ACC_HOME)
    s = mgr.get("+621")
    assert s.model_key == "claude-haiku"
    assert s.model_config["model"] == "claude-haiku-4-5-20251001"

def test_pilih_openrouter_munculkan_submenu():
    mgr = _mgr()
    bot.handle("+621", "T", "/model", mgr, ACC_HOME)
    out = bot.handle("+621", "T", "5", mgr, ACC_HOME)
    assert "SUB-MODEL" in out
    s = mgr.get("+621")
    assert s.pending and s.pending.get("action") == "choose_submodel"

def test_pilih_submodel_deepseek():
    mgr = _mgr()
    bot.handle("+621", "T", "/model", mgr, ACC_HOME)
    bot.handle("+621", "T", "5", mgr, ACC_HOME)
    bot.handle("+621", "T", "7", mgr, ACC_HOME)  # DeepSeek
    s = mgr.get("+621")
    assert s.model_config["provider"] == "openrouter"
    assert "deepseek" in s.model_config["model"]

def test_model_angka_invalid():
    mgr = _mgr()
    bot.handle("+621", "T", "/model", mgr, ACC_HOME)
    out = bot.handle("+621", "T", "99", mgr, ACC_HOME)
    assert "tidak valid" in out.lower() or "1" in out


# ── Format jawaban ───────────────────────────────────────────
def test_set_format_pdf():
    mgr = _mgr()
    bot.handle("+622", "T", "/format pdf", mgr, ACC_HOME)
    assert mgr.get("+622").output_format == "pdf"

def test_parse_format_choice():
    assert bot.parse_format_choice("1") == "wa"
    assert bot.parse_format_choice("2") == "pdf"
    assert bot.parse_format_choice("3") == "txt"
    assert bot.parse_format_choice("xyz") is None


# ── Skill ────────────────────────────────────────────────────
def test_skill_off():
    mgr = _mgr()
    out = bot.handle("+623", "T", "/skill off", mgr, ACC_HOME)
    assert mgr.get("+623").skill is None


# ── Pesan biasa -> None (diteruskan ke AI) ──────────────────
def test_pesan_biasa_diteruskan():
    mgr = _mgr()
    out = bot.handle("+624", "T", "Halo apa kabar", mgr, ACC_HOME)
    assert out is None  # None artinya lanjut ke AI


# ── /menu & /status tidak crash ─────────────────────────────
def test_menu_status_about():
    mgr = _mgr()
    assert bot.handle("+625", "T", "/menu", mgr, ACC_HOME)
    assert bot.handle("+625", "T", "/status", mgr, ACC_HOME)
    assert bot.handle("+625", "T", "/about", mgr, ACC_HOME)


if __name__ == "__main__":
    import traceback
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in funcs:
        try:
            fn(); passed += 1; print(f"  PASS  {fn.__name__}")
        except Exception as e:
            failed += 1; print(f"  FAIL  {fn.__name__}: {e}")
            traceback.print_exc()
    print(f"\n  {passed} lulus, {failed} gagal dari {len(funcs)} test")
    sys.exit(1 if failed else 0)
