"""
TDD: Test classify_twilio_error - ubah error Twilio teknis jadi pesan jelas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from doc_utils import classify_twilio_error


def test_daily_limit_63038():
    err = "exceeded the 50 daily messages limit ... errors/63038"
    code, msg, is_quota = classify_twilio_error(err)
    assert code == 63038
    assert is_quota is True
    assert "kuota" in msg.lower() or "limit" in msg.lower() or "batas" in msg.lower()

def test_not_joined_sandbox_63016():
    err = "errors/63016 message failed"
    code, msg, is_quota = classify_twilio_error(err)
    assert code == 63016
    assert is_quota is False
    assert "join" in msg.lower() or "sandbox" in msg.lower()

def test_too_long_21617():
    err = "concatenated message body exceeds the 1600 character limit errors/21617"
    code, msg, is_quota = classify_twilio_error(err)
    assert code == 21617
    assert "panjang" in msg.lower() or "1600" in msg

def test_auth_error_20003():
    err = "errors/20003 authenticate"
    code, msg, is_quota = classify_twilio_error(err)
    assert code == 20003
    assert "auth" in msg.lower() or "token" in msg.lower()

def test_unknown_error():
    err = "some random error without code"
    code, msg, is_quota = classify_twilio_error(err)
    assert code is None
    assert is_quota is False
    assert msg  # tetap ada pesan generik

def test_quota_flag_hanya_untuk_limit():
    # Hanya 63038 (daily) & 63018 (rate) yang dianggap kuota
    _, _, q1 = classify_twilio_error("errors/63038")
    _, _, q2 = classify_twilio_error("errors/21617")
    assert q1 is True
    assert q2 is False


if __name__ == "__main__":
    import traceback
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in funcs:
        try:
            fn(); passed += 1; print(f"  PASS  {fn.__name__}")
        except Exception as e:
            failed += 1; print(f"  FAIL  {fn.__name__}: {e}"); traceback.print_exc()
    print(f"\n  {passed} lulus, {failed} gagal dari {len(funcs)} test")
    sys.exit(1 if failed else 0)
