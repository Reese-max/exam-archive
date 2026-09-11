// Payload 預算閘門（issue #1）：在 index.html 拆分為 per-year/per-category
// chunks 之前，先釘住首載體積不得再長。拆完後調低門檻。
import { statSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
// 目前 index.html ~1.35MB；預算留 ~10% 緩衝，split 落地後應降到 < 300KB
const INDEX_MAX = 1.5 * 1024 * 1024;
const TOTAL_MAX = 6 * 1024 * 1024; // 整站資產總量

const indexSize = statSync(join(ROOT, "index.html")).size;
const total = readdirSync(ROOT, { recursive: true })
  .filter((f) => !String(f).startsWith(".git") && !String(f).startsWith("node_modules"))
  .reduce((sum, f) => {
    try { return sum + statSync(join(ROOT, f)).size; } catch { return sum; }
  }, 0);

const fails = [];
if (indexSize > INDEX_MAX) fails.push(`index.html ${(indexSize / 1e6).toFixed(2)}MB > ${INDEX_MAX / 1e6}MB 預算`);
if (total > TOTAL_MAX) fails.push(`整站 ${(total / 1e6).toFixed(1)}MB > ${TOTAL_MAX / 1e6}MB 預算`);

if (fails.length) {
  for (const f of fails) console.error(`BUDGET_FAIL ${f}`);
  process.exit(1);
}
console.log(`BUDGET_OK index.html=${(indexSize / 1e6).toFixed(2)}MB total=${(total / 1e6).toFixed(1)}MB`);
