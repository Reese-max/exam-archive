"""Build step: regenerate index.html from the shell template + per-year chunks.

Sources (stored with LF line endings):
  src/index.template.txt  page shell; each <!--ARCHIVE-DATA:year-NNN--> line is
                          the seam where that year's archive section is inserted
  data/year-NNN.txt       per-year archive sections, newest first

The committed artifact (index.html) uses CRLF line endings, so build() converts
the assembled LF document back to CRLF and the output is byte-identical.

Usage:
  python3 tests/rebuild_index.py           regenerate index.html in place
  python3 tests/rebuild_index.py --check   verify only; exit 1 if stale
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "src" / "index.template.txt"
DATA_DIR = ROOT / "data"
SUBJECT_DIR = DATA_DIR / "subjects"
INDEX_PATH = ROOT / "index.html"
MARKER = re.compile(r"<!--ARCHIVE-DATA:(year-\d+)-->")
CARD_START = re.compile(rb'<div class="subject-card" id="y\d+-\d+">')
DIV_TAG = re.compile(rb"</?div\b[^>]*>", re.IGNORECASE)
CARD_TITLE = re.compile(rb"<h3>(.*?)</h3>", re.DOTALL)
TAG = re.compile(rb"<[^>]+>")
SUBJECTS = {
    "constitution": "中華民國憲法",
    "chinese": "國文",
    "digital-forensics": "數位鑑識執法",
    "police-scenario": "警察情境實務",
    "police-law": "警察法規",
    "police-information": "警政資訊管理",
    "cybercrime": "電腦犯罪偵查",
}


def extract_cards(path: Path) -> list[tuple[str, bytes]]:
    """Return (subject slug, exact card bytes) pairs from one year source."""
    source = path.read_bytes()
    if b"\r" in source:
        raise ValueError(f"{path.name} must be stored with LF endings")
    cards = []
    for start in CARD_START.finditer(source):
        depth = 0
        end = None
        for tag in DIV_TAG.finditer(source, start.start()):
            if tag.group().startswith(b"</"):
                depth -= 1
            else:
                depth += 1
            if depth == 0:
                end = tag.end()
                break
        if end is None:
            raise ValueError(f"unclosed subject card in {path.name}")
        card = source[start.start():end]
        title_match = CARD_TITLE.search(card)
        if not title_match:
            raise ValueError(f"subject card has no h3 title in {path.name}")
        title = html.unescape(TAG.sub(b"", title_match.group(1)).decode("utf-8"))
        matches = [slug for slug, label in SUBJECTS.items() if title.startswith(label)]
        if len(matches) != 1:
            raise ValueError(f"cannot uniquely classify subject card {title!r} in {path.name}")
        cards.append((matches[0], card))
    if len(cards) != len(SUBJECTS):
        raise ValueError(f"expected {len(SUBJECTS)} subject cards in {path.name}, found {len(cards)}")
    return cards


def generated_subject_assets() -> dict[Path, bytes]:
    """Create category/year assets derived byte-for-byte from the year sources."""
    assets = {}
    for year_path in sorted(DATA_DIR.glob("year-*.txt")):
        year = year_path.stem.removeprefix("year-")
        for slug, card in extract_cards(year_path):
            assets[Path("data") / "subjects" / slug / f"year-{year}.txt"] = card + b"\n"
    expected = len(list(DATA_DIR.glob("year-*.txt"))) * len(SUBJECTS)
    if len(assets) != expected:
        raise ValueError(f"expected {expected} category/year assets, generated {len(assets)}")
    return assets


def build() -> bytes:
    """Return the bytes index.html must contain for the current sources."""
    template = TEMPLATE_PATH.read_bytes()
    if b"\r" in template:
        raise ValueError(f"{TEMPLATE_PATH.name} must be stored with LF endings")
    names = MARKER.findall(template.decode("utf-8"))
    if not names:
        raise ValueError("template carries no ARCHIVE-DATA markers")
    chunks = {path.stem: path for path in DATA_DIR.glob("year-*.txt")}
    missing = [name for name in names if name not in chunks]
    orphan = [name for name in chunks if name not in names]
    if missing or orphan:
        raise ValueError(f"template/chunk mismatch: missing={missing} orphan={orphan}")
    page = template
    for name in names:
        marker = f"<!--ARCHIVE-DATA:{name}-->\n".encode()
        if page.count(marker) != 1:
            raise ValueError(f"marker {name} is not unique in template")
        year = name.removeprefix("year-")
        placeholder = (
            f'<section class="year-placeholder" id="{name}" data-year="{year}" '
            f'aria-live="polite"><h2 class="year-heading">民國 {year} 年</h2>'
            f'<p>此年度考題尚未載入。<button type="button" onclick="ensureYearLoaded(\'{year}\')">'
            f'載入考題</button></p></section>\n'
        ).encode("utf-8")
        page = page.replace(marker, placeholder, 1)
    return page.replace(b"\n", b"\r\n")


def check() -> bool:
    if not INDEX_PATH.is_file() or build() != INDEX_PATH.read_bytes():
        return False
    expected = generated_subject_assets()
    actual_paths = {path.relative_to(ROOT) for path in SUBJECT_DIR.rglob("*.txt")} if SUBJECT_DIR.exists() else set()
    if actual_paths != set(expected):
        return False
    return all((ROOT / path).is_file() and (ROOT / path).read_bytes() == content for path, content in expected.items())


def main(argv: list[str]) -> int:
    built = build()
    if "--check" in argv:
        if check():
            print(f"OK: shell and category assets match sources ({len(built)} bytes, {len(generated_subject_assets())} category/year assets)")
            return 0
        print("FAIL: generated shell or category assets are stale; run: python3 tests/rebuild_index.py", file=sys.stderr)
        return 1
    generated = generated_subject_assets()
    INDEX_PATH.write_bytes(built)
    for path, content in generated.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    expected_paths = set(generated)
    if SUBJECT_DIR.exists():
        for stale in SUBJECT_DIR.rglob("*.txt"):
            if stale.relative_to(ROOT) not in expected_paths:
                stale.unlink()
        for directory in sorted((p for p in SUBJECT_DIR.rglob("*") if p.is_dir()), reverse=True):
            if not any(directory.iterdir()):
                directory.rmdir()
    print(f"wrote {INDEX_PATH.name}: {len(built)} bytes; generated {len(generated)} category/year assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
