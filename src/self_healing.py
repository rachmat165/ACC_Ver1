#!/usr/bin/env python3
"""
Self-Healing Code Loop v2 - Arunika Command Centre
Mode OTOMATIS PENUH dengan progress bar & status visual via rich.
"""
import os, re, sys, json, shutil, subprocess
from pathlib import Path
from datetime import datetime

ACC_HOME = Path(os.environ.get("ACC_HOME", Path(__file__).resolve().parent.parent))
DATA_DIR = ACC_HOME / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from acc import load_env, load_config, call_model
except Exception:
    load_env = lambda: None
    load_config = lambda: {}
    def call_model(s, m, c): return "[call_model tidak tersedia]"

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


GEN_SYSTEM = """Kamu engineer Python senior di Arunika Command Centre.
Tugasmu menulis kode Python BENAR beserta testnya (pytest).

ATURAN OUTPUT (WAJIB):
- Balas HANYA dengan dua blok kode berlabel.
- Blok 1: ===FILE: solution.py
- Blok 2: ===FILE: test_solution.py
- Tanpa pagar ``` apapun.
- Test impor dari solution (mis. `from solution import ...`).
- Test deterministik, tanpa jaringan, tanpa input interaktif.
- Tulis kode bersih, docstring singkat, tangani edge case wajar.
"""

FIX_SYSTEM = """Kamu engineer Python yang memperbaiki kode gagal test.
Input: spek + isi solution.py + isi test_solution.py + output error pytest.

ATURAN OUTPUT (WAJIB):
- Baris 1 diawali '# DIAGNOSA:' berisi penyebab error (maks 1 baris).
- Lalu file perbaikan dengan label:
  ===FILE: solution.py   (selalu sertakan versi lengkap terbaru)
  ===FILE: test_solution.py (HANYA jika test perlu diperbaiki)
- Tanpa pagar ```.
- JANGAN melonggarkan test agar lulus; perbaiki akar masalah.
"""


