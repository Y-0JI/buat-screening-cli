# PERBAIKAN_21 — Koordinasi Rate Limit Belum Benar-Benar Nyambung, Plus 3 Sisa Pekerjaan

## Masalah

Setelah dicek ulang, fitur validasi ticker (`validate-universe`) dan pekerjaan pembersihan kode sebelumnya sudah jalan dan sebagian besar bagus. Tapi ada beberapa hal yang kelihatannya sudah benar di permukaan, ternyata belum benar-benar berfungsi seperti yang dimaksud:

1. Dua bagian sistem yang seharusnya saling memberi tahu kapan salah satu kena rate limit — supaya yang satu tidak terus jalan sementara yang lain sedang didinginkan — ternyata TIDAK benar-benar terhubung. Masing-masing punya catatan sendiri-sendiri yang terlihat sama tapi sebenarnya terpisah.
2. Proses validasi ticker masih menjalankan jumlah proses paralel yang jauh lebih tinggi dibanding proses screening/gainers/losers yang sudah diturunkan sebelumnya — jadi proses yang paling berisiko kena rate limit sekarang justru yang paling "kencang" jalannya.
3. Ada dua berkas pengujian otomatis yang isinya hampir sama persis (menguji command yang sama dengan cara yang sama), dan sebagian dari pengujian itu benar-benar menghubungi Yahoo Finance secara langsung saat dijalankan, bukan memakai data tiruan. Ini membuat pengujian jadi lambat dan hasilnya bisa berubah-ubah tergantung koneksi internet saat itu.
4. Perbaikan sebelumnya soal "nama saham tampil sebagai kode ticker doang" (PERBAIKAN_14 bagian nama & sektor) belum benar-benar dikerjakan. Nama dan sektor perusahaan masih diminta langsung ke Yahoo Finance setiap kali, padahal seharusnya diambil dari data lokal yang sudah lengkap dan benar.

## Yang perlu diperbaiki

1. **Satukan benar-benar sinyal "baru saja kena rate limit" antara proses validasi ticker dan proses screening/gainers/losers/analisis.** Saat ini keduanya punya catatan sendiri-sendiri yang terlihat seperti berbagi informasi yang sama, tapi kenyataannya tidak saling terhubung. Pastikan begitu salah satu bagian sistem kena rate limit, SEMUA bagian lain (termasuk proses validasi ticker) benar-benar ikut tahu dan ikut melambat — bukan cuma bagian yang kena limit itu sendiri.

2. **Samakan jumlah proses paralel untuk validasi ticker dengan angka yang sudah dipakai di proses screening/gainers/losers saat ini** (yang sudah diturunkan sebelumnya karena terbukti lebih aman). Jangan biarkan proses validasi ticker punya angka concurrency sendiri yang lebih tinggi.

3. **Gabungkan dua berkas pengujian yang isinya hampir sama** menjadi satu, hilangkan duplikasinya. Untuk semua pengujian yang menjalankan command seperti analisis satu saham, tren, skor, atau perbandingan saham — pastikan pengujian itu memakai data tiruan/simulasi untuk bagian yang mengambil data dari Yahoo Finance, jangan sampai pengujian ini benar-benar menghubungi internet saat dijalankan.

4. **Selesaikan bagian nama & sektor perusahaan yang belum dikerjakan dari perbaikan sebelumnya.** Nama dan sektor perusahaan untuk ditampilkan ke user harus diambil dari data ticker lokal yang sudah ada (yang sudah lengkap dan benar), bukan diminta ulang ke Yahoo Finance setiap kali. Yahoo Finance cukup dipakai untuk data harga saja.

## Batasan — Jangan diubah

- Alur perintah CLI dan format output ke user tidak berubah.
- Logika screening/sinyal teknikal tidak berubah.
- Cara ticker delisted difilter dari hasil screening (yang sudah bekerja dengan baik sekarang) tidak perlu diubah, cukup dipertahankan.
- Daftar/isi database saham lokal tidak perlu diubah, cukup dipakai lebih optimal untuk nama & sektor.

## Catatan buat agent

- Untuk poin 1: kalau caranya cuma "impor nilai dari satu berkas ke berkas lain", itu biasanya TIDAK cukup untuk membuat dua bagian program benar-benar berbagi informasi yang berubah-ubah secara real-time — nilainya akan tercatat sebagai salinan terpisah, bukan sumber yang sama. Pastikan cara yang dipakai benar-benar membuat kedua sisi membaca dan menulis ke satu sumber yang sama, lalu buktikan itu bekerja dengan mencoba memicu rate limit dari satu sisi dan menunjukkan sisi lain juga ikut melambat.
- Untuk poin 3: setelah digabung dan di-mock, jalankan seluruh rangkaian pengujian dari awal sampai akhir tanpa akses internet dan pastikan semuanya tetap selesai dengan wajar (tidak ada yang menggantung lama).

## Verifikasi wajib setelah agent klaim selesai

- Tunjukkan bukti (skenario nyata atau log) bahwa saat satu bagian sistem terdeteksi kena rate limit, proses validasi ticker yang sedang/akan berjalan juga ikut melambat — bukan cuma tercatat di sisi masing-masing secara terpisah.
- Tunjukkan bahwa jumlah proses paralel untuk validasi ticker sekarang sama dengan yang dipakai di proses screening/gainers/losers.
- Jalankan seluruh rangkaian pengujian otomatis dari nol, tunjukkan waktu totalnya, dan pastikan tidak ada lagi pengujian yang benar-benar menghubungi Yahoo Finance secara langsung.
- Jalankan screening atau analisis untuk beberapa saham yang sebelumnya tampil dengan nama "kosong"/sama seperti kode tickernya, dan tunjukkan nama perusahaan yang benar sekarang muncul.
- Semua bukti berupa cuplikan log/output nyata dari hasil jalan ulang, bukan cuma klaim tertulis.
