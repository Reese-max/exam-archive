import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HTML = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');

async function loadPage() {
  const dom = new JSDOM(HTML, {
    url: 'https://exam-archive.test/',
    runScripts: 'dangerously',
    beforeParse(window) {
      window.matchMedia = window.matchMedia || (q => ({
        matches: false, media: q, onchange: null,
        addListener() {}, removeListener() {},
        addEventListener() {}, removeEventListener() {},
        dispatchEvent() { return false; },
      }));
      window.Element.prototype.scrollIntoView = window.Element.prototype.scrollIntoView || function () {};
      window.scrollTo = window.scrollTo || function () {};
    },
  });
  await new Promise((res, rej) => {
    const t = setTimeout(() => rej(new Error('page load timeout')), 15000);
    if (dom.window.document.readyState === 'complete') { clearTimeout(t); res(); }
    else dom.window.addEventListener('load', () => { clearTimeout(t); res(); });
  });
  return dom;
}

const fields = doc => [...doc.querySelectorAll('fieldset.mc-field')];
const radios = doc => [...doc.querySelectorAll('input.mc-radio[type=radio]')];
const score = doc => ({
  correct: +doc.getElementById('scoreCorrect').textContent,
  total: +doc.getElementById('scoreTotal').textContent,
});
const pick = (win, radio) => {
  radio.checked = true;
  radio.dispatchEvent(new win.Event('change', { bubbles: true }));
};
const letterOf = radio => radio.value;
const correctLetter = (field) => {
  const card = field.closest('.subject-card');
  const idx = +field.dataset.qidx;
  const cell = card.querySelectorAll('.answer-section .answer-cell')[idx];
  const el = cell && cell.querySelector('.q-ans');
  return el ? el.textContent.trim() : '';
};

test('every multiple-choice option becomes a radio inside a labelled fieldset group', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  const fs_ = fields(doc);
  assert.ok(fs_.length > 1000, `expected >1000 question groups, got ${fs_.length}`);

  for (const f of fs_) {
    // programmatic group label
    const legend = f.firstElementChild;
    assert.ok(legend && legend.tagName === 'LEGEND', 'fieldset missing legend');
    assert.match(legend.textContent.trim(), /第\s*\S+\s*題/);
    // every option is a <label> wrapping a radio
    const opts = [...f.querySelectorAll('.mc-option')];
    assert.ok(opts.length >= 2, 'group with <2 options');
    for (const o of opts) {
      assert.equal(o.tagName, 'LABEL');
      const r = o.querySelector('input.mc-radio[type=radio]');
      assert.ok(r, 'option missing radio input');
      assert.match(r.value, /^[A-Z]$/);
      // programmatic name: label text content
      assert.ok(o.textContent.trim().length > 0);
    }
  }
});

test('radio group names are unique per question across the whole document', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  const byName = new Map();
  for (const r of radios(doc)) {
    if (!byName.has(r.name)) byName.set(r.name, new Set());
    byName.get(r.name).add(r.closest('.mc-field'));
  }
  for (const [name, parents] of byName) {
    assert.equal(parents.size, 1, `name ${name} shared by ${parents.size} groups`);
  }
});

test('options are inert until practice mode is enabled', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  assert.ok(radios(doc).every(r => r.disabled), 'radios should be disabled before practice mode');
  assert.ok(!doc.body.classList.contains('practice-mode'));

  window.togglePractice();
  assert.ok(doc.body.classList.contains('practice-mode'));
  assert.ok(radios(doc).every(r => !r.disabled), 'radios should be enabled in practice mode');

  window.togglePractice();
  assert.ok(radios(doc).every(r => r.disabled), 'radios should be disabled after practice mode off');
});

