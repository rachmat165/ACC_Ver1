# SKILL — Self-Healing Code Loop (Generate → Test → Verify → Fix → Deploy)

## Aktivasi
Dipicu saat operator minta: "buat kode", "buatkan fungsi/script", "perbaiki kode",
"buat aplikasi kecil", atau menyebut "self-healing".

## Siklus
1. GENERATE — Tulis kode + test (pytest) dari spesifikasi.
2. TEST     — Jalankan test di subprocess terisolasi (timeout).
3. VERIFY   — Periksa apakah SELURUH test lulus.
4. FIX      — Bila gagal: baca error, diagnosa akar masalah, perbaiki kode.
5. ULANG    — Kembali ke TEST hingga lulus atau batas iterasi tercapai.
6. DEPLOY   — Setelah semua test lulus, stage/deploy artefak.

## Aturan Penting
- Jangan melonggarkan test hanya agar lulus; perbaiki akar masalah.
- Test wajib deterministik: tanpa jaringan, tanpa input interaktif.
- Deploy nyata (git push, rilis) WAJIB persetujuan operator
  (require_human_approval di config.yaml). Default: staging dry-run.
- Setiap fase dicatat ke _healing_log.jsonl untuk audit.

## Format Output Generate (wajib)
===FILE: solution.py
<isi kode>
===FILE: test_solution.py
<isi test>

## Eksekusi
Engine: src/self_healing.py
Contoh: python src/self_healing.py "Buat fungsi PPN 11% + test" --max-iter 5
