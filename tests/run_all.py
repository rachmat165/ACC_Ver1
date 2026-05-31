"""
Agentic Self-Testing Framework - ACC
Jalankan semua test di folder tests/ tanpa perlu pytest.

Pakai:
  python tests/run_all.py
atau double-klik TESTS.bat
"""
import sys, importlib.util, traceback
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent / "src"))


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    print()
    print("=" * 56)
    print("  ACC - AGENTIC SELF-TESTING FRAMEWORK")
    print("  PT. Arunika Teknologi Global")
    print("=" * 56)

    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    if not test_files:
        print("  Tidak ada file test_*.py")
        return 0

    grand_pass = grand_fail = 0
    failed_names = []

    for tf in test_files:
        print(f"\n  [{tf.name}]")
        try:
            mod = load_module(tf)
        except Exception as e:
            print(f"    ERROR import: {e}")
            traceback.print_exc()
            grand_fail += 1
            failed_names.append(f"{tf.name} (import)")
            continue

        funcs = [v for k, v in sorted(vars(mod).items())
                 if k.startswith("test_") and callable(v)]
        for fn in funcs:
            try:
                fn()
                grand_pass += 1
                print(f"    PASS  {fn.__name__}")
            except Exception as e:
                grand_fail += 1
                failed_names.append(f"{tf.name}::{fn.__name__}")
                print(f"    FAIL  {fn.__name__}: {e}")

    total = grand_pass + grand_fail
    print()
    print("=" * 56)
    print(f"  HASIL: {grand_pass}/{total} test LULUS")
    if grand_fail:
        print(f"  {grand_fail} GAGAL:")
        for n in failed_names:
            print(f"    - {n}")
        print("=" * 56)
        return 1
    print("  SEMUA TEST LULUS. Sistem siap dipakai.")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())
