import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import vm from 'node:vm';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const loaderSource = await readFile(join(root, 'src', 'archive-loader.js'), 'utf8');
const indexSource = await readFile(join(root, 'index.html'), 'utf8');

function createRuntime() {
  const window = {};
  vm.runInNewContext(loaderSource, { window });
  return window;
}

test('first page shell is small and requests one usable year chunk', async () => {
  const [indexStats, loaderStats] = await Promise.all([
    stat(join(root, 'index.html')),
    stat(join(root, 'src', 'archive-loader.js')),
  ]);
  assert.ok(indexStats.size < 120_000, `index.html was ${indexStats.size} bytes`);
  assert.ok(indexStats.size + loaderStats.size < 120_000, 'shell and loader exceed the first-load budget');
  assert.equal((indexSource.match(/class="year-placeholder"/g) || []).length, 10);
  assert.doesNotMatch(indexSource, /class="subject-card"/);

  const requests = [];
  const loader = createRuntime().createArchiveLoader(async url => {
    requests.push(url);
    return { ok: true, status: 200, text: async () => `<div data-asset="${url}"></div>` };
  });
  const [first, again] = await Promise.all([loader.loadYear('114'), loader.loadYear('114')]);
  assert.equal(first, again);
  assert.deepEqual(requests, ['data/year-114.txt']);
  assert.match(first, /data-asset="data\/year-114.txt"/);
});

test('year, category, and search scopes request only their declared assets', async () => {
  const requests = [];
  const loader = createRuntime().createArchiveLoader(async url => {
    requests.push(url);
    return { ok: true, status: 200, text: async () => url };
  });

  await loader.loadCategory('constitution', '113');
  assert.deepEqual(requests, ['data/subjects/constitution/year-113.txt']);
  requests.length = 0;

  const results = await loader.loadSearchScope();
  assert.equal(results.length, 10);
  assert.deepEqual(requests, ['114', '113', '112', '111', '110', '109', '108', '107', '106', '105'].map(year => `data/year-${year}.txt`));
});

test('keyboard shortcut focuses search and Escape clears it', () => {
  const { bindArchiveSearchShortcuts } = createRuntime();
  let keydown;
  let activeElement = null;
  const document = {
    addEventListener(type, handler) { if (type === 'keydown') keydown = handler; },
    get activeElement() { return activeElement; },
  };
  const input = {
    value: '',
    focus() { activeElement = input; },
    blur() { if (activeElement === input) activeElement = null; },
  };
  const cleared = [];
  bindArchiveSearchShortcuts(document, input, query => cleared.push(query));
  let prevented = false;
  keydown({ key: 'k', ctrlKey: true, target: { closest: () => null }, preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(document.activeElement, input);
  input.value = '人工智慧';
  keydown({ key: 'Escape', target: input, preventDefault() {} });
  assert.equal(input.value, '');
  assert.deepEqual(cleared, ['']);
  assert.equal(document.activeElement, null);
});

test('generated search path opens matching question cards after loading its scope', async () => {
  const inline = [...indexSource.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)?.[1];
  assert.ok(inline, 'inline page script is missing');
  new vm.Script(inline); // parse the actual generated UI script
  assert.match(inline, /ensureYearLoaded\('114'\)/);
  assert.match(inline, /Promise\.all\(ARCHIVE_YEARS\.map\(ensureYearLoaded\)\)/);
  assert.match(inline, /card\.classList\.add\('open'\)/);
  assert.match(loaderSource, /event\.key === "\/"/);
});
