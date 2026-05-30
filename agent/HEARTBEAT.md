# HEARTBEAT — Siklus Operasi Arunika

## Detak (interval default: 30 menit)
Setiap detak, jalankan urutan berikut:

1. CEK ANTRIAN
   - Adakah pesan WhatsApp belum diproses? Proses sesuai prioritas.

2. CEK JADWAL
   - Adakah cron job jatuh tempo? (lihat data/schedule.yaml)

3. CEK TARGET
   - Bandingkan progres pendapatan vs target Rp 1 M/tahun.
   - Bila meleset dari lintasan, usulkan tindakan ke operator.

4. TINDAK LANJUT
   - Proposal/penawaran menunggu balasan klien > 3 hari? Susun draf follow-up.

5. PEMELIHARAAN MEMORI
   - Ringkas sesi panjang ke memori semantik.
   - Catat pelajaran baru sebagai kandidat skill.

6. LAPOR (bila ada hal penting)
   - Kirim ringkasan singkat ke operator via WhatsApp.

## Prioritas
- P1 Permintaan langsung operator
- P2 Tenggat klien (proposal, laporan)
- P3 Tugas terjadwal rutin
- P4 Optimasi internal & pembelajaran
