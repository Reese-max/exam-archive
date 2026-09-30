# 資管系考古題總覽 — exam-archive

Static archive of 警察特考三等資訊管理組 (Police Special Examination, Level 3,
Information Management) past papers: ROC years 105–114, 7 subjects, 70 papers,
126 referenced PDFs, ~4,700 questions with answers.

## Status

**Active and maintained.** This repository is the source of truth for the
archive and is **not superseded** by any other repository. If that ever changes,
this section becomes the redirect notice.

## Canonical public URL

<https://reese-max.github.io/exam-archive/> — deployed from the repo root by
`.github/workflows/pages.yml` (GitHub Pages).

## Repository contract

| Path | Role | Rule |
|---|---|---|
| `index.html` | Generated deployable artifact | Never hand-edit; rebuild it |
| `src/index.template.txt` | Page shell (markup, CSS, JS) with `<!--ARCHIVE-DATA:year-NNN-->` seams | Edit for shell/UI changes |
| `data/year-NNN.txt` | Per-year archive sections (HTML fragments, LF), ROC 114→105 | Edit for content changes |
| `tests/rebuild_index.py` | Build step | Writes or verifies `index.html` |
| `tests/test_archive_contract.py` | Executable contract | Budgets, reproducibility, smoke tests |

### Build

```bash
python3 tests/rebuild_index.py           # regenerate index.html
python3 tests/rebuild_index.py --check   # verify index.html matches sources
```

Sources are stored LF; the build emits CRLF, matching the committed artifact's
convention. The build is deterministic and byte-exact: `tests/` verifies it.

### Test

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

CI (`.github/workflows/test.yml`) runs the contract suite and the rebuild
check on every push to `main` and every pull request.

## Data provenance

Content was compiled from publicly released 考選部 police special-examination
papers and embedded as HTML sections. The audits that produced this split live
in `docs/audits/` and `.github/quality-audits/`; the originating protocol is
`Reese-max/autodev-ng/docs/portfolio-audit/2026-09-06-50-persona-audit.md`.

## Payload budgets (enforced by tests)

- `index.html` ≤ 1,400,000 bytes — ratchet ceiling at the current size; may
  only shrink from here
- shell template ≤ 120,000 bytes — this becomes the first-load payload once
  chunks lazy-load
- per-year chunk ≤ 160,000 bytes — keeps each lazy-load granule small

## Roadmap / known gaps

- The 1.32 MiB monolith is now *separated* — per-year chunks are the source of
  truth and `index.html` is reproducibly generated from them — but not yet
  *lazy-loaded*. Because the chunks deploy with the site as static assets,
  switching the runtime to fetch `data/year-*.txt` on demand is a front-end
  follow-up that needs no layout change.
- No JavaScript toolchain is vendored; verification is pytest plus static
  contract assertions against the generated artifact.
