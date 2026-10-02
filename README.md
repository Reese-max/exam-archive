# 資管系考古題總覽

This single-file GitHub Pages site collects the police examination archive and provides search, year/subject views, bookmarks, and practice mode.

## Practice-mode accessibility contract

When the page loads, multiple-choice options are progressively enhanced into native radio groups:

- each question is a `fieldset.mc-field` with a visually hidden `legend` containing the question number and stem;
- each option is a labelled `input.mc-radio[type="radio"]`, with one unique radio name per question;
- radios stay disabled outside practice mode and use native Space/arrow-key behavior when practice mode is enabled;
- each group has a `role="status"` / `aria-live="polite"` verdict with text for correct, incorrect, and papers without an answer key;
- the practice score is also a polite live status;
- delegated change handling works for both year-view markup and subject-view clones, while stable `data-akey` values preserve the first-attempt scoring policy across views;
- reset clears radio, visual, verdict, and score state; toggling views or practice mode does not add duplicate groups or handlers.

The enhancement does not add IDs to cloned question controls, so subject-view cloning cannot create duplicate IDs. Existing subject headers retain their keyboard and expanded-state behavior.

## Tests

```bash
python3 -m pytest -q
```

The suite drives the local artifact in Chromium and covers keyboard activation, native radio semantics, arrow navigation, announcements, first-attempt scoring, reset, subject-view cloning, lifecycle toggles, and the browser accessibility tree. A desktop screen-reader smoke check should still be performed against the deployed page before release; this repository does not bundle a screen reader runtime.
