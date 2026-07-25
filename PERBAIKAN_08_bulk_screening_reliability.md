# PERBAIKAN_08: Bulk Screening Reliability

## Masalah

Saat menjalankan bulk screening terhadap banyak saham, proses masih
dapat terkena pembatasan (rate limit) dari data provider. Akibatnya
sebagian data gagal diambil, namun proses tetap berjalan sehingga hasil
screening mungkin tidak lengkap tanpa informasi yang jelas kepada
pengguna.

## Tujuan

Meningkatkan keandalan bulk screening agar tetap stabil saat memproses
banyak saham serta memberikan transparansi apabila sebagian data tidak
berhasil diproses.

## Yang Perlu Dilakukan

-   Evaluasi mekanisme pengambilan data pada bulk screening agar lebih
    ramah terhadap batasan data provider.
-   Tingkatkan ketahanan proses terhadap kegagalan sementara (misalnya
    pembatasan request), sehingga tidak langsung mengurangi kualitas
    hasil.
-   Pastikan penggunaan data yang sudah tersedia tidak melakukan
    pengambilan ulang secara tidak perlu.
-   Berikan ringkasan hasil proses di akhir screening, termasuk jumlah
    data yang berhasil diproses dan jumlah yang gagal apabila ada.
-   Pastikan pengguna mengetahui apabila hasil screening mungkin belum
    lengkap karena keterbatasan pengambilan data.

## Acceptance Criteria

-   Bulk screening dapat memproses banyak saham dengan lebih stabil.
-   Frekuensi kegagalan akibat pembatasan data provider berkurang secara
    signifikan.
-   Hasil screening tetap konsisten walaupun terdapat kegagalan parsial.
-   Pengguna memperoleh informasi yang jelas mengenai status proses dan
    kelengkapan hasil.
-   Tidak ada perubahan pada business logic atau aturan screening yang
    sudah ada.