test('first-attempt scoring: one answer counts once, re-picks do not corrupt score', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  window.togglePractice();

  const field = fields(doc)[0];
  const ans = correctLetter(field);
  assert.match(ans, /^[A-D]$/, 'test fixture card must have an answer key');
  const wrong = field.querySelector(`.mc-radio[value="${ans === 'A' ? 'B' : 'A'}"]`);
  const right = field.querySelector(`.mc-radio[value="${ans}"]`);

  pick(window, wrong);
  assert.deepEqual(score(doc), { correct: 0, total: 1 });
  const wrongLabel = wrong.closest('.mc-option');
  assert.ok(wrongLabel.classList.contains('selected'));
  assert.ok(wrongLabel.classList.contains('wrong'));
  // correct answer is revealed
  assert.ok(right.closest('.mc-option').classList.contains('correct'));
  // verdict announced in text, not CSS only
  const verdict = field.querySelector('.mc-verdict');
  assert.ok(verdict && verdict.textContent.includes('答錯'), 'verdict should say wrong');
  assert.ok(verdict.textContent.includes(ans), 'verdict should name the correct answer');
  assert.equal(verdict.getAttribute('role'), 'status');

  // re-pick the right answer: score must NOT change (first attempt policy)
  pick(window, right);
  assert.deepEqual(score(doc), { correct: 0, total: 1 });
  assert.ok(right.closest('.mc-option').classList.contains('selected'));
  assert.ok(right.closest('.mc-option').classList.contains('correct'));

  // second question, first attempt, correct → counts once more
  const field2 = fields(doc)[1];
  const ans2 = correctLetter(field2);
  pick(window, field2.querySelector(`.mc-radio[value="${ans2}"]`));
  assert.deepEqual(score(doc), { correct: 1, total: 2 });
});

test('paper without an answer key: selection is announced and never scored', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  const card = [...doc.querySelectorAll('.subject-card')].find(c => c.querySelector('.mc-option'));
  card.querySelector('.answer-section').remove(); // simulate a paper with no key

  window.togglePractice();
  const field = card.querySelector('.mc-field');
  pick(window, field.querySelector('.mc-radio'));
  assert.deepEqual(score(doc), { correct: 0, total: 0 });
  const verdict = field.querySelector('.mc-verdict');
  assert.match(verdict.textContent, /已選擇|無標準答案/);
});

test('resetScore clears radios, classes, verdicts and allows recounting', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  window.togglePractice();
  const field = fields(doc)[0];
  pick(window, field.querySelector(`.mc-radio[value="${correctLetter(field)}"]`));
  assert.deepEqual(score(doc), { correct: 1, total: 1 });

  window.resetScore();
  assert.deepEqual(score(doc), { correct: 0, total: 0 });
  assert.ok(radios(doc).every(r => !r.checked), 'radios still checked after reset');
  assert.ok([...doc.querySelectorAll('.mc-option')].every(o =>
    !o.classList.contains('selected') && !o.classList.contains('correct') && !o.classList.contains('wrong')));
  assert.ok([...doc.querySelectorAll('.mc-verdict')].every(v => v.textContent.trim() === ''));

  pick(window, field.querySelector(`.mc-radio[value="${correctLetter(field)}"]`));
  assert.deepEqual(score(doc), { correct: 1, total: 1 }, 're-answer after reset should count again');
});

