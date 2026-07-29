# Execution Plan — Phase 2: Watchlist Metadata

## Objective
Memperkaya setiap watchlist dengan informasi tambahan agar lebih mudah diorganisasi, dikelola, dan menjadi fondasi bagi fitur-fitur berikutnya.

## Scope
- Menambahkan deskripsi pada watchlist
- Mengelompokkan watchlist menggunakan tag
- Menambahkan catatan pada watchlist
- Menandai watchlist sebagai favorit
- Melihat dan mengelola metadata watchlist

## Business Rules
- Seluruh metadata bersifat opsional
- Satu watchlist dapat memiliki lebih dari satu tag
- Status favorit hanya memiliki dua kondisi (favorit atau tidak)
- Metadata dapat diubah tanpa memengaruhi isi watchlist

## Expected Outcome
Pengguna dapat mengelola watchlist dengan informasi yang lebih lengkap sehingga lebih mudah diorganisasi dan dikelola. Phase ini juga menjadi fondasi bagi fitur pencarian, filtering, AI, dan web pada fase berikutnya.

## Success Criteria
- Pengguna dapat menambahkan dan mengubah deskripsi watchlist
- Pengguna dapat menambah dan menghapus tag
- Pengguna dapat menambahkan dan mengubah catatan
- Pengguna dapat menandai atau menghapus status favorit
- Seluruh metadata ditampilkan saat melihat detail watchlist
- Metadata tetap tersedia setelah aplikasi dijalankan kembali

## Arahan untuk Agen
- Ikuti arsitektur, konvensi, dan pola project yang sudah ada
- Jaga konsistensi pengalaman CLI yang telah dibangun pada Phase 1
- Pastikan implementasi tetap mudah dikembangkan pada fase berikutnya

## Di Luar Lingkup Phase 2
- Metadata simbol (nama perusahaan, sektor, industri, dan informasi lainnya) — Phase 3
- Sinkronisasi dengan data provider — Phase 4
- Pencarian dan filtering lanjutan — Phase 5
- Backend penyimpanan alternatif (SQLite, PostgreSQL, cloud) — Phase 6