def parse_files(text):
    files = {}
    parts = re.split(r"^===FILE:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        body = parts[i+1] if i+1 < len(parts) else ""
        body = re.sub(r"^```[a-zA-Z]*\n?", "", body.strip())
        body = re.sub(r"\n?```$", "", body)
        files[name] = body.strip() + "\n"
    return files


def run_pytest(workdir, timeout=60):
    py = sys.executable
    has_pytest = subprocess.run([py, "-c", "import pytest"], capture_output=True).returncode == 0
    try:
        if has_pytest:
            proc = subprocess.run([py, "-m", "pytest", "-q"], cwd=str(workdir),
                                  capture_output=True, text=True, timeout=timeout)
            out = (proc.stdout or "") + (proc.stderr or "")
            return proc.returncode == 0, out
        runner = (
            "import importlib.util,sys,traceback,glob,inspect\n"
            "fails=[];total=0\n"
            "for fp in glob.glob('test_*.py'):\n"
            "    spec=importlib.util.spec_from_file_location(fp[:-3],fp)\n"
            "    m=importlib.util.module_from_spec(spec);sys.modules[fp[:-3]]=m\n"
            "    try:spec.loader.exec_module(m)\n"
            "    except Exception as e:fails.append(fp+': import '+repr(e));continue\n"
            "    for n,f in inspect.getmembers(m,inspect.isfunction):\n"
            "        if n.startswith('test_'):\n"
            "            total+=1\n"
            "            try:f()\n"
            "            except Exception:fails.append(n+': '+traceback.format_exc())\n"
            "print(f'Ran {total} tests, {len(fails)} failed')\n"
            "[print(x) for x in fails]\n"
            "sys.exit(1 if fails or total==0 else 0)\n"
        )
        proc = subprocess.run([py, "-c", runner], cwd=str(workdir),
                              capture_output=True, text=True, timeout=timeout)
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, f"[TIMEOUT] Test melebihi {timeout} detik."


def write_files(workdir, files):
    workdir.mkdir(parents=True, exist_ok=True)
    for n, b in files.items():
        (workdir / n).write_text(b, encoding="utf-8")


def log_event(workdir, event):
    with (workdir / "_healing_log.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def deploy(workdir, deploy_dir):
    deploy_dir.mkdir(parents=True, exist_ok=True)
    for f in workdir.glob("*.py"):
        shutil.copy2(f, deploy_dir / f.name)


# ============ UI ============
def banner(spec):
    if RICH:
        console.print(Panel.fit(
            f"[bold cyan]SELF-HEALING CODE LOOP[/bold cyan]\n"
            f"[dim]Mode otomatis penuh: Generate -> Test -> Fix -> Deploy[/dim]\n\n"
            f"[yellow]Spesifikasi:[/yellow] {spec}",
            border_style="cyan", padding=(1, 2)))
    else:
        print("=" * 60)
        print(f"  SELF-HEALING CODE LOOP - Mode Otomatis")
        print(f"  Spek: {spec}")
        print("=" * 60)


def status(msg, icon="-", style="white"):
    if RICH:
        console.print(f"  [{style}]{icon}[/{style}]  {msg}")
    else:
        print(f"  {icon}  {msg}")


def phase_header(num, name):
    if RICH:
        console.print(f"\n[bold cyan][{num}] {name}[/bold cyan]")
    else:
        print(f"\n[{num}] {name}")


def show_result(passed, it, max_iter):
    if RICH:
        mark = "[bold green]LULUS[/bold green]" if passed else "[bold red]GAGAL[/bold red]"
        console.print(f"  -> {mark}  (iterasi {it}/{max_iter})")
    else:
        print(f"  -> {'LULUS' if passed else 'GAGAL'}  (iterasi {it}/{max_iter})")


def summary_table(workdir, total_iter, passed):
    if not RICH:
        print(f"\nHasil: {'BERHASIL' if passed else 'GAGAL'} | iterasi: {total_iter}")
        return
    t = Table(show_header=False, border_style="dim", padding=(0, 1))
    t.add_column("k", style="dim"); t.add_column("v")
    t.add_row("Status", "[bold green]BERHASIL[/bold green]" if passed else "[bold red]GAGAL[/bold red]")
    t.add_row("Iterasi", str(total_iter))
    t.add_row("Workdir", str(workdir))
    t.add_row("Files", ", ".join(f.name for f in workdir.glob("*.py")))
    if passed:
        t.add_row("Deploy", str(workdir.parent / "deploy" / workdir.name))
    console.print(Panel(t, title="[bold]Ringkasan[/bold]",
                        border_style="green" if passed else "red"))


# ============ LOOP ============
def self_healing_loop(spec, workdir, max_iter=5, timeout=60, auto_approve_deploy=True):
    load_env()
    cfg = load_config()
    workdir = Path(workdir)
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    banner(spec)

    # FASE 1: GENERATE
    phase_header(1, "GENERATE - AI menulis kode + test")
    if RICH:
        with console.status("[cyan]Menulis kode...[/cyan]", spinner="dots"):
            gen = call_model(GEN_SYSTEM, f"Spesifikasi tugas:\n{spec}", cfg)
    else:
        status("Menulis kode...")
        gen = call_model(GEN_SYSTEM, f"Spesifikasi tugas:\n{spec}", cfg)

    files = parse_files(gen)
    if "solution.py" not in files or "test_solution.py" not in files:
        status("Model tidak mengembalikan dua file yang diharapkan.", "X", "red")
        if RICH:
            console.print(Panel(gen[:1200], title="Output mentah", border_style="red"))
        else:
            print(gen[:1200])
        return False
    write_files(workdir, files)
    status(f"Berhasil menulis: {', '.join(files.keys())}", "v", "green")
    log_event(workdir, {"ts": datetime.now().isoformat(), "phase": "generate"})

    passed = False
    it = 1
    for it in range(1, max_iter + 1):
        phase_header(2, f"TEST + VERIFY (iterasi {it}/{max_iter})")
        if RICH:
            with console.status("[cyan]Menjalankan pytest...[/cyan]", spinner="dots"):
                passed, out = run_pytest(workdir, timeout=timeout)
        else:
            status("Menjalankan pytest...")
            passed, out = run_pytest(workdir, timeout=timeout)

        log_event(workdir, {"ts": datetime.now().isoformat(), "phase": "test",
                            "iter": it, "passed": passed})
        show_result(passed, it, max_iter)
        if passed:
            break

        snippet = "\n".join(out.strip().splitlines()[-6:])
        if RICH:
            console.print(Panel(snippet, title="[red]Error[/red]", border_style="red dim", padding=(0,1)))
        else:
            print("  Error:\n   " + snippet.replace("\n", "\n   "))

        if it == max_iter:
            status("Batas iterasi tercapai. Reviu manual diperlukan.", "X", "red")
            break

        phase_header(3, "FIX - AI membaca error & memperbaiki")
        sol = (workdir / "solution.py").read_text(encoding="utf-8")
        tst = (workdir / "test_solution.py").read_text(encoding="utf-8")
        fix_msg = (f"SPESIFIKASI:\n{spec}\n\n"
                   f"===FILE: solution.py\n{sol}\n\n"
                   f"===FILE: test_solution.py\n{tst}\n\n"
                   f"OUTPUT ERROR PYTEST:\n{out[-3000:]}")
        if RICH:
            with console.status("[yellow]Memperbaiki kode...[/yellow]", spinner="dots"):
                fix = call_model(FIX_SYSTEM, fix_msg, cfg)
        else:
            status("Memperbaiki kode...")
            fix = call_model(FIX_SYSTEM, fix_msg, cfg)

        diag = next((l for l in fix.splitlines() if l.startswith("# DIAGNOSA:")), "")
        if diag:
            status(diag.replace("# DIAGNOSA:", "Diagnosa:").strip(), "?", "yellow")
        newfiles = parse_files(fix)
        if not newfiles:
            status("Model tidak mengembalikan file perbaikan. Hentikan.", "X", "red")
            break
        write_files(workdir, newfiles)
        status(f"File diperbarui: {', '.join(newfiles.keys())}", "v", "green")
        log_event(workdir, {"ts": datetime.now().isoformat(), "phase": "fix",
                            "iter": it, "diagnosis": diag})

    if passed:
        phase_header(4, "DEPLOY - staging artefak otomatis")
        deploy_dir = workdir.parent / "deploy" / workdir.name
        deploy(workdir, deploy_dir)
        status(f"Artefak: {deploy_dir}", "P", "green")
        log_event(workdir, {"ts": datetime.now().isoformat(), "phase": "deploy",
                            "deploy_dir": str(deploy_dir)})

    summary_table(workdir, it, passed)
    return passed


def main():
    args = sys.argv[1:]
    if not args:
        print('Pemakaian: python src/self_healing.py "spek" [--max-iter N] [--workdir DIR]')
        return
    max_iter = 5
    workdir = ACC_HOME / "build" / ("tugas-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    spec_parts = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--max-iter":
            i += 1; max_iter = int(args[i])
        elif a == "--workdir":
            i += 1; workdir = Path(args[i])
        elif a == "--spec":
            i += 1; spec_parts.append(Path(args[i]).read_text(encoding="utf-8"))
        else:
            spec_parts.append(a)
        i += 1
    spec = " ".join(spec_parts).strip()
    self_healing_loop(spec, workdir, max_iter=max_iter, auto_approve_deploy=True)


if __name__ == "__main__":
    main()