test('subject view clones get unique names, working radios, and no state corruption', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  window.togglePractice();

  // answer in year view first
  const yearField = fields(doc)[0];
  pick(window, yearField.querySelector(`.mc-radio[value="${correctLetter(yearField)}"]`));
  assert.deepEqual(score(doc), { correct: 1, total: 1 });

  window.switchView('subject');
  const sv = doc.getElementById('subjectView');
  assert.ok(sv.children.length > 0, 'subject view not built');
  const svFields = [...sv.querySelectorAll('fieldset.mc-field')];
  assert.ok(svFields.length > 1000);

  // names must not collide with year view
  const yearNames = new Set(radios(doc).filter(r => r.closest('#yearView')).map(r => r.name));
  const svNames = new Set(radios(doc).filter(r => r.closest('#subjectView')).map(r => r.name));
  for (const n of svNames) assert.ok(!yearNames.has(n), `name ${n} duplicated across views`);

  // the same logical question answered in subject view must NOT double count
  const akey = yearField.dataset.akey;
  assert.ok(akey, 'fieldset should carry a stable answer key id');
  const svField = sv.querySelector(`.mc-field[data-akey="${akey}"]`);
  assert.ok(svField, 'subject view should contain a clone of the answered question');
  const before = score(doc);
  pick(window, svField.querySelector('.mc-radio'));
  assert.deepEqual(score(doc), before, 're-answering same logical question in another view must not increment score');

  // a different, unanswered question in subject view does count
  const svField2 = svField.closest('.subject-card').querySelectorAll('.mc-field')[1];
  const ans2 = correctLetter(svField2);
  pick(window, svField2.querySelector(`.mc-radio[value="${ans2}"]`));
  assert.deepEqual(score(doc), { correct: before.correct + 1, total: before.total + 1 });

  window.switchView('year');
  assert.equal(doc.getElementById('yearView').style.display, '');
});

test('toggling practice and switching views never duplicates groups, legends, handlers or verdicts', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  const baseFields = fields(doc).length;

  window.togglePractice();
  window.switchView('subject');
  window.switchView('year');
  window.togglePractice();
  window.togglePractice();
  window.switchView('subject');
  window.switchView('year');
  window.togglePractice();
  window.togglePractice();

  const yvFields = doc.querySelectorAll('#yearView fieldset.mc-field').length;
  const svFields = doc.querySelectorAll('#subjectView fieldset.mc-field').length;
  assert.equal(fields(doc).length, yvFields + svFields);
  assert.equal(yvFields, baseFields, 'year view groups must be stable across toggles');
  // subject view may legitimately hold MORE groups: a card whose title matches
  // several subject keys is cloned into each matching section (existing behavior)
  assert.ok(svFields > 0, 'subject view clones its groups');
  // every fieldset still has exactly one legend and one verdict
  for (const f of fields(doc)) {
    assert.equal([...f.children].filter(c => c.tagName === 'LEGEND').length, 1, 'duplicate legend');
    assert.equal(f.querySelectorAll('.mc-verdict').length, 1, 'duplicate verdict');
  }
  // no duplicated ids anywhere
  const ids = [...doc.querySelectorAll('[id]')].map(e => e.id);
  assert.equal(new Set(ids).size, ids.length, 'duplicate ids present');
  // reveal buttons: at most one per answer section
  for (const s of doc.querySelectorAll('.answer-section')) {
    const prev = s.previousElementSibling;
    const count = prev && prev.classList.contains('reveal-btn') ? 1 : 0;
    assert.ok(count <= 1);
    assert.ok(!prev || !prev.previousElementSibling || !prev.previousElementSibling.classList.contains('reveal-btn'), 'stacked reveal buttons');
  }
  window.togglePractice();
  assert.equal(doc.querySelectorAll('.reveal-btn').length, 0, 'reveal buttons left after practice off');
});

test('score region is a live region that announces results', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  const region = doc.getElementById('practiceScore');
  assert.equal(region.getAttribute('role'), 'status');
  assert.equal(region.getAttribute('aria-live'), 'polite');
  window.togglePractice();
  const field = fields(doc)[0];
  pick(window, field.querySelector(`.mc-radio[value="${correctLetter(field)}"]`));
  assert.equal(doc.getElementById('scoreCorrect').textContent, '1');
});

test('clicking a label selects its radio (activation path)', async () => {
  const { window } = await loadPage();
  const doc = window.document;
  window.togglePractice();
  const field = fields(doc)[0];
  const label = field.querySelector('.mc-option');
  label.dispatchEvent(new window.MouseEvent('click', { bubbles: true, cancelable: true }));
  const radio = label.querySelector('.mc-radio');
  assert.ok(radio.checked, 'label click should check the radio');
  assert.ok(label.classList.contains('selected'));
});
