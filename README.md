# 資管系考古題總覽 (exam-archive)

單一檔案靜態網站（`index.html`），收錄警察特考三等 105–114 年共 70 份試卷，
提供搜尋、年份/科目雙檢視、書籤與練習模式。透過 GitHub Pages 部署。

## 練習模式的無障礙結構（option component contract）

選擇題選項在頁面載入時由 `enhanceMcGroups()` 漸進增強為原生表單語意：

```html
<fieldset class="mc-field" data-qidx="0" data-qnum="1" data-akey="y114-38157-q0">
  <legend class="sr-only">第1題：<題幹></legend>
  <label class="mc-option">
    <input type="radio" class="mc-radio" name="mcq-N" value="A">
    <span class="opt-label">(A)</span><span class="opt-text">…</span>
  </label>
  …
  <div class="mc-verdict" role="status" aria-live="polite"></div>
</fieldset>
```

- 分組沿用原計分規則：每張 `.subject-card` 內遇到 `(A)` 另起新題組
  （部分試卷題幹內嵌於選項文字，無 `.mc-question`，legend 退回「第N題」）。
- radio `name` 每題組全文件唯一；科目檢視的 innerHTML clone 會由
  `fixupClonedMcGroups()` 重新命名並依 `.selected` 補回 `checked`。
- `data-akey`（cardId-qidx）在跨檢視複製間維持同一題身份，
  保證首次作答計分一次（first-attempt policy）。
  原生 radio 群組的方向鍵會同時移動焦點並選取（APG 語意），
  因此以方向鍵掠過的選項即為首次作答、計分一次。
- 不使用任何 `id`，clone 不會產生重複 id。
- 非練習模式下 radio `disabled`（不進 Tab 序）；練習模式啟用。
- 作答結果同時寫入可見文字 `.mc-verdict`（live region 會播報）與
  `.practice-score`（`role="status"`）。
- 事件採 `document` 層委派（`change` / `.reveal-btn` click），
  clone 節點不需重新綁定、切換檢視或練習模式不會重複掛 handler。

## 測試

```bash
pip install -r requirements.txt
python3 -m playwright install chromium   # 首次需要下載瀏覽器
python3 -m pytest -q                     # 真實 Chromium：鍵盤操作 / 語意 / 計分 / 重置 / 檢視切換 / AX tree
```

測試以 Playwright 驅動 headless Chromium 載入 `index.html`，
模擬真實鍵盤（focus、Space、方向鍵）與 label 點擊，
並經由 CDP `Accessibility.queryAXTree` 檢查輔助科技樹，
產出寫入 `tests/artifacts/`。
