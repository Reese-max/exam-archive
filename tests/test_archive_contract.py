"""Executable repository contract for the exam-archive static site.

Pins the guarantees documented in README.md:
- index.html is a generated artifact, reproducible from src/ + data/ sources
- exam data lives in per-year chunks that can be fetched as static assets
- first-load payload stays inside the published budgets
- the mobile / keyboard / 200%-zoom / search affordances the 50-persona
  audit requires are present in the shipped page
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rebuild_index  # noqa: E402

INDEX = ROOT / "index.html"
TEMPLATE = ROOT / "src" / "index.template.txt"
DATA_DIR = ROOT / "data"
README = ROOT / "README.md"

INDEX_BUDGET_BYTES = 1_400_000   # generated artifact is ~1.32 MiB; may only shrink
SHELL_BUDGET_BYTES = 120_000     # becomes the first-load payload once chunks lazy-load
CHUNK_BUDGET_BYTES = 160_000     # per-year lazy-load granule (largest is ~133 KiB)
YEARS_DESC = [str(y) for y in range(114, 104, -1)]  # ROC 114 -> 105, newest first

index_bytes = INDEX.read_bytes()
index_lf = index_bytes.replace(b"\r\n", b"\n")
index_text = index_bytes.decode("utf-8")
template_text = TEMPLATE.read_bytes().decode("utf-8")


def test_rebuild_is_byte_exact():
    assert rebuild_index.build() == index_bytes


def test_check_mode_reports_clean():
    assert rebuild_index.check() is True


def test_every_template_marker_has_a_chunk():
    names = rebuild_index.MARKER.findall(template_text)
    assert names == [f"year-{y}" for y in YEARS_DESC]
    assert sorted(p.stem for p in DATA_DIR.glob("year-*.txt")) == sorted(
        f"year-{y}" for y in YEARS_DESC
    )


def test_artifact_contains_no_unsubstituted_markers():
    assert b"ARCHIVE-DATA" not in index_bytes


def test_chunks_are_complete_year_sections():
    for year in YEARS_DESC:
        frag = (DATA_DIR / f"year-{year}.txt").read_bytes()
        assert frag.startswith(f'<div class="year-section" id="year-{year}">'.encode())
        assert frag.endswith(b"</div>\n")
        assert frag.count(b"<div") == frag.count(b"</div")
        assert f"{year}年".encode() in frag
        # chunk content is verbatim archive data: present in the artifact
        assert frag.replace(b"\n", b"\r\n") in index_bytes


def test_first_load_asset_budget():
    assert len(index_bytes) <= INDEX_BUDGET_BYTES
    # first load must not pull any local subresource besides index.html itself
    assert b"<script src=" not in index_bytes
    for href in re.findall(rb'<link[^>]+href="([^"]+)"', index_bytes):
        assert href.startswith(b"https://"), href
    for src in re.findall(rb'src="([^"]+)"', index_bytes):
        assert src.startswith(b"https://"), src


def test_shell_and_chunk_budgets():
    assert len(TEMPLATE.read_bytes()) <= SHELL_BUDGET_BYTES
    chunks = list(DATA_DIR.glob("year-*.txt"))
    assert len(chunks) == len(YEARS_DESC)
    for path in chunks:
        assert len(path.read_bytes()) <= CHUNK_BUDGET_BYTES, path.name
    # the data split is real: the bulk of the archive lives in chunks
    assert sum(len(p.read_bytes()) for p in chunks) > 1_000_000


def test_readme_repository_contract():
    text = README.read_bytes().decode("utf-8")
    for needle in (
        "https://reese-max.github.io/exam-archive/",  # canonical public URL
        "source of truth",                            # status / supersession
        "not superseded",
        "provenance",
        "python3 tests/rebuild_index.py",             # build step
        "python3 -m pytest",                          # test step
        "index.html",                                 # generated artifact named
    ):
        assert needle in text, needle


def test_mobile_smoke():
    assert 'name="viewport" content="width=device-width' in index_text
    assert "@media (max-width: 768px)" in index_text
    assert 'id="hamburgerBtn"' in index_text
    assert "sidebar.classList.toggle('open')" in index_text


def test_keyboard_smoke():
    assert 'class="sidebar-year" role="button" tabindex="0"' in index_text
    assert "addEventListener('keydown'" in index_text
    assert "e.key === 'Enter'" in index_text
    assert "e.key === '/'" in index_text      # '/' focuses search
    assert "e.key === 'Escape'" in index_text


def test_zoom_200_percent_smoke():
    viewport = re.search(r'<meta name="viewport" content="([^"]+)"', index_text).group(1)
    assert "maximum-scale" not in viewport and "user-scalable" not in viewport
    assert index_text.count("rem") > 50  # fluid rem-based layout reflows at 200%


def test_search_open_question_smoke():
    assert 'id="searchInput"' in index_text
    assert "function doSearch(" in index_text
    assert "function toggleCard(" in index_text
    assert len(re.findall(r'class="subject-card" id="y\d+-\d+"', index_text)) == 70
    assert "mc-option" in index_text and "essay-question" in index_text
    assert "answer-section" in index_text


def test_sidebar_anchors_resolve():
    ids = set(re.findall(r'id="([^"]+)"', index_text))
    targets = set(re.findall(r'href="#([^"]+)"', index_text))
    missing = targets - ids
    assert not missing, f"dead sidebar links: {sorted(missing)[:5]}"
    assert len(targets) >= 60
