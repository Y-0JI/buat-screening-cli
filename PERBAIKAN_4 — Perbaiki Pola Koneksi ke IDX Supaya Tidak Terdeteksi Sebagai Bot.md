# PERBAIKAN_4 — Perbaiki Pola Koneksi ke IDX Supaya Tidak Terdeteksi Sebagai Bot

## Latar Belakang

Percobaan mengambil data langsung dari situs IDX selalu gagal (diblokir)
saat dijalankan dari sistem yang sedang dikembangkan. Sempat dikira ini
karena situs IDX memblokir semua akses otomatis dari server, tapi
setelah dicoba manual di luar sistem ini, ternyata pengambilan data
dari IDX bisa berhasil dengan cara yang sama (tanpa browser sungguhan,
cuma panggilan HTTP biasa).

Artinya masalahnya bukan di jenis akses (server vs bukan), tapi di
detail cara sistem ini "berpura-pura" jadi browser saat menghubungi
IDX — detail itu kurang meyakinkan sehingga IDX mendeteksinya sebagai
bot dan memblokirnya. Ada proyek terpisah milik pribadi (pernah dipakai
di project web screening sebelumnya, nama proyeknya IDX-API oleh
NeaByteLab) yang berhasil melakukan hal yang sama dengan pendekatan
serupa tapi detailnya lebih lengkap dan lebih meyakinkan sebagai
request dari browser sungguhan. Itu bisa dijadikan acuan pola yang
sudah terbukti berhasil.

---

## Perbaikan 1 — Lengkapi Identitas Browser yang Dikirim ke IDX

**Masalah:** Identitas browser yang dikirim sistem ini ke IDX saat ini
tidak lengkap / terpotong, sehingga terlihat tidak natural dan mudah
dikenali sebagai bukan browser sungguhan.

**Yang harus dilakukan:** Ganti identitas browser tersebut dengan
identitas browser modern yang lengkap dan valid, persis seperti yang
dikirim oleh browser sungguhan saat mengakses situs seperti IDX.
Pastikan format dan isinya lengkap, tidak terpotong di tengah.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log percobaan
koneksi ke IDX dari sistem ini setelah perbaikan, yang membuktikan
koneksi berhasil dan data yang diminta benar-benar didapat, bukan lagi
diblokir.

---

## Perbaikan 2 — Tambahkan Header yang Biasa Dikirim Browser Saat Meminta Data

**Masalah:** Saat browser sungguhan meminta data ke situs seperti IDX
(bukan membuka halaman biasa, tapi mengambil data di baliknya), ada
header tambahan yang biasa disertakan otomatis oleh browser untuk
menandai bahwa ini permintaan data, bukan membuka halaman. Sistem ini
tidak pernah menyertakan header tersebut sama sekali di setiap
permintaan datanya ke IDX, sehingga terlihat mencurigakan.

**Yang harus dilakukan:** Tambahkan header tersebut pada setiap
permintaan data ke IDX, konsisten di semua tempat yang menghubungi
IDX, mengikuti pola yang biasa dipakai browser sungguhan.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log percobaan
koneksi ke IDX yang membuktikan header ini benar-benar terkirim di
setiap permintaan data, dan datanya berhasil didapat.

---

## Perbaikan 3 — Tiru Pola Waktu dan Header Natural Seperti Browser Sungguhan

**Masalah:** Saat pertama kali menghubungi IDX, sistem ini langsung
menembakkan beberapa permintaan secara berurutan tanpa jeda sama
sekali. Ini tidak natural — pengguna sungguhan yang membuka situs baru
kemudian datanya termuat pasti butuh sedikit waktu jeda. Selain itu ada
satu header umum lain yang biasa dikirim browser saat membuka halaman
yang belum disertakan sistem ini.

**Yang harus dilakukan:** Tambahkan jeda waktu singkat yang wajar di
antara permintaan pertama (membuka halaman) dan permintaan berikutnya
(validasi/pengambilan data) saat proses awal menghubungi IDX. Sertakan
juga header umum tambahan yang biasa dikirim browser saat membuka
halaman, yang sebelumnya belum ada.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log percobaan
koneksi ke IDX dari awal (proses inisialisasi sampai berhasil ambil
data) yang membuktikan jeda waktu benar-benar diterapkan dan
prosesnya berhasil sampai akhir tanpa diblokir.

---

## Catatan untuk Agent

Boleh gunakan proyek IDX-API milik NeaByteLab sebagai referensi pola
yang sudah terbukti berhasil untuk detail identitas browser, header,
dan jeda waktu yang dipakai. Tidak perlu menyalin strukturnya secara
utuh, cukup samakan detail-detail teknis yang membuat request terlihat
seperti browser sungguhan.

## Aturan Verifikasi Umum

Untuk ketiga perbaikan di atas, laporan "sudah selesai" dari agent
**tidak cukup** tanpa bukti konkret berupa log percobaan koneksi ke
IDX yang benar-benar dijalankan dan berhasil mengambil data. Klaim
tanpa bukti nyata dianggap belum selesai.
