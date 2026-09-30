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

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "src" / "index.template.txt"
DATA_DIR = ROOT / "data"
INDEX_PATH = ROOT / "index.html"
MARKER = re.compile(r"<!--ARCHIVE-DATA:(year-\d+)-->")


def build() -> bytes:
    """Return the bytes index.html must contain for the current sources."""
    template = TEMPLATE_PATH.read_bytes()
    if b"\r" in template:
        raise ValueError(f"{TEMPLATE_PATH.name} must be stored with LF endings")
    names = MARKER.findall(template.decode("utf-8"))
    if not names:
        raise ValueError("template carries no ARCHIVE-DATA markers")
    chunks = {}
    for path in DATA_DIR.glob("year-*.txt"):
        content = path.read_bytes()
        if b"\r" in content:
            raise ValueError(f"{path.name} must be stored with LF endings")
        chunks[path.stem] = content
    missing = [name for name in names if name not in chunks]
    orphan = [name for name in chunks if name not in names]
    if missing or orphan:
        raise ValueError(f"template/chunk mismatch: missing={missing} orphan={orphan}")
    page = template
    for name in names:
        marker = f"<!--ARCHIVE-DATA:{name}-->\n".encode()
        if page.count(marker) != 1:
            raise ValueError(f"marker {name} is not unique in template")
        page = page.replace(marker, chunks[name], 1)
    return page.replace(b"\n", b"\r\n")


def check() -> bool:
    return INDEX_PATH.is_file() and build() == INDEX_PATH.read_bytes()


def main(argv: list[str]) -> int:
    built = build()
    if "--check" in argv:
        if check():
            print(f"OK: index.html matches sources ({len(built)} bytes)")
            return 0
        print("FAIL: index.html is stale; run: python3 tests/rebuild_index.py", file=sys.stderr)
        return 1
    INDEX_PATH.write_bytes(built)
    print(f"wrote {INDEX_PATH.name}: {len(built)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
