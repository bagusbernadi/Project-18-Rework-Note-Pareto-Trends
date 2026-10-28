"""Konstanta dan path bersama Project 18 (Rework Note Analysis: Defect Pareto & Trends).

ROOT = folder project/. Semua skrip memakai path dari sini. Folder hasil dibuat otomatis.
Definisi yang tidak ada di rancangan ditulis di project/docs/definitions.md dengan label asumsi.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"                       # hasil generator: catatan bernama dan kebenaran kategori (tidak di-commit)
ANON = DATA / "anon"                     # data anonim (tidak di-commit, dibuat ulang)
CLEAN = DATA / "clean"                   # teks bersih (tidak di-commit)
MAPPING = DATA / "mapping.json"          # pemetaan stasiun dan model (tidak di-commit)
DB_PATH = ROOT / "notes.duckdb"          # tidak di-commit
RES1 = ROOT / "results" / "1-data-preparation"
RES2 = ROOT / "results" / "2-analysis"
RES3 = ROOT / "results" / "3-presentation"
SQL_DIR = ROOT / "code" / "2-analysis" / "sql"
PROMPTS = ROOT / "prompts"
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"
for _d in (DATA, RAW, ANON, CLEAN, RES1, RES2, RES3, OUTPUTS):
    _d.mkdir(parents=True, exist_ok=True)

SEED = 18
ALPHA = 0.05
BOOT_B = 2000
GOLDEN_N = 300                 # rancangan: ±300 catatan golden set
MIN_WORDS = 3                  # asumsi: catatan < 3 kata dianggap terlalu singkat (tidak valid untuk klasifikasi)
CONF_THRESHOLD = 0.70          # rancangan: ambang keyakinan awal 0,70 (dievaluasi di 11_evaluate.py)
TOP_SHARE_TARGET = 0.80        # rancangan: Q1, kategori yang menyumbang sekitar 80% catatan
H1_BAND = (0.75, 0.85)         # asumsi: "sekitar 80%" = 75% sampai 85% kumulatif pada 2 atau 3 kategori
H5_BAND = (0.05, 0.10)         # rancangan: sekitar 5 sampai 10% catatan terlalu singkat atau tidak jelas
H4_MIN_SHARE_RATIO = 1.5       # asumsi: satu stasiun menyumbang >= 1,5 kali porsi seharusnya untuk satu kategori
MIN_ERRORS_H3 = 10             # asumsi: pasangan tertukar baru bermakna bila total kesalahan >= 10
# Dampak (asumsi, tidak dari data): lihat project/docs/definitions.md
REWORK_MIN_PER_UNIT = 12       # asumsi: menit rework per unit
READ_SEC_PER_NOTE = 20         # asumsi: detik baca dan rekap manual per catatan
TOP_REDUCTION = 0.20           # skenario: kategori teratas turun 20%
CATS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]

# Taksonomi 9 kategori (rancangan: 8 penyebab + Lainnya). Definisi dan contoh dipakai prompt, dim_category, dan docs/taxonomy.md.
TAXONOMY = {
    "C1": ("Kontaminasi / debu", "Partikel, debu, kotoran, minyak, atau serat asing di permukaan.", "ada debu di sisi kiri, bersihkan ulang"),
    "C2": ("Goresan", "Baret, lecet, atau scratch di permukaan tanpa bagian yang patah.", "goresan di area tengah"),
    "C3": ("Retak / patah", "Bagian retak, patah, atau pecah (struktur rusak).", "retak di lensa"),
    "C4": ("Perekat kurang / berlebih", "Lem atau perekat kurang, tipis, tidak menempel, atau meluber.", "lem kurang, sisi kiri tdk nempel"),
    "C5": ("Posisi tidak sejajar", "Komponen miring, bergeser, atau tidak sejajar (alignment).", "posisi miring pojok atas"),
    "C6": ("Dimensi di luar toleransi", "Ukuran, tebal, atau gap di luar spesifikasi.", "dimensi konektor di luar toleransi"),
    "C7": ("Gagal uji fungsi", "Unit gagal functional test: tidak ada output atau sinyal, tegangan rendah.", "gagal uji fungsi, tdk ada output"),
    "C8": ("Label / pengemasan", "Label salah atau terbalik, barcode tidak terbaca, kemasan rusak.", "label salah tempel"),
    "C9": ("Lainnya / tidak jelas", "Catatan tidak menyebut penyebab yang bisa dikelompokkan.", "ng lagi, cek ulang"),
}
CAT_NAME = {k: v[0] for k, v in TAXONOMY.items()}
