# PERBAIKAN_09 – Stock Universe Quality & Provider Validation

## Masalah

Pada proses bulk screening masih terdapat banyak ticker yang tidak memiliki data valid dari data provider. Akibatnya muncul banyak log seperti:

- `possibly delisted`
- `Quote not found`
- `HTTP 404`
- `No data found`

Walaupun proses screening tetap berjalan, log menjadi penuh oleh ticker yang memang sudah tidak valid atau tidak dapat diproses.

---

## Tujuan

Meningkatkan kualitas proses bulk screening dengan memastikan hanya ticker yang valid dan relevan yang diproses.

Fokus perbaikan adalah kualitas stock universe, bukan mengubah business logic screening.

---

## Yang Perlu Dilakukan

- Audit sumber daftar saham yang digunakan pada bulk screening.
- Pastikan ticker yang sudah tidak valid tidak terus diproses pada setiap screening.
- Jika memungkinkan, validasi ticker menggunakan data provider yang lebih sesuai sebelum melakukan fetch data harga.
- Bedakan kondisi seperti:
  - ticker tidak valid
  - data sementara tidak tersedia
  - provider sedang bermasalah
- Kurangi log yang tidak memberikan nilai tambah, tetapi tetap pertahankan informasi penting untuk debugging.

---

## Yang Tidak Berubah

- Business logic screening.
- Aturan BUY / HOLD / SELL.
- Perhitungan indikator.
- Format hasil screening.

---

## Acceptance Criteria

- Bulk screening tidak lagi menghasilkan banyak log untuk ticker yang sudah tidak valid.
- Daftar saham yang diproses lebih akurat dan relevan.
- Request yang tidak perlu ke data provider berkurang.
- Output terminal menjadi lebih bersih dan mudah dipahami.
- Business logic screening tetap menghasilkan hasil yang sama untuk ticker yang valid.
- Seluruh test existing tetap lolos.

---

## Catatan

Tujuan issue ini adalah meningkatkan kualitas universe saham yang digunakan oleh engine.

Perbaikan ini tidak berfokus pada menyembunyikan warning, tetapi mengurangi penyebab munculnya warning tersebut melalui validasi dan pemeliharaan daftar ticker yang diproses.
