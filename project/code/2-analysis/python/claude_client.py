"""Klasifikasi catatan dengan Claude API (modul pembantu, bukan skrip bernomor).

PENTING: bagian ini TIDAK dijalankan terhadap API pada project ini karena tidak ada API key di lingkungan pengerjaan.
Yang diuji (07_test_claude_pipeline.py) hanyalah penyusunan prompt, pemeriksaan format JSON, dan logika ulang satu kali,
memakai klien palsu. Pemanggilan API sebenarnya belum pernah diuji.
"""
import json
import time

import common as CM

PROMPT_VERSION = "classify_v1"
MODEL_NAME = "claude-sonnet-5-5"          # nama model yang dikonfigurasi; tidak dipanggil pada project ini


def render_prompt():
    lines = ["Kamu mengklasifikasikan catatan rework operator manufaktur ke tepat satu kategori penyebab.", "", "Kategori:"]
    for code, (name, definition, example) in CM.TAXONOMY.items():
        lines.append(f"- {code} {name}: {definition} Contoh: \"{example}\".")
    lines += ["", "Jawab HANYA dengan JSON satu baris: {\"category_code\": \"C1\" sampai \"C9\", \"confidence\": angka 0 sampai 1, \"reason\": alasan singkat}.",
              "Gunakan C9 bila catatan tidak menyebut penyebab yang jelas. Catatan:"]
    return "\n".join(lines)


def parse_answer(text):
    """Kembalikan (category_code, confidence) atau None bila format tidak valid (di luar daftar kategori atau confidence di luar 0..1)."""
    try:
        d = json.loads(text.strip())
        code, conf = d["category_code"], float(d["confidence"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
    if code not in CM.TAXONOMY or not 0.0 <= conf <= 1.0:
        return None
    return code, conf


def classify_note(client, note_text, max_retry=1):
    """client.complete(prompt, note) -> (teks, token_masuk, token_keluar). Jawaban tidak valid diulang satu kali, lalu C9 dengan confidence 0."""
    prompt = render_prompt()
    tokens, t0 = 0, time.perf_counter()
    for attempt in range(max_retry + 1):
        text, t_in, t_out = client.complete(prompt, note_text)
        tokens += t_in + t_out
        parsed = parse_answer(text)
        if parsed:
            return dict(category_code=parsed[0], confidence=parsed[1], tokens=tokens, attempts=attempt + 1, valid=1, seconds=time.perf_counter() - t0)
    return dict(category_code="C9", confidence=0.0, tokens=tokens, attempts=max_retry + 1, valid=0, seconds=time.perf_counter() - t0)


class AnthropicClient:
    """Pemanggil API sebenarnya (belum diuji). Butuh variabel lingkungan ANTHROPIC_API_KEY; key tidak pernah disimpan di kode."""

    def __init__(self):
        import anthropic  # impor lambat: tidak diperlukan untuk menjalankan pipeline lokal
        self.client = anthropic.Anthropic()

    def complete(self, prompt, note_text):
        r = self.client.messages.create(model=MODEL_NAME, max_tokens=120, system=prompt, messages=[{"role": "user", "content": note_text}])
        return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
