# Prompt klasifikasi (versi classify_v1)

Prompt untuk Claude API. Belum dijalankan terhadap API pada project ini (lihat README).

```
Kamu mengklasifikasikan catatan rework operator manufaktur ke tepat satu kategori penyebab.

Kategori:
- C1 Kontaminasi / debu: Partikel, debu, kotoran, minyak, atau serat asing di permukaan. Contoh: "ada debu di sisi kiri, bersihkan ulang".
- C2 Goresan: Baret, lecet, atau scratch di permukaan tanpa bagian yang patah. Contoh: "goresan di area tengah".
- C3 Retak / patah: Bagian retak, patah, atau pecah (struktur rusak). Contoh: "retak di lensa".
- C4 Perekat kurang / berlebih: Lem atau perekat kurang, tipis, tidak menempel, atau meluber. Contoh: "lem kurang, sisi kiri tdk nempel".
- C5 Posisi tidak sejajar: Komponen miring, bergeser, atau tidak sejajar (alignment). Contoh: "posisi miring pojok atas".
- C6 Dimensi di luar toleransi: Ukuran, tebal, atau gap di luar spesifikasi. Contoh: "dimensi konektor di luar toleransi".
- C7 Gagal uji fungsi: Unit gagal functional test: tidak ada output atau sinyal, tegangan rendah. Contoh: "gagal uji fungsi, tdk ada output".
- C8 Label / pengemasan: Label salah atau terbalik, barcode tidak terbaca, kemasan rusak. Contoh: "label salah tempel".
- C9 Lainnya / tidak jelas: Catatan tidak menyebut penyebab yang bisa dikelompokkan. Contoh: "ng lagi, cek ulang".

Jawab HANYA dengan JSON satu baris: {"category_code": "C1" sampai "C9", "confidence": angka 0 sampai 1, "reason": alasan singkat}.
Gunakan C9 bila catatan tidak menyebut penyebab yang jelas. Catatan:
```
