# PERBAIKAN.Roadmap_Watchlist_Database — Watchlist Database: Tutup Kesenjangan Sebelum Digabung ke Main

## Latar Belakang

Fase 1 sampai 6 dari roadmap "Watchlist Database" sudah dikerjakan
masing-masing di branch terpisah dan menunggu digabung ke branch
utama. Secara garis besar arahnya sudah sesuai dengan tujuan roadmap:
pengguna bisa membuat, mengubah, dan mengisi watchlist, ada metadata
tambahan di level watchlist maupun simbol, ada fitur cari/filter/urut,
dan penyimpanan datanya sudah dibuat modular (bisa pindah antar jenis
penyimpanan).

Namun hasil audit dan pengujian langsung menemukan beberapa masalah
yang perlu diperbaiki dulu sebelum digabung ke branch utama. Beberapa
di antaranya cukup serius karena bisa merusak data asli pengguna atau
membuat aplikasi crash saat dipakai dengan cara yang wajar. Sisanya
adalah kesenjangan antara apa yang dijanjikan dokumen roadmap dengan
apa yang benar-benar berfungsi saat ini.

Dokumen ini berisi daftar perbaikan untuk menutup kesenjangan tersebut.
Kerjakan berurutan, dan **Perbaikan 1 wajib diselesaikan lebih dulu**
karena berkaitan dengan risiko kehilangan data saat proses pengujian
dijalankan.

---

## Perbaikan 1 — Amankan Data Asli Pengguna dari Proses Pengujian

**Masalah:** Rangkaian pengujian otomatis untuk fitur watchlist saat
ini menulis langsung ke berkas data yang sama dengan yang dipakai
aplikasi sungguhan sehari-hari, bukan ke tempat penyimpanan sementara
yang terpisah. Akibatnya, setiap kali pengujian ini dijalankan,
seluruh isi watchlist asli milik pengguna ikut terhapus/tertimpa tanpa
peringatan apa pun. Ini sudah terbukti terjadi saat pengujian dicoba.

**Yang harus dilakukan:** Ubah rangkaian pengujian fitur watchlist
supaya menggunakan lokasi penyimpanan sementara/terisolasi yang
terpisah total dari data asli aplikasi, sehingga menjalankan
pengujian kapan pun tidak akan pernah menyentuh data sungguhan
pengguna.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan bahwa sebelum dan
sesudah rangkaian pengujian dijalankan, berkas data watchlist asli
sama sekali tidak berubah (misalnya dengan menyimpan data asli lebih
dulu, menjalankan pengujian, lalu membuktikan data asli masih utuh),
sambil seluruh pengujian tetap berhasil lolos seperti biasa.

---

## Perbaikan 2 — Perbaiki Bug Crash pada Fitur Urutkan Watchlist Berdasarkan Posisi

**Masalah:** Watchlist punya opsi mengurutkan isi berdasarkan urutan
posisi simbol. Saat opsi ini dipakai dan ada lebih dari satu simbol
dengan posisi bukan nol (kondisi yang sangat umum dalam pemakaian
normal), aplikasi crash dan menampilkan pesan error teknis mentah ke
pengguna, bukan pesan yang bisa dipahami.

**Yang harus dilakukan:** Perbaiki logika pengurutan tersebut supaya
bisa menangani nilai posisi (angka) dengan benar, dibedakan dari
pengurutan berdasarkan teks seperti nama atau kode saham. Pastikan
juga bila terjadi error yang tidak terduga di fitur ini ke depannya,
pengguna tetap mendapat pesan yang jelas, bukan crash mentah.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log/transkrip
menjalankan perintah urutkan-berdasarkan-posisi pada watchlist berisi
minimal 3 simbol dengan posisi berbeda-beda, dan buktikan hasilnya
terurut benar tanpa crash. Tambahkan juga pengujian otomatis baru
yang mengunci perilaku ini supaya tidak rusak lagi di kemudian hari.

---

## Perbaikan 3 — Perbaiki Bug Ganti Nama Watchlist ke Nama yang Sama

**Masalah:** Saat pengguna mengganti nama sebuah watchlist tapi nama
barunya sama persis dengan nama watchlist itu sendiri saat ini,
sistem keliru menganggapnya sebagai nama yang sudah dipakai watchlist
lain dan menolak perubahan tersebut, padahal seharusnya tidak masalah.

**Yang harus dilakukan:** Perbaiki pengecekan nama duplikat supaya
tidak membandingkan watchlist dengan dirinya sendiri, hanya dengan
watchlist lain.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan bahwa mengganti
nama watchlist ke nama yang sudah dimilikinya sendiri saat ini
berhasil (tidak dianggap error), sementara mengganti nama ke nama
yang sudah dipakai watchlist *lain* tetap ditolak seperti seharusnya.

---

## Perbaikan 4 — Ubah Cara Penyimpanan SQLite agar Tidak Menghapus dan Menulis Ulang Semua Data Setiap Ada Perubahan Kecil

**Masalah:** Salah satu jenis penyimpanan watchlist (SQLite) saat ini
bekerja dengan cara menghapus seluruh data watchlist yang ada lalu
menulis ulang semuanya dari awal, setiap kali ada satu perubahan
sekecil apa pun (misalnya menambah satu simbol ke satu watchlist).
Cara ini berisiko dan tidak akan cocok dengan rencana jangka panjang
roadmap untuk mendukung sinkronisasi multi-perangkat di masa depan,
karena pola hapus-tulis-ulang total akan gampang menimbulkan konflik
atau kehilangan data begitu ada lebih dari satu sumber perubahan.

