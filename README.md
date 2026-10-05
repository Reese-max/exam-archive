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
| `index.html` | Generated deployable shell with year placeholders | Never hand-edit; rebuild it |
| `src/index.template.txt` | Page shell (markup, CSS, JS) with `<!--ARCHIVE-DATA:year-NNN-->` seams | Edit for shell/UI changes |
| `src/archive-loader.js` | Dependency-free runtime loader and keyboard search shortcuts | Edit for asset loading behavior |
| `data/year-NNN.txt` | Canonical per-year archive sections (HTML fragments, LF), ROC 114→105 | Edit for content changes |
| `data/subjects/{slug}/year-NNN.txt` | Generated category/year card fragments | Rebuilt from the canonical year sources |
| `tests/rebuild_index.py` | Build step | Writes or verifies the shell and category assets |
| `tests/test_archive_contract.py`, `tests/archive_loader.test.mjs` | Executable contract | Budgets, reproducibility, request scopes, keyboard behavior |

### Build

```bash
python3 tests/rebuild_index.py           # regenerate index.html and category assets
python3 tests/rebuild_index.py --check   # verify generated files match sources
```

Sources and category assets are stored LF; the build emits CRLF for
`index.html`, matching the committed artifact's convention. The build is
deterministic and byte-exact: `tests/` verifies it.

### Test

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

CI (`.github/workflows/test.yml`) runs the Python contract suite, dependency-free
Node loader tests, the rebuild check, and a separate Chromium browser smoke on
every push to `main` and every pull request. To run the browser checks locally:

```bash
python3 -m pip install -r requirements-browser.txt
python3 -m playwright install chromium
python3 tests/browser_smoke.py
```

The five browser journeys verify first-load year scoping, keyboard search and
question expansion, mobile navigation, selected-subject loading, and reflow at
640 CSS pixels (the effective width of a 1280-pixel viewport at 200% zoom).
They serve the generated site on loopback and block optional external fonts.

## Data provenance

Content was compiled from publicly released 考選部 police special-examination
papers and embedded as HTML sections. The audits that produced this split live
in `docs/audits/` and `.github/quality-audits/`; the originating protocol is
`Reese-max/autodev-ng/docs/portfolio-audit/2026-09-06-50-persona-audit.md`.

## Payload budgets (enforced by tests)

- generated `index.html` ≤ 120,000 bytes; the archive questions are not embedded
- shell template plus `src/archive-loader.js` ≤ 120,000 bytes
- per-year chunk ≤ 160,000 bytes
- total generated category/year fragments ≤ 1,400,000 bytes; selecting one
  subject fetches only its fragments, while the year source remains canonical

## Roadmap / known gaps

- The first page request contains only the shell and loader. It fetches year
  114 so the first archive result is usable; other years load when their
  navigation, hash link, or year filter is opened.
- Subject view fetches only the selected subject's per-year fragments. A
  search without a year or subject filter loads all year chunks when the query
  is submitted so result counts remain complete.
- Category fragments are generated from `data/year-NNN.txt`; never edit those
  derived files directly. The Node checks use the built-in test runner and do
  not require a package manager or third-party JavaScript dependencies.
- Automated Chromium tests run against the candidate's local static server.
  Deployed Pages, physical-device zoom, and human screen-reader acceptance
  remain outstanding; equivalent-width reflow is not a device zoom receipt.

## Practice accessibility

Multiple-choice questions use native radio groups with question legends, visible
keyboard focus, and polite live result announcements. Only the first attempt per
source question counts toward the score, including when switching between year
and subject views. Reset clears the score and selections. Lazy-loaded years and
subjects receive the same enhancement; inactive practice controls are disabled.

Run the keyboard, accessibility-tree and scoring regression cases using:

```bash
python3 -m pip install -r requirements.txt -r requirements-browser.txt
python3 -m playwright install chromium
python3 -m pytest tests/test_practice_a11y.py -q
```

These Chromium checks do not replace a human screen-reader check on the deployed
site. That acceptance layer remains outstanding.
