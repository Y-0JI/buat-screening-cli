# PERBAIKAN_07 — Konsistensi Hasil Analisis AI

**Repo:** buat-screening-cli

**Konteks:** Saat analisis dijalankan berulang menggunakan data yang sama, AI terkadang memberikan narasi, penekanan, atau kesimpulan yang berbeda. Variasi bahasa masih dapat diterima, tetapi perubahan interpretasi atau rekomendasi dapat mengurangi kepercayaan pengguna terhadap hasil analisis.

---

## Investigasi Root Cause

### Experiment Results

| Experiment | Avg Similarity | Unique/5 | Speed |
|---|---|---|---|
| `coba9router` (T=default) → `deepseek-v4-flash-free` | 0.0978 | 5/5 | ~18s |
| `coba9router` (T=0) → `deepseek-v4-flash-free` | 0.1046 | 5/5 | ~19s |
| `gh/gpt-4o-mini-2024-07-18` (T=0) | **0.8136** | **2/5** | **~4s** |

### Confirmed Root Causes

1. **Model `coba9router` routes to `deepseek-v4-flash-free`** — model inherently nondeterministic. Avg pairwise similarity ~0.10 (essentially random). Temperature=0 makes **no measurable difference**.
2. `gh/gpt-4o-mini-2024-07-18` + T=0 produces highly consistent output (0.81 similarity, 4/5 runs identical). Also 4.5x faster.

### Validated Non-Causes

- **Temperature absence** — Not a factor. T=0 on nondeterministic model changes nothing.
- **"Variasikan struktur" prompt instructions** — Not a factor. Model variance drowns out prompt effects.

---

## What Changed

### `app/services/llm.py`
- Added `temperature: float | None = None` parameter to `chat_completion()`.
- If set, includes `temperature` in the API payload.

### `app/agent/core.py`
- `analyze_with_ai()` and `compare_with_ai()` now call `chat_completion(..., temperature=0)`.
- `ask_llm()` (chat mode) unchanged — keeps default temperature for creative responses.

### `app/agent/research.py`
- Research report synthesis now uses `temperature=0` for consistent report generation.

### `.env.example`
- Changed default model from placeholder to `gh/gpt-4o-mini-2024-07-18`.

---

## Verifikasi wajib (jangan skip)

1. Jalankan analisis beberapa kali menggunakan data yang sama tanpa ada perubahan data pasar.
2. Pastikan fakta utama yang digunakan AI tetap sama.
3. Pastikan kesimpulan dan rekomendasi tetap memiliki arah yang konsisten.
4. Pastikan perbedaan yang muncul hanya pada penyampaian, bukan pada makna analisis.
5. Dokumentasikan hasil pengujian sebagai bukti bahwa analisis sudah cukup stabil untuk kondisi data yang identik.
