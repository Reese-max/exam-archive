# exam-archive

> **A single static HTML page that ships a public-domain exam / past-paper archive.**
> Repo is short on purpose: one `index.html`, GitHub Pages workflow, audit history.
> It is **not** superseded by any other repo — this **is** the canonical artifact.

## What this is

- A static `index.html` (currently ~1.35 MB) that renders the archive as a
  single long page (sections per year + category). No JavaScript
  framework, no build step.
- A GitHub Pages deployment workflow under `.github/workflows/`.
- An audit-history directory at `docs/audits/`.

## What this is NOT

- Not an interactive web app. There is no SPA, no router, no runtime data fetch.
- Not superseded by `police-exam-archive` or `police-exam-practice`. Those
  are sibling repos with different product shapes (interactive practice,
  separate topic layout). If you are looking for an interactively
  answerable question bank, go to those, **not** here.
- Not a CDN / mirror. There is one canonical copy: this repo's `main` branch.

## Status

| Asset | Source | State |
|-------|--------|-------|
| Content | Embedded inside `index.html` | Generated from upstream by hand / script — provenance chain documented below |
| Layout | Embedded inside `index.html` | Hand-curated, no build step |
| Deployment | `.github/workflows/` → GitHub Pages | Automated on push to `main` |

The 1.35 MB monolithic `index.html` is the audit's known concern.
**Splitting it into per-year / per-category chunks with lazy-loading is
a follow-up engineering task** that the audit tracked as a separate
item; it is **not** done in this README PR. The audit's PR-1 acceptance
criteria are partially addressed below.

## What is acknowledged as **not yet done**

1. **Per-year / per-category lazy-loading chunks.** The monolithic
   payload remains. A split would require either a build step
   (added complexity for no current user-reported need) or hand-splitting
   per section (large diff). The audit accepted either; this README PR
   chooses the *document-the-state* arm and leaves the split as an
   engineering work item for the same re-audit round.
2. **Build step for reproducible regeneration.** The current
   `index.html` is updated by hand against an upstream paste / mirror
   of the archive. If a future maintainer wants reproducible
   generation, a separate PR can introduce a small script
   (e.g. `build.py`) plus a `.github/workflows/release.yml`.
3. **Payload budgets.** Until #1 lands, there is no asset to budget
   against; this README is the only file that is small.

## Provenance

| Source | Where it comes from |
|--------|---------------------|
| Past-paper content | Authoritative source external to this repo; reconciled into `index.html` per the audit round. The exact reconciliation process is recorded in `docs/audits/`. |
| Layout / typography | Hand-edited alongside content updates; `git log` shows the change history. |

## Local viewing

```bash
python -m http.server 8765
# open http://localhost:8765/
```

(1.35 MB loads fast on a desktop browser; mobile / slow-network users
should expect ~1-2 second parse delay — acknowledged limitation, not
blocking.)

## Local setup

No dependencies. No build. The "build" is a one-shot save of `index.html`.

## Secrets & data hygiene

- **No secrets** in this repository. There is no `.env` and no CI
  workflow that needs one.
- **No PII**. Past-paper content is by definition not PII.
- Public-only content. If a non-public exam item is discovered during
  reconciliation, delete the corresponding section before committing.

## License & contribution

No `LICENSE` file is committed. Until one is added, all-rights-reserved
by the maintainers. PRs:

- Must cite the upstream source in the commit body when adding / updating
  content.
- Must **not** introduce a build system without first reopening this
  README.
- Must respect the policy in `docs/audits/`.
- Must pass Pages deployment cleanly (i.e. the Pages workflow must stay
  green post-merge).

## Repo map / sibling products

| Repo | What it is |
|------|-----------|
| `Reese-max/exam-archive` (this) | Static long-page archive of past papers. Read-only consumption. |
| `Reese-max/police-exam-archive` | Earlier / different layout for similar content; consult its README to decide whether to redirect here. |
| `Reese-max/police-exam-practice` | Interactive answering practice for the same content; different product shape. |

When in doubt about which repo to edit, ask: "am I adding a new
question to a practice bank, or am I restoring historical paper content
to a long-form archive?" Practice bank → `police-exam-practice`.
Historical archive → **this repo**.
