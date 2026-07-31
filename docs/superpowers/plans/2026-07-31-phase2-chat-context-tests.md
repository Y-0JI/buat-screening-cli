# Phase 2 — Perkuat Pengujian Penyimpanan Konteks Percakapan (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Goal:** Buktikan lewat pengujian bahwa penyimpanan konteks percakapan (PR Phase 2, issue #164) benar-benar memenuhi keputusan execution plan. Perubahan terbatas pada pengujian; kode produksi hanya diubah bila pengujian membuktikan pelanggaran, dengan perbaikan sekecil mungkin pada area penyimpanan konteks percakapan.

**Global Constraints:**
- Tidak memperluas scope ke personalisasi (preferensi user), perubahan arsitektur, atau kemampuan AI baru.
- Tidak menambah dependency.
- Alur chat dijalankan sungguhan lewat CLI (input nyata); mock hanya di batas eksternal: panggilan AI (jaringan) dan file memori (isolasi, jangan mencemari memori user).
- Tiap task: eksplorasi → pengujian → seluruh test suite lulus → lanjut.

---

### Task 1: Tiga tes end-to-end alur chat

**Tujuan:** Buktikan empat perilaku: (1) hanya bagian percakapan yang perlu dipertahankan yang tersimpan, (2) percakapan tanpa interaksi bermakna tidak membuat entri, (3) penyimpanan tidak memicu panggilan AI tambahan, (4) mekanisme bekerja lewat alur chat sesungguhnya.

**Tes A — hanya ekor percakapan yang disimpan, tanpa panggilan AI tambahan:**
- Jalankan chat asli dengan 5 pertanyaan-jawaban (5 turn user, 10 pesan total).
- Verifikasi:
  - Panggilan AI terjadi tepat 5 kali (satu per pertanyaan user) — membuktikan penyimpanan memori tidak memicu panggilan AI apa pun di luar percakapan normal (deterministik, tanpa biaya tambahan).
  - Entri memori terbentuk (tipe konteks penting, sumber chat).
  - Isi entri mengandung pertanyaan/jawaban ke-4 dan ke-5 (ekor percakapan).
  - Isi entri TIDAK mengandung pertanyaan ke-1 — membuktikan hanya 3 pertanyaan-jawaban terakhir tersimpan, bukan seluruh riwayat.

**Tes B — percakapan tanpa isi tidak disimpan walau user mengetik:**
- Jalankan chat asli, user mengetik 2 pertanyaan, tapi AI gagal merespon semua (panggilan AI dikembalikan kosong — percakapan tidak pernah terbentuk).
- Verifikasi: tidak ada entri memori baru. (Membedakan "user mengetik" dari "percakapan berisi" — isi = pertanyaan yang benar-benar dijawab.)

**Tes C — sesi langsung keluar tanpa apa pun:**
- Jalankan chat asli, langsung `exit` tanpa mengetik apa pun.
- Verifikasi: tidak ada entri memori, panggilan AI tidak terjadi sama sekali.

### Task 2: Verifikasi

- Test chat lulus semua (tes A, B, C + tes chat yang sudah ada).
- Seluruh test suite lulus, tidak ada regresi.
- Jika ada tes gagal: perbaiki kode produksi seminimal mungkin, hanya area penyimpanan konteks percakapan, lalu ulangi verifikasi.

### Task 3: Perbarui PR

- Commit → push ke branch PR Phase 2 yang sudah ada → PR ter-update otomatis. **Tidak di-merge** sampai review selesai.

---

**Di luar scope:** personalisasi, perubahan arsitektur, kemampuan AI baru, ringkasan percakapan cerdas.
