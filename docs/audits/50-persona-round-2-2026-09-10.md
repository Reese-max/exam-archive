# 50-Persona Audit — Round 2

Date: 2026-09-10
Protocol: `Reese-max/autodev-ng/docs/portfolio-audit/2026-09-06-50-persona-audit.md`

> Fixed 50-persona model simulation plus current default-branch/code/CI evidence review; not 50 human participants.

## Round 2 result

Status: **P2 OPEN — NOT CLEAN**

New actionable finding is mapped to existing Issue #3: the advertised practice mode cannot be completed without a pointer because multiple-choice options are non-focusable `div.mc-option` elements activated only through `onclick`, with no native radio semantics or equivalent keyboard/assistive-technology state.

The current head before this report (`9f65299a30427e07004efc1785c150dfe99fa130`) is documentation-only on top of the audited product commit, so the practice implementation is unchanged by that head. Existing Issue #1 also remains open and therefore independently prevents CLEAN.

## Fixed-persona rerun

The same 50 persona IDs were applied to the core journey: open archive → find paper/question → enable practice mode → choose an answer → receive result → continue/review.

Core failure is reproducible for:

- G01 keyboard-only: answer options are skipped by normal focus navigation and have no keyboard activation path.
- G02 screen-reader user: option role, checked state, grouping and correctness are not exposed as form semantics.
- F03 reduced hand precision: a pointer-only custom control provides no keyboard/switch fallback.
- G04 200% zoom/narrow viewport: keyboard fallback is especially important when pointer travel/navigation becomes harder.
- A04 time-pressured candidate: cannot use a keyboard-first practice path even though practice is a primary product feature.
- B05 mobile/fragmented-use user with an unreliable pointing surface: no alternate semantic activation path exists.
- E03 low-digital-confidence user: activation failure presents as a control that cannot be reached rather than a recoverable error.
- J05 expert/shortest-path user: cannot complete rapid keyboard-driven practice.

This is **P2** under the portfolio rubric: a meaningful accessibility/interaction barrier that materially lowers completion for a recurring user cohort. It is not promoted to P1 because the read-only archive remains available and the failure is scoped to the interactive practice path for affected input/AT modes.

## Actionable issues

- #3 — `[P2][ACCESSIBILITY][UX] Make practice answers operable and announced without a pointer`
- #1 — existing repository/product-contract and monolith maintainability gap; remains open and is not duplicated here.

For #3, prefer native `fieldset`/`legend` + radio inputs/labels, or an APG-compatible radio pattern only if native controls cannot satisfy the UI. The regression gate must cover keyboard selection, programmatic names/grouping/checked state, text/announced correctness, score single-count behavior, reset and year/subject view switching.

## Runtime evidence boundary

A previously recorded Pages workflow run for the audited product revision completed successfully, which proves deployment of that artifact only. This round does **not** claim keyboard, screen-reader or assistive-technology runtime validation; no interaction/a11y test currently proves those paths.

Closure of #3 requires actual keyboard and at least one desktop browser/screen-reader smoke receipt on the deployed remediation artifact, in addition to deterministic automated interaction tests.

## CLEAN gate

1. Resolve #3 and #1 on default branch.
2. Obtain runtime evidence for keyboard-only practice and at least one screen-reader/browser pair after #3 remediation.
3. Re-run all 50 fixed personas on the current remediation SHA.
4. Require two consecutive rounds with no new P0/P1/P2.

Consecutive no-new-P0/P1/P2 count: **0/2** because Round 2 incorporates P2 #3.