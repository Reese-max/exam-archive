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
LOADER = ROOT / "src" / "archive-loader.js"

INDEX_BUDGET_BYTES = 120_000     # generated page shell; archive content is fetched separately
SHELL_BUDGET_BYTES = 120_000     # page shell plus its small loader
CHUNK_BUDGET_BYTES = 160_000     # per-year lazy-load granule
SUBJECT_CHUNK_BUDGET_BYTES = 60_000
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
        assert len(re.findall(rb'class="subject-card" id="y\d+-\d+"', frag)) == 7


def test_first_load_asset_budget():
    assert len(index_bytes) <= INDEX_BUDGET_BYTES
    assert len(TEMPLATE.read_bytes()) + len(LOADER.read_bytes()) <= SHELL_BUDGET_BYTES
    # Shell carries year placeholders only; one explicit loader fetch is initiated at startup.
    assert b"class=\"subject-card\"" not in index_bytes
    assert len(re.findall(rb'class="year-placeholder" id="year-\d+"', index_bytes)) == len(YEARS_DESC)
    local_scripts = [src for src in re.findall(rb'<script[^>]+src="([^"]+)"', index_bytes) if not src.startswith(b"https://")]
    assert local_scripts == [b"src/archive-loader.js"]
    for href in re.findall(rb'<link[^>]+href="([^"]+)"', index_bytes):
        assert href.startswith(b"https://"), href
    for src in re.findall(rb'src="([^"]+)"', index_bytes):
        assert src.startswith(b"https://") or src == b"src/archive-loader.js", src


def test_shell_and_chunk_budgets():
    assert len(TEMPLATE.read_bytes()) <= SHELL_BUDGET_BYTES
    chunks = list(DATA_DIR.glob("year-*.txt"))
    assert len(chunks) == len(YEARS_DESC)
    for path in chunks:
        assert len(path.read_bytes()) <= CHUNK_BUDGET_BYTES, path.name
    assets = rebuild_index.generated_subject_assets()
    assert len(assets) == len(YEARS_DESC) * len(rebuild_index.SUBJECTS)
    for path, content in assets.items():
        assert len(content) <= SUBJECT_CHUNK_BUDGET_BYTES, path
    for slug in rebuild_index.SUBJECTS:
        assert sum(len(content) for path, content in assets.items() if path.parts[2] == slug) <= 600_000
    assert sum(len(content) for content in assets.values()) < 1_400_000
    assert all((ROOT / path).read_bytes() == content for path, content in assets.items())


def test_first_load_loader_and_requested_search_scopes():
    source = LOADER.read_bytes().decode("utf-8")
    assert "loadYear(year)" in source
    assert "loadCategory(slug, year)" in source
    assert "loadSearchScope()" in source
    assert "data/year-${value}.txt" in source
    assert "data/subjects/${slug}/year-${value}.txt" in source
    assert "bindArchiveSearchShortcuts" in source


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
    loader = LOADER.read_bytes().decode("utf-8")
    assert 'event.key === "/"' in loader      # '/' focuses search
    assert 'event.key === "Escape"' in loader
    assert "window.bindArchiveSearchShortcuts" in index_text


def test_zoom_200_percent_smoke():
    viewport = re.search(r'<meta name="viewport" content="([^"]+)"', index_text).group(1)
    assert "maximum-scale" not in viewport and "user-scalable" not in viewport
    assert index_text.count("rem") > 50  # fluid rem-based layout reflows at 200%


def test_search_open_question_smoke():
    assert 'id="searchInput"' in index_text
    assert "function doSearch(" in index_text
    assert "function toggleCard(" in index_text
    assert "ensureYearLoaded(activeYearFilter)" in index_text
    assert "classList.add('open')" in index_text
    archive = b"".join(path.read_bytes() for path in DATA_DIR.glob("year-*.txt")).decode("utf-8")
    assert len(re.findall(r'class="subject-card" id="y\d+-\d+"', archive)) == 70
    assert "mc-option" in archive and "essay-question" in archive
    assert "answer-section" in archive


def test_sidebar_anchors_resolve():
    targets = set(re.findall(r'href="#([^"]+)"', index_text))
    archive = b"".join(path.read_bytes() for path in DATA_DIR.glob("year-*.txt")).decode("utf-8")
    ids = set(re.findall(r'id="([^"]+)"', index_text)) | set(re.findall(r'id="([^"]+)"', archive))
    missing = targets - ids
    assert not missing, f"dead sidebar links: {sorted(missing)[:5]}"
    assert len(targets) >= 60
