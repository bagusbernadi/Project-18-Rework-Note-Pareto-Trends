# Taksonomi kategori defect (Project 18)

Sembilan kategori: delapan penyebab dan satu kategori "Lainnya / tidak jelas". Satu catatan mendapat satu kategori utama. Definisi dan contoh di bawah dibuat dari `TAXONOMY` di `code/common.py` dan dipakai oleh prompt (`prompts/classify_v1.md`) dan tabel `dim_category`.

| Kode | Nama | Definisi | Contoh |
|---|---|---|---|
| C1 | Kontaminasi / debu | Partikel, debu, kotoran, minyak, atau serat asing di permukaan. | ada debu di sisi kiri, bersihkan ulang |
| C2 | Goresan | Baret, lecet, atau scratch di permukaan tanpa bagian yang patah. | goresan di area tengah |
| C3 | Retak / patah | Bagian retak, patah, atau pecah (struktur rusak). | retak di lensa |
| C4 | Perekat kurang / berlebih | Lem atau perekat kurang, tipis, tidak menempel, atau meluber. | lem kurang, sisi kiri tdk nempel |
| C5 | Posisi tidak sejajar | Komponen miring, bergeser, atau tidak sejajar (alignment). | posisi miring pojok atas |
| C6 | Dimensi di luar toleransi | Ukuran, tebal, atau gap di luar spesifikasi. | dimensi konektor di luar toleransi |
| C7 | Gagal uji fungsi | Unit gagal functional test: tidak ada output atau sinyal, tegangan rendah. | gagal uji fungsi, tdk ada output |
| C8 | Label / pengemasan | Label salah atau terbalik, barcode tidak terbaca, kemasan rusak. | label salah tempel |
| C9 | Lainnya / tidak jelas | Catatan tidak menyebut penyebab yang bisa dikelompokkan. | ng lagi, cek ulang |

**Asumsi (label asumsi):** rancangan menulis taksonomi sebagai usulan awal "disesuaikan setelah membaca sampel". Pada simulasi, kategori ditentukan generator, jadi definisi di atas ditulis mengikuti templat generator, bukan hasil membaca catatan nyata.