**Yang harus dilakukan:** Ubah cara kerja penyimpanan ini supaya hanya
menyimpan bagian data yang benar-benar berubah, bukan menghapus dan
menulis ulang seluruh isi database setiap kali.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan bukti (misalnya
lewat log query atau perbandingan sebelum/sesudah) bahwa mengubah satu
watchlist tidak menyentuh ulang data watchlist lain yang tidak
berkaitan dengan perubahan tersebut.

---

## Perbaikan 5 — Bersihkan Berkas yang Tidak Seharusnya Ikut Tersimpan di Riwayat Kode

**Masalah:** Ada berkas cadangan/sisa proses pengembangan yang tidak
sengaja ikut tersimpan di riwayat kode, isinya versi lama kode dengan
sebagian besar penanganan error dinonaktifkan (dikomentari). Berkas
ini memang tidak dipakai aplikasi, tapi seharusnya tidak pernah ikut
tersimpan. Selain itu, aturan pengabaian berkas belum mencakup berkas
database SQLite yang dihasilkan salah satu jenis penyimpanan
watchlist, sehingga berisiko ikut ter-commit secara tidak sengaja bila
jenis penyimpanan itu dipakai.

**Yang harus dilakukan:** Hapus berkas cadangan yang tidak terpakai
tersebut dari riwayat kode, dan lengkapi aturan pengabaian berkas
supaya mencakup jenis-jenis berkas cadangan/sementara dan berkas
database SQLite hasil watchlist.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan bahwa berkas
cadangan tersebut sudah tidak ada lagi di kode, dan tunjukkan bukti
bahwa berkas serupa (backup, database SQLite watchlist) tidak lagi
bisa ikut ter-commit meskipun sempat dibuat secara lokal.

---

## Perbaikan 6 — Lengkapi Metadata Simbol Sesuai yang Dijanjikan Roadmap

**Masalah:** Dokumen roadmap Fase 3 menjanjikan setiap simbol di
watchlist punya metadata lengkap: nama perusahaan, bursa, sektor,
industri, pasar, mata uang, dan identitas penyedia data. Yang benar-
benar terisi dan ter-update saat ini hanya nama perusahaan dan sektor.
Field lain seperti bursa, industri, dan mata uang memang ada di
struktur data tapi tidak pernah diisi oleh proses mana pun, sehingga
selalu kosong. Field pasar dan identitas penyedia data bahkan belum
ada sama sekali di struktur data. Selain itu, proses penyegaran
metadata (Fase 4) saat ini hanya membandingkan dengan satu berkas
data statis lokal, bukan dengan sumber data langsung/live yang
sebenarnya dipakai proyek ini, sehingga tidak benar-benar bisa
mendeteksi kondisi seperti penyedia data yang sedang tidak tersedia,
seperti yang dijanjikan Fase 4.

**Yang harus dilakukan:** Tentukan dan hubungkan sumber data yang
benar untuk tiap field metadata simbol yang dijanjikan roadmap. Jika
ada field yang memang belum realistis diisi sekarang, itu boleh, tapi
harus didokumentasikan secara eksplisit sebagai belum didukung
(perbarui juga dokumen roadmapnya), bukan dibiarkan diam-diam kosong
seolah-olah sudah berfungsi. Sambungkan juga proses penyegaran
metadata ke sumber data langsung yang sudah dipakai proyek ini,
bukan hanya berkas statis lokal.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan sampel beberapa
simbol dengan metadata yang benar-benar terisi nilai nyata untuk
setiap field yang diklaim didukung, atau tunjukkan pembaruan dokumen
roadmap yang menjelaskan field mana yang sengaja belum didukung.
Tunjukkan juga skenario pengujian di mana sebuah simbol menjadi tidak
tersedia di sumber data sebenarnya, dan buktikan watchlist bisa
mendeteksi serta mencerminkan kondisi itu setelah proses penyegaran
dijalankan.

---

## Perbaikan 7 — Konsistenkan Pembuatan Watchlist Default di Semua Jalur Perintah

**Masalah:** Saat aplikasi baru pertama kali dipakai (belum ada
watchlist sama sekali), sebagian perintah otomatis membuatkan
watchlist default untuk pengguna, tapi sebagian perintah lain tidak,
sehingga pengguna baru bisa mendapat pesan error yang membingungkan
tergantung perintah mana yang pertama kali dicoba.

**Yang harus dilakukan:** Samakan perilaku ini di semua perintah
terkait watchlist — baik dengan membuat watchlist default secara
konsisten di semua jalur, atau (jika memang disengaja tidak otomatis)
memberi pesan yang jelas dan konsisten yang mengarahkan pengguna untuk
membuat watchlist terlebih dahulu.

**Kriteria selesai (butuh bukti nyata):** Pada kondisi instalasi baru
tanpa watchlist sama sekali, tunjukkan bahwa mencoba perintah
watchlist apa pun sebagai perintah pertama kali memberi hasil/pesan
yang konsisten dan mudah dipahami, tidak berbeda-beda tergantung
perintah mana yang dicoba lebih dulu.

---

## Aturan Verifikasi Umum

Untuk setiap perbaikan di atas, laporan "sudah selesai" dari agent
**tidak cukup** tanpa bukti konkret berupa log, transkrip output, atau
hasil pengujian yang benar-benar dijalankan. Klaim tanpa bukti
dianggap belum selesai dan harus diulang sampai buktinya bisa
ditunjukkan.

Setelah seluruh perbaikan di atas selesai dan terbukti, baru
pertimbangkan menggabungkan branch fase 1–6 watchlist ke branch utama.
