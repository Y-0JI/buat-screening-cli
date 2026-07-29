# Execution Plan — Phase 1: Core Watchlist Management

## Objective
Menyediakan cara yang andal untuk membuat dan mengelola watchlist.

## Scope
- Membuat watchlist baru
- Mengganti nama watchlist
- Menghapus watchlist
- Melihat daftar semua watchlist
- Melihat isi satu watchlist (daftar simbol di dalamnya)
- Menambah simbol ke watchlist
- Menghapus simbol dari watchlist
- Mengubah urutan simbol dalam watchlist
- Mencegah simbol duplikat dalam satu watchlist

## Business Rules
- Setiap watchlist harus memiliki nama yang tidak kosong
- Satu watchlist dapat berisi banyak simbol
- Satu simbol tidak boleh muncul dua kali dalam satu watchlist (cegah duplikat)
- Satu simbol boleh muncul di watchlist yang berbeda
- Simbol baru ditambahkan di urutan paling akhir
- Urutan simbol dapat diatur ulang oleh pengguna
- Data watchlist harus persisten (tidak hilang saat aplikasi ditutup)

## Expected Outcome
Pengguna dapat mengorganisir sekuritas ke dalam watchlist yang terstruktur. Phase 1 ini menjadi fondasi bagi fase-fase berikutnya seperti metadata, sinkronisasi data, pencarian & filtering, serta integrasi dengan AI dan web.

## Dependencies
Phase 1 memanfaatkan fondasi yang sudah tersedia dari fase sebelumnya:
- **Universal Symbol Discovery** — daftar emiten dan mekanisme validasi simbol sudah tersedia dari proyek utama
- **CLI Framework** — struktur command Typer dan output Rich sudah tersedia
- **Data Access** — pola akses data ke file JSON sudah mapan

Tidak ada dependency baru yang perlu ditambahkan. Phase 1 tidak membangun ulang mekanisme yang sudah ada.

## Success Criteria
| Kriteria | Keterangan |
|----------|-----------|
| Buat watchlist | Bisa membuat lebih dari satu watchlist dengan nama berbeda |
| Ganti nama | Nama watchlist bisa diubah setelah dibuat |
| Hapus watchlist | Watchlist bisa dihapus beserta seluruh isinya |
| Tambah simbol | Simbol dapat ditambahkan ke watchlist |
| Hapus simbol | Simbol dapat dihapus tanpa mengganggu simbol lain |
| Cegah duplikat | Menambah simbol yang sudah ada dalam watchlist yang sama harus ditolak |
| Atur urutan | Urutan simbol dalam watchlist dapat diubah |
| Persistensi | Data watchlist tetap tersimpan setelah aplikasi dimulai ulang |
| Tampilkan daftar | Semua watchlist dapat dilihat dalam satu tampilan |
| Tampilkan isi | Isi satu watchlist dapat dilihat lengkap dengan urutannya |

## Definition of Done
Phase 1 dinyatakan selesai apabila:
1. Seluruh item dalam **Scope** telah diimplementasikan
2. Seluruh **Success Criteria** terpenuhi dan telah terverifikasi
3. Tidak ada fitur di luar **Scope** yang ikut terimplementasi
4. Implementasi siap menjadi fondasi untuk **Phase 2 (Watchlist Metadata)**
5. Seluruh perubahan telah melalui code review dan disetujui

## Arahan untuk Agen
- Ikuti arsitektur dan konvensi project yang sudah ada
- Jaga kompatibilitas dengan CLI yang sudah ada
- Pastikan implementasi dapat dikembangkan pada fase berikutnya
- Gunakan pendekatan penyimpanan yang sederhana dan tidak memerlukan dependency tambahan

## Di Luar Lingkup Phase 1
Seluruh fitur berikut tidak termasuk dalam Phase 1 dan akan dikerjakan pada fase-fase berikutnya sesuai roadmap Watchlist Database:
- Metadata watchlist (deskripsi, tag, favorit, dll)
- Metadata simbol (nama perusahaan, sektor, industri, dll)
- Sinkronisasi data dengan provider
- Pencarian dan filtering lanjutan
- Backend penyimpanan alternatif (SQLite, PostgreSQL, cloud)
- Integrasi dengan AI, screening, atau fitur lain di luar watchlist
