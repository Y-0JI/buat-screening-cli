import glob
import os

from app.agent.core import _build_system_prompt, _load_prompt

_PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "prompts")


def _prompt(name: str) -> str:
    with open(os.path.join(_PROMPT_DIR, name)) as f:
        return f.read()


def test_no_structure_variation_instructions_left():
    for path in glob.glob(os.path.join(_PROMPT_DIR, "*.md")):
        content = _prompt(os.path.basename(path)).lower()
        assert "variasikan struktur" not in content, f"instruksi konflik masih ada di {path}"


def test_guideline_present_and_single_source():
    g = _prompt("response_guideline.md")
    for marker in ("## Struktur respons", "## Gaya bahasa"):
        assert marker in g


def test_system_prompt_embeds_guideline():
    p = _build_system_prompt()
    assert p.count("## Struktur respons") == 1, "guideline disisipkan sekali, tidak duplikat"
    assert "## Gaya bahasa" in p
    assert "variasikan struktur" not in p.lower()
    assert "Ikuti Response Guideline" in p


def test_guideline_recommendation_is_conditional():
    g = _prompt("response_guideline.md")
    assert "definisi/penjelasan sederhana" in g, "rekomendasi tidak boleh dipaksakan untuk pertanyaan definisi"
    assert "TIDAK diulang" in g, "output terstruktur tidak boleh diulang AI"


def test_analysis_prompt_aligned():
    p = _prompt("analysis.md")
    assert "Response Guideline" in p
    assert "variasikan" not in p.lower()
    assert "rekomendasi singkat" in p, "analyze harus menyediakan rekomendasi bila bersifat keputusan"


def test_research_prompt_adds_insight_not_repetition():
    p = _prompt("research.md")
    assert "BUKAN bagian yang harus ditulis ulang" in p
    assert "Hanya pakai data yang diberikan" in p