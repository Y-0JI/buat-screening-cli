# Phase 2 — Kunci Batas Ekor Penyimpanan Percakapan (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Goal:** Perkuat pengujian penyimpanan konteks percakapan (PR Phase 2) agar batas ekor yang disimpan terbukti presisi, setiap sesi menghasilkan tepat satu entri, dan tanpa panggilan AI tambahan. Perubahan fokus pada pengujian; kode produksi hanya diubah bila pengujian membuktikan perilaku tidak sesuai, dengan perbaikan sekecil mungkin hanya di area penyimpanan konteks percakapan.

**Global Constraints:**
- Tidak memperluas scope: personalisasi, perubahan arsitektur, kemampuan AI baru — semua di luar.
- Tidak menambah dependency.
- Alur chat dijalankan sungguhan lewat CLI (input nyata); mock hanya di batas eksternal: panggilan AI (jaringan) dan file memori (isolasi).
- Tiap task: eksplorasi → pengujian → seluruh test suite lulus → lanjut.

---

### Task 1: Perkuat tes batas ekor percakapan

**Tujuan:** Buktikan batas ekor yang tersimpan tepat 3 pertanyaan-jawaban terakhir (bukan sekadar "bukan seluruh riwayat"), dan setiap sesi menghasilkan tepat satu entri.

**Tes A — perkuat (tes existing yang menjalankan chat asli 5 Q&A):**
- Tambahkan verifikasi: pertanyaan ke-3 ADA di isi entri (batas bawah ekor — ekor 3 Q&A terakhir = {3,4,5} semua tersimpan).
- Tambahkan verifikasi: pertanyaan ke-2 TIDAK ada di isi entri (yang ke-4 dari akhir sudah terpotong) — mengunci tepat 3 pertanyaan-jawaban, bukan 4 atau lebih.
- Tambahkan verifikasi: tepat satu entri memori chat terbentuk per sesi (bukan bertumpuk).

**Tes B & C (sudah ada, dipertahankan):**
- Tes B: user mengetik tapi AI gagal merespon → tidak ada entri.
- Tes C: sesi langsung keluar → tidak ada entri, AI tidak dipanggil.

### Task 2: Verifikasi

- Test chat lulus semua (A, B, C + tes chat existing).
- Seluruh test suite lulus, tidak ada regresi.
- Jika ada tes gagal: perbaiki kode produksi seminimal mungkin, hanya area penyimpanan konteks percakapan, lalu ulangi verifikasi. Jika semua lulus tanpa perubahan produksi → implementasi Phase 2 dianggap memenuhi tujuan.

### Task 3: Perbarui PR

- Commit → push ke branch PR Phase 2 yang sudah ada → PR ter-update otomatis. **Tidak di-merge** sampai review akhir selesai.

---

**Di luar scope:** personalisasi, perubahan arsitektur, kemampuan AI baru, ringkasan percakapan cerdas.
