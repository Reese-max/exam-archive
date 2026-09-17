// Real-browser keyboard + accessibility evidence for issue #3.
// Drives system Chrome via playwright-core. Run: npm run test:e2e
// Env: CHROME_PATH overrides the Chrome binary lookup.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ARTIFACTS = path.join(ROOT, 'tests', 'artifacts');
fs.mkdirSync(ARTIFACTS, { recursive: true });

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
].filter(Boolean);
const chromePath = CHROME_CANDIDATES.find(p => fs.existsSync(p));

let passed = 0, failed = 0;
function check(name, cond, extra = '') {
  if (cond) { passed++; console.log(`  PASS ${name}`); }
  else { failed++; console.log(`  FAIL ${name} ${extra}`); }
}

if (!chromePath) {
  console.log('SKIP: no Chrome/Chromium binary found (set CHROME_PATH).');
  process.exit(0);
}
console.log(`Using browser: ${chromePath}`);

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
  args: ['--no-sandbox', '--disable-gpu'],
});
try {
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('  [pageerror]', e.message));
  await page.goto('file://' + path.join(ROOT, 'index.html'), { waitUntil: 'load' });
  await page.waitForSelector('fieldset.mc-field input.mc-radio', { state: 'attached' });

  // --- 1. Enter practice mode by keyboard only ---
  await page.focus('#practiceToggle');
  await page.keyboard.press('Enter');
  check('practice mode on via keyboard Enter', await page.evaluate(() =>
    document.body.classList.contains('practice-mode')));

  // --- 2. Open the first card by keyboard (Enter on the header) ---
  const firstCard = page.locator('#yearView .subject-card').first();
  await firstCard.locator('.subject-header').first().focus();
  await page.keyboard.press('Enter');
  check('card opened via keyboard Enter', await firstCard.evaluate(c => c.classList.contains('open')));

  // --- 3. Focus a radio, operate it by keyboard ---
  const firstField = firstCard.locator('fieldset.mc-field').first();
  const meta = await firstField.evaluate(f => {
    const card = f.closest('.subject-card');
    const cell = card.querySelectorAll('.answer-section .answer-cell')[+f.dataset.qidx];
    return { qnum: f.dataset.qnum, correct: cell.querySelector('.q-ans').textContent.trim() };
  });
  const radios = firstField.locator('input.mc-radio');
  // focus a radio known to be WRONG, then press Space to select
  const wrongIdx = meta.correct === 'A' ? 1 : 0;
  const wrongLetter = String.fromCharCode(65 + wrongIdx);
  await radios.nth(wrongIdx).focus();
  await page.keyboard.press(' ');
  check('radio checked via Space', await radios.nth(wrongIdx).isChecked());
  const verdict1 = await firstField.locator('.mc-verdict').textContent();
  check('verdict announces wrong + correct answer',
    verdict1.includes('答錯') && verdict1.includes(meta.correct), verdict1);
  const score1 = await page.locator('#scoreTotal').textContent();
  check('score total is 1 after first answer', score1 === '1', score1);

  // --- 4. Arrow keys move selection inside the group; score must not recount ---
  await page.keyboard.press('ArrowDown'); // moves to next radio and selects it
  const checkedIdx = await firstField.evaluate(f =>
    [...f.querySelectorAll('input.mc-radio')].findIndex(r => r.checked));
  check('ArrowDown moved selection within group', checkedIdx === (wrongIdx + 1) % 4, `checkedIdx=${checkedIdx}`);
  const score2 = await page.locator('#scoreTotal').textContent();
  check('re-pick via arrow key does not double count', score2 === '1', score2);

  // --- 5. Tab leaves the whole group in one stop ---
  await page.keyboard.press('Tab');
  const outside = await firstField.evaluate(f => !f.contains(document.activeElement));
  check('Tab leaves the radio group (single tab stop)', outside);

  // --- 6. Selected state + names exposed in the AT tree (CDP) ---
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Accessibility.enable').catch(() => {});
  const { nodes } = await cdp.send('Accessibility.getFullAXTree');
  const legendText = await firstField.locator('legend').textContent();
  const groupNode = nodes.find(n =>
    (n.name?.value || '').includes(legendText.trim().slice(0, 20)));
  const radioNodes = nodes.filter(n => /radio/i.test(n.role?.value || ''));
  const checkedRadio = radioNodes.find(n =>
    n.properties?.some(p => p.name === 'checked' && (p.value?.value === true || p.value?.value === 'true')));
  check('fieldset group has an accessible name in the AX tree', !!groupNode,
    `legend="${legendText.trim().slice(0, 30)}…"`);
  check('AX tree exposes radio controls', radioNodes.length > 0, `found ${radioNodes.length}`);
  check('AX tree exposes a checked radio (selected state)', !!checkedRadio);
  fs.writeFileSync(path.join(ARTIFACTS, 'at-smoke.json'), JSON.stringify({
    groupName: groupNode?.name?.value || null,
    radioCount: radioNodes.length,
    checkedRadioName: checkedRadio?.name?.value || null,
    sampleRadios: radioNodes.slice(0, 4).map(n => ({
      name: n.name?.value, checked: n.properties?.find(p => p.name === 'checked')?.value?.value,
    })),
  }, null, 2));

  // --- 6. Automated a11y check (axe-core) scoped to the practice semantics ---
  const axePath = path.join(ROOT, 'node_modules', 'axe-core', 'axe.min.js');
  if (fs.existsSync(axePath)) {
    await page.addScriptTag({ path: axePath });
    const results = await page.evaluate(async () => {
      const res = await window.axe.run(document, {
        resultTypes: ['violations'],
      });
      const isOurs = v => v.nodes.some(n =>
        n.target.some(t => /mc-(field|option|radio|verdict)|practice-score|reveal-btn/.test(t)));
      return {
        ours: res.violations.filter(v => isOurs(v) && ['critical', 'serious'].includes(v.impact)),
        otherCount: res.violations.filter(v => !isOurs(v)).length,
      };
    });
    check('0 critical/serious axe violations on question/option semantics',
      results.ours.length === 0, JSON.stringify(results.ours.map(v => v.id)));
    console.log(`  (pre-existing unrelated violations: ${results.otherCount})`);
  } else {
    console.log('  (axe-core not installed; skipped automated a11y check)');
  }

  // --- 7. Subject view: same keyboard operability ---
  await page.focus('#viewBySubject');
  await page.keyboard.press('Enter');
  await page.waitForSelector('#subjectView fieldset.mc-field input.mc-radio', { state: 'attached' });
  // first fieldset is the clone of the question already answered in year view
  // (same data-akey) — answering the SECOND question proves subject view works.
  const svField = page.locator('#subjectView fieldset.mc-field').nth(1);
  const svCorrect = await svField.evaluate(f => {
    const cell = f.closest('.subject-card')
      .querySelectorAll('.answer-section .answer-cell')[+f.dataset.qidx];
    return cell.querySelector('.q-ans').textContent.trim();
  });
  await svField.locator(`input.mc-radio[value="${svCorrect}"]`).focus();
  await page.keyboard.press(' ');
  check('subject view radio selectable by keyboard',
    await svField.locator(`input.mc-radio[value="${svCorrect}"]`).isChecked());
  const score3 = await page.evaluate(() => ({
    c: +document.getElementById('scoreCorrect').textContent,
    t: +document.getElementById('scoreTotal').textContent,
  }));
  check('subject view correct answer increments once', score3.t === 2 && score3.c === 1,
    JSON.stringify(score3));

  // --- 8. Reset by keyboard clears everything ---
  await page.focus('.score-reset');
  await page.keyboard.press('Enter');
  check('reset clears score', (await page.locator('#scoreTotal').textContent()) === '0');
  check('reset unchecks all radios', await page.evaluate(() =>
    [...document.querySelectorAll('input.mc-radio')].every(r => !r.checked)));

  await firstField.screenshot({ path: path.join(ARTIFACTS, 'fieldset.png') }).catch(() => {});
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exitCode = failed ? 1 : 0;
} finally {
  await browser.close();
}
