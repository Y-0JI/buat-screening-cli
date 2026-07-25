# PERBAIKAN_06 — Riwayat Percakapan di Mode Chat Turun Kualitas

**Repo:** buat-screening-cli
**Konteks:** hasil review PR #56 (fix chat supaya bisa akses tool, dari `PERBAIKAN_05` Issue 1). Fix-nya berhasil buat soal akses tool, tapi caranya bikin kualitas riwayat percakapan turun.

**Cara pakai dokumen ini:** kerjakan issue ini, lalu jalankan verifikasi sebelum klaim selesai.

---

## Issue — Riwayat percakapan sekarang digabung jadi satu blok teks, bukan riwayat asli

**Masalah:**
Sebelum PR #56, mode diskusi interaktif nyimpen riwayat percakapan dengan cara yang benar — tiap ucapan user dan tiap jawaban AI disimpan sebagai entri terpisah dengan label siapa yang ngomong, dan semuanya dikirim utuh ke AI tiap giliran baru.

Setelah PR #56 (yang benerin supaya chat bisa akses tool), cara nyimpen riwayatnya berubah jadi: semua ucapan sebelumnya digabung jadi satu blok teks panjang, terus blok teks itu dijejelin sebagai satu potongan "konteks" doang. AI sekarang harus baca riwayat percakapan dalam bentuk teks mentah yang digabung, bukan riwayat percakapan yang terstruktur rapi.

**Kenapa ini masalah:**
Cara lama lebih akurat buat AI memahami alur percakapan (siapa ngomong apa, kapan). Cara baru berpotensi bikin AI bingung soal urutan/siapa-ngomong-apa kalau percakapannya makin panjang, dan ini langsung bertentangan sama tujuan Fase 2 roadmap (Conversation Context) yang minta riwayat percakapan dipertahankan dengan baik.

**Yang perlu dilakukan:**
Cari cara supaya mode diskusi interaktif tetap punya DUA hal sekaligus, bukan pilih salah satu:
1. Riwayat percakapan tersimpan dan terkirim ke AI dalam bentuk terstruktur asli (bukan digabung jadi teks blok).
2. AI tetap bisa akses & jalanin tools kapan pun dibutuhkan (kemampuan yang baru ditambahkan di PR #56).

Investigate whether the current conversation handling can preserve structured message history while supporting tool execution within the same interaction flow.

Reuse the existing conversation and tool orchestration mechanisms whenever possible instead of introducing parallel implementations.

**Verifikasi wajib (jangan skip):**
1. Buka mode diskusi interaktif, lakukan percakapan minimal 4-5 giliran bolak-balik yang saling nyambung (misal: tanya soal satu saham, terus tanya lanjutan yang mengacu ke jawaban sebelumnya tanpa nyebut ulang nama sahamnya).
2. Pastikan AI masih inget konteks dari giliran-giliran sebelumnya dengan akurat.
3. Di tengah percakapan itu, tanya sesuatu yang butuh data saham asli — pastikan AI masih bisa jalanin tool dan kasih data beneran (bukan cuma kembali ke jawaban generik).
4. Tunjukkan potongan percakapan yang membuktikan dua hal di atas jalan bareng, bukan cuma salah satu.
