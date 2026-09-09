# Product Board Audit — exam-archive

**Audit date:** 2026-09-09 (Asia/Taipei)  
**Repository:** `Reese-max/exam-archive`  
**Audited default branch:** `main@09fd79761285c1d8fd66571125a34416165156da`  
**Evidence mode:** repository/code/CI inspection plus current public-source comparison. No human study, no authenticated production session, and no assistive-technology Runtime session were performed.

## Executive Summary

`exam-archive` is a public, static, local-first archive for Taiwan police third-class information-management past papers covering 105–114, with search, year/subject views, bookmarks, print support, and a pointer-driven practice mode. It is small operationally but not physically: the product and data are concentrated in a single ~1.35 MB `index.html`.

This round found one new independent Quality-Gate finding: the core multiple-choice practice journey is pointer-only because `.mc-option` elements are non-focusable `div` controls wired only with `onclick`, with no native radio or equivalent ARIA state. The finding is mapped to [#3](https://github.com/Reese-max/exam-archive/issues/3).

Existing [#1](https://github.com/Reese-max/exam-archive/issues/1) remains reproducible on `main` (no root README, monolithic artifact, no reproducible build/budget). It was not modified because [PR #2](https://github.com/Reese-max/exam-archive/pull/2) and branch `docs/issue-1-root-readme` are active. The PR is partial and its draft README describes the artifact as “not an interactive web app,” while the audited `index.html` exposes search, bookmarks, view switching and practice scoring. This is recorded as **SKIPPED_LOCKED**, not counted as a new finding and not written into the active thread.

**Decision:** **SIMPLIFY / MAINTAIN.** Fix practice accessibility, finish one truthful repository/product contract, then decide whether this archive and `police-exam-archive` should share a generated data layer or converge. Do not add AI tutoring, accounts, analytics, a native app, or a teacher LMS here.

## Project Discovery

| Dimension | Finding | Evidence level | Verification class |
|---|---|---|---|
| Product type | Public static exam archive with optional local practice behavior | CONFIRMED | Code |
| Target users | Police information-management exam candidates; secondary users are teachers and maintainers | LIKELY | Product copy + static inference |
| Core task | Find a year/subject/question, study it, optionally answer MCQs and review score | CONFIRMED | Code |
| Value | Narrow corpus, no login, no backend, searchable single-file portability | CONFIRMED | Code |
| Maturity | Working published artifact; maintenance contract/build/test system immature | CONFIRMED | Repo + CI |
| Data scope | 105–114, 7 subjects, 70 papers, 126 PDFs claimed in UI | CONFIRMED as UI claim | Runtime/data reconciliation pending |
| Architecture | One 1,348,222-byte HTML artifact plus one Pages workflow | CONFIRMED | Git tree |
| Persistence | Bookmarks/theme/practice history use browser localStorage | CONFIRMED | Code |
| CI/CD | Push-to-main GitHub Pages deployment only | CONFIRMED | Workflow |
| Latest CI | Pages run 33989284229 succeeded for audited SHA | CONFIRMED | CI |
| Tests | No test files or interaction/a11y gate on main | CONFIRMED | Git tree |
| License/source contract | No LICENSE or root README on main; active PR #2 attempts partial documentation | CONFIRMED / LOCKED | Repo + PR |
| Largest weakness | Core practice answer controls are pointer-only and unannounced | CONFIRMED | Code; Runtime fix verification required |

### Code/CI evidence

- `index.html` is 1,348,222 bytes in Git and decodes to about 993 KB of UTF-8 text across roughly 10,502 lines.
- It contains search, highlighting, year filters, hash navigation, subject-view DOM cloning, practice scoring, bookmarks, progress summary and dark mode.
- `togglePractice()` assigns `opt.onclick = handleOptionClick` to `.mc-option`.
- The code deliberately adds role/tabindex/Enter/Space support to sidebar years and subject headers but not answer options.
- No `input[type=radio]`, `role="radio"`, `radiogroup`, `aria-checked`, or option focus management appears.
- [Pages workflow](https://github.com/Reese-max/exam-archive/blob/09fd79761285c1d8fd66571125a34416165156da/.github/workflows/pages.yml) deploys `.` on every push to main; it does not build or test interactions.
- [Latest audited Pages run](https://github.com/Reese-max/exam-archive/actions/runs/33989284229) succeeded. This confirms deployment, not usability or accessibility.

## Competitive Intelligence

Public product/source capabilities were rechecked on **2026-09-09**:
[MOEX past-paper platform](https://wwwq.moex.gov.tw/), [MOEX reuse statement](https://wwwc.moex.gov.tw/main/content/wfrmContent.aspx?menu_id=1189), [Yamol current police-IT papers](https://yamol.tw/latest-1783217973.htm), [Quizlet Learn](https://help.quizlet.com/hc/en-us/articles/360030986971-Studying-with-Learn), [Quizlet Test](https://help.quizlet.com/hc/en-us/articles/360030642972-Studying-with-Test), [Anki manual](https://docs.ankiweb.net/studying.html), and [W3C radio pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/).

| Dimension | exam-archive | MOEX official | Yamol | police-exam-practice | Quizlet | Anki |
|---|---|---|---|---|---|---|
| Target user | Police IT candidate | All Taiwan examinees | Broad exam candidates | Same portfolio's interactive exam users | General learners/classes | Self-directed spaced-repetition users |
| Value proposition | Narrow, free, no-login archive + light practice | Authoritative source/PDF | Large current question bank + community | Canonical interactive practice entry | Polished multi-mode study | Powerful offline/cross-device SRS |
| Killer feature | All 10 years searchable in one local-first page | Authority/freshness | Breadth and latest papers | Focused quiz flow | Personalized Learn/Test | Scheduling and extensibility |
| Onboarding | Immediate, but repo contract missing on main | Search form | Login prompts around richer use | Redirects to canonical quiz | Account/plan boundaries | Installation/deck setup |
| Search/browse | Full-text, year, subject | Exam/category filters | Topic/exam navigation | Question-oriented | Set-based | Deck/browser search |
| Practice | Pointer-only MCQ mode; local score | Mostly document retrieval | Online questions/community | Interactive exam path | Learn/Test | Card review/SRS |
| Progress | Local summary only | None | Account-backed | Product-specific | Account-backed | Local + optional sync |
| Mobile | Responsive static page | Responsive web/PDF constraints | Web/mobile | Web | Web/apps | Apps |
| Offline | Strong after load/saved file | PDF download | Limited/UNKNOWN | UNKNOWN | App/plan dependent | Strong |
| Reliability | No backend; one large artifact | High authority | Service dependent | Portfolio dependency | SaaS | Local-first + sync |
| Security/privacy | No account; localStorage | Government site | Account/service | Separate repo | SaaS account | Local collection + optional sync |
| Pricing | Free | Free | Freemium/UNKNOWN exact current terms | Free portfolio product | Freemium/Plus | Core desktop free; mobile varies |
| Open source | Public code, no LICENSE on main | Public documents, reuse conditions apply | Closed service | Public repo | Closed service | Open ecosystem |
| Community | None | Institutional | Strong local exam community | Portfolio only | Large | Large |
| Documentation | Missing on main; active PR | Official help | Product pages | Sibling repo | Extensive help | Extensive manual |
| Distribution | GitHub Pages | Government search | Search/brand | GitHub Pages | Web/app stores | Desktop/mobile/ecosystem |
| Common advantage | Zero login and narrow scope | Correctness/provenance | Currency and breadth | Better practice fit | Adaptive modes | Durable personal study |
| Common weakness | Monolith, stale ceiling, inaccessible practice | PDF-heavy | Ads/account/service dependence | Smaller corpus | Subscription/account | Setup complexity |

### Gap classification

- **MUST MATCH:** keyboard/assistive-tech operability for the practice task; truthful product contract; source/version traceability; current deployment health.
- **SHOULD BE BETTER:** no-login privacy, narrow police-IT navigation, local-first access, shareable stable anchors, lightweight print.
- **DIFFERENTIATOR:** a curated 10-year police-IT archive that remains useful without an account or server.
- **DO NOT COPY:** broad user-generated marketplace, classroom administration, social/community mechanics, general-purpose SRS engine, AI answer generation, ad/analytics stack.

## Competitive Gaps

1. **Practice operability (MUST MATCH):** competitors treat answering as a real form interaction; this product exposes pointer-only answer choices.
2. **Currency/provenance (MUST MATCH, already under #1/active PR):** MOEX and Yamol expose 115-year material; this archive explicitly stops at 114 and lacks a main-branch update/source contract.
3. **Adaptive study (DO NOT COPY here):** Quizlet/Anki win at adaptive repetition, but duplicating them would turn a reliable archive into another learning platform. Route that need to the sibling practice product.
4. **Local-first privacy (SHOULD BE BETTER):** no account/backend is a meaningful strength worth preserving.
5. **Portfolio clarity (SHOULD BE BETTER):** `exam-archive`, `police-exam-archive`, and `police-exam-practice` need one user-facing boundary and shared source-of-truth decision.

## Virtual Executive Board

| Role | Independent question | Opportunity | Priority | Boundary |
|---|---|---|---|---|
| CEO | 此 repo 是 archive 還是 practice product？三個同族 repo 是否有單一入口？ | 保留窄領域、零登入、單檔可攜優勢 | 1) 修 #3；2) 完成 #1 的真實產品契約；3) 定義 sibling canonical routing | 不做 AI tutor、帳號、社群或教師後台 |
| CPO | 練習 CTA 是否對所有人真的可完成？ | 把唯讀 archive 與可作答 practice 明確分層 | 先修可操作性，再討論新學習功能 | 反對以功能數量追 Quizlet |
| CTO | 單一 1.35MB HTML 如何安全維護與測試？ | 原生 control 可減少自製事件狀態 | 建立最小 DOM/keyboard 測試與未來生成契約 | 不先引入大型框架 |
| Staff/Principal Engineer | year/subject 兩個 view 的 clone/rebind 是否漂移？ | 抽出一個 semantic option contract | 讓兩視圖共用事件與狀態模型 | 避免在兩份 DOM 上繼續疊 patch |
| UX Lead | 使用者能否理解第一答、改答與計分？ | 文字化答案狀態與 scoring policy | 鍵盤/讀屏 journey 優先 | 不以更多動畫代替回饋 |
| UX Researcher | 受影響比例與裝置組合未知 | 以 8 個障礙 Persona 作招募假設 | 修後做 5 人輔助科技走查 | 合成 Persona 不能冒充需求量 |
| Growth Lead | 免費、窄領域、免登入是自然分發點 | SEO/分享應建立在可信可用核心上 | 先降低核心練習失敗率 | 不先加 analytics 或 referral |
| CFO/Business Analyst | 三個考試 repo 重複維護成本高 | 共享 data/build contract 可降成本 | 先量化更新工時與重複資料 | 不建付費牆 |
| Security/Privacy Lead | localStorage 邊界與公開內容來源是否清楚 | 無帳號、無 server-side learner data 是優勢 | 保持 local-first；來源治理納入 #1 | 反對在未有價值證據前收集個資 |
| QA Lead | 部署綠燈不等於互動驗收 | 加 deterministic keyboard/state tests | #3 AC 全部納入 regression | 不把靜態 lint 當 AT 驗證 |
| SRE Lead | 目前唯一 workflow 只部署且無 interaction gate | 簡單站可維持低運維 | 加入輕量 smoke/budget，不建立後端 | 反對多服務化 |
| Accessibility Specialist | mc-option 的 div+onclick 是核心阻塞 | native radio/fieldset 可低成本修正 | 鍵盤、名稱、狀態、結果公告 | 反對自製複雜 ARIA widget |
| Customer Support Lead | 「練習模式按了但選不了」難以從截圖診斷 | 可操作語意也改善語音控制 | 文件說明計分政策與 local-only 狀態 | 不讓支援承擔未承諾同步功能 |

### Cross-review and minority opinions

Consensus: accessibility is a release-quality defect because it blocks the advertised practice journey; the smallest correct fix is semantic native controls and tests. The second consensus is portfolio simplification: one archive/source contract, one interactive practice entry, and no duplicated AI/LMS layer.

Minority opinion: the single-file artifact is valuable for portability and may not require a framework or a complex chunking system. The board accepts that position only if a reproducible generator, payload budget and constrained-network evidence show the single file meets target users' needs. Another minority view would remove practice entirely and keep a pure archive; the CEO retains this as a valid fallback if practice semantics cannot be maintained cheaply.

CEO, if only three things can be done:

1. Fix [#3](https://github.com/Reese-max/exam-archive/issues/3) with native keyboard/AT-operable answers.
2. Complete the truthful contract and source/build boundary in [#1](https://github.com/Reese-max/exam-archive/issues/1) after the active PR is resolved.
3. Decide the canonical data/product relationship among the three exam repositories and remove duplicate maintenance.

Do not build AI tutoring, accounts/sync, classroom management, comments/community, analytics, a native app, or another generalized question platform.

## 50 Synthetic Personas

**Synthetic simulation only; not a survey, market share study, usability test or assistive-technology Runtime test.** B01–B30 are the 60% regression baseline; E31–E50 are the 40% rotating exploration cohort.

| ID | Cohort | Background | Goal | Expectation | Task | Journey | Friction | Outcome | Comment | Severity | Suggestion |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B01 | Baseline | 18歲首考生；手機；中等熟練；4G | 找近十年重點 | 快速搜尋並開始練習 | 搜尋「人工智慧」 | 首頁→搜尋→展開試卷→開練習→選答案 | 滑鼠操作成功；鍵盤選項不可達 | FAIL（鍵盤情境） | 搜尋清楚，但練習控制需鍵盤語意 | P2 | 改用原生 radio 並公布結果 |
| B02 | Baseline | 23歲重考生；Windows；高熟練；寬頻 | 依年度複習 | 年份切換不重載 | 114→112 年篩選 | 年份 chip→試卷→題目 | 單頁載入大；篩選可用 | SUCCESS/FRICTION | 離線感佳，首載偏重 | P3 | 在 #1 下分割資料 |
| B03 | Baseline | 31歲在職警員；手機；低熟練；5G | 通勤零碎複習 | 一步找到科目 | 依科目看警政資訊 | 科目檢視→選科→展開 | 控制多但可完成 | SUCCESS | 保留簡單篩選 | P3 | 勿加帳號牆 |
| B04 | Baseline | 26歲補習班學員；筆電；中等熟練 | 做完整選擇題 | 計分可信 | 開練習→連答20題 | 點選選項→看分數 | 第一次答案政策未說明 | FRICTION | 不知道改答案是否重算 | P3 | 說明 first-attempt 規則並測試 |
| B05 | Baseline | 21歲考生；Chromebook；低熟練；觸控板故障 | 只靠鍵盤作答 | Tab 可進入所有答案 | 啟用練習並選 B | Tab→練習按鈕→題目 | 答案 div 被跳過 | FAIL | 核心練習完全中斷 | P2 | Issue #3 |
| B06 | Baseline | 35歲視障考生；NVDA；Windows | 聽讀並選答案 | 題組、選項、狀態被朗讀 | 讀第1題並作答 | H1→搜尋→題目→答案 | 選項無 radio/checked 語意 | FAIL | 只聽到文字，無可操作控制 | P2 | Issue #3 |
| B07 | Baseline | 29歲低視力使用者；200% zoom；鍵盤 | 放大後作答 | 焦點與結果清楚 | 放大→科目檢視→作答 | 縮窄畫面→Tab | 選項不可聚焦；未做 Runtime zoom | FAIL/UNKNOWN | 靜態可確認鍵盤阻塞 | P2 | Issue #3；修後 Runtime |
| B08 | Baseline | 42歲動作障礙；switch control；平板 | 掃描選擇答案 | 互動項有可識別控制 | 練習第5題 | 掃描→啟用→選項 | click-only div 不進掃描控制 | FAIL | 需要原生控制 | P2 | Issue #3 |
| B09 | Baseline | 20歲手機螢幕閱讀器使用者 | 依題作答 | VoiceOver/TalkBack 可報讀狀態 | 開啟某試卷 | 搜尋→題目→練習 | ARIA 結果與選取狀態缺失 | FAIL | 需 live result | P2 | Issue #3 |
| B10 | Baseline | 24歲低頻寬離島考生；Android；3G | 看一份題目 | 盡快首屏可用 | 首頁→114年 | 載入→搜尋 | 單一約1.35MB HTML | FRICTION | 可用但成本集中 | P2 existing | 維持 #1，不另開 |
| B11 | Baseline | 27歲 Power User；桌機；鍵盤優先 | 快速跳題 | 快捷鍵涵蓋主流程 | Ctrl+K 搜尋→作答 | 搜尋可鍵盤操作；答案不可 | FAIL | 效率在最後一步崩潰 | P2 | Issue #3 |
| B12 | Baseline | 19歲第一次使用；iPhone；4G | 知道產品做什麼 | README/頁面說明一致 | 從 GitHub 進站 | repo→README→Pages | main 無 README；PR 尚未合併 | FAIL/LOCKED | 維持 #1 | P2 existing | 不重複建 Issue |
| B13 | Baseline | 33歲教師；Mac；高熟練 | 投影題目講解 | 快速展開與列印 | 搜尋→展開→列印 | 列印 CSS 可見題目 | SUCCESS | 適合唯讀講解 | P3 | 保留 print-first |
| B14 | Baseline | 28歲考生；桌機；中等熟練 | 收藏薄弱科目 | 書籤重開仍在 | 收藏→重載→只看書籤 | localStorage 保存 | SUCCESS | 本機私密且輕量 | P3 | 保留 local-first |
| B15 | Baseline | 40歲多裝置使用者；手機+桌機 | 跨裝置延續 | 書籤與進度同步 | 手機收藏→桌機開啟 | localStorage 無同步 | FAIL（預期不符） | 但產品未承諾同步 | P3 | 明示本機保存；不先建帳號 |
| B16 | Baseline | 22歲隱私敏感考生；Firefox | 不登入使用 | 零帳號、零追蹤 | 直接開始 | 開頁→搜尋→練習 | 未見帳號/analytics | SUCCESS | 低摩擦、低資料風險 | None | 保留 |
| B17 | Baseline | 30歲網路不穩定；筆電 | 載入後離線讀 | 內容不依 API | 開頁後斷網 | 載入→斷線→瀏覽 | 字型外部；內容內嵌 | SUCCESS/FRICTION | 核心內容可在既有頁面中 | P3 | 避免新增 runtime API |
| B18 | Baseline | 37歲申論題考生；平板 | 整理申論題 | 能依科目搜尋 | 搜「數位證物」 | 搜尋→展開申論 | 搜尋成功；無答題工作區 | SUCCESS | 唯讀任務足夠 | P3 | 不要把 AI 評分塞進本 repo |
| B19 | Baseline | 25歲只看官方來源者 | 核對原題 | 每題有來源鏈 | 查看題目來源 | 題目→metadata | 內容含考試資訊但 exact source link 不明 | FRICTION | 需在 #1 的來源契約處理 | P2 existing | 不另建 duplicate |
| B20 | Baseline | 18歲色弱考生；滑鼠 | 辨認對錯 | 不只靠顏色 | 練習選錯 | 點選→CSS correct/wrong | 結果主要為顏色/class，文字公告不足 | FAIL | 與選項語意同根因 | P2 | 合併 Issue #3 |
| B21 | Baseline | 44歲鍵盤與語音輸入使用者 | 用語音/鍵盤控制 | 控制有可辨識名稱 | 說「選 B」 | 語音控制掃描互動元素 | div 選項未暴露控制 | FAIL | 同一 root cause | P2 | Issue #3 |
| B22 | Baseline | 32歲補教內容編輯；桌機 | 修正答案 | 變更可追溯、可重建 | 定位答案→編輯 | 單一 HTML 手改 | FAIL（維護） | 既有 #1 已涵蓋 | P2 existing | 不新增 Issue |
| B23 | Baseline | 50歲考生；低數位熟練 | 大字閱讀 | 不需理解 icon | 打開→搜尋→展開 | 可見文字多 | SUCCESS/FRICTION | 固定單頁可理解但密度高 | P3 | 維持清晰標籤 |
| B24 | Baseline | 20歲短時複習者；手機 | 5分鐘練10題 | 快速恢復進度 | 作答→關閉→重開 | 只在關閉練習時存摘要 | FRICTION | 不構成資料遺失承諾 | P3 | 先衡量需求 |
| B25 | Baseline | 36歲安全敏感使用者 | 不洩露作答 | 資料只在本機 | 收藏與練習 | localStorage | SUCCESS | 沒有伺服器資料面 | None | 勿加 analytics |
| B26 | Baseline | 27歲列印學習者 | 列印完整題目 | 展開內容不遺漏 | 列印一科 | print CSS 展開 body | LIKELY SUCCESS | 需實機列印驗證 | P3 | 保留打印 smoke |
| B27 | Baseline | 19歲 Safari 使用者 | 使用深色模式 | 跟隨系統偏好 | 開啟頁面 | prefers-color-scheme→toggle | 靜態邏輯存在 | LIKELY SUCCESS | 未做實機 | P3 | Runtime smoke |
| B28 | Baseline | 45歲維護者；乾淨 clone | 理解部署 | README與build可追溯 | clone→讀 README→改題 | main 無 README、無 build | FAIL/LOCKED | #1 + PR #2 | P2 existing | 不干擾 PR |
| B29 | Baseline | 23歲只需 PDF 原件 | 下載原始卷 | 能找到官方檔 | 尋找 PDF link | 頁面內嵌文字/統計 | UNKNOWN | 未確認所有 PDF link可達 | P3 | 未通過 evidence gate |
| B30 | Baseline | 34歲資料分析者 | 匯出題目資料 | 內容結構化 | 嘗試取 JSON | 只有 monolith HTML | FAIL（不承諾） | 不宜在此 repo 新增 API | P3 | 由 sibling data layer 提供 |
| E31 | Explore | 17歲無滑鼠考生；學校電腦 | 鍵盤練習 | 原生選項 | 開練習→作答 | 選項不可聚焦 | FAIL | 核心 barrier | P2 | Issue #3 |
| E32 | Explore | 62歲手抖考生；大螢幕 | 穩定選答 | 大 hit target 可鍵盤替代 | 答第1題 | 點選/Tab | 點擊區大但鍵盤無路徑 | FAIL | 語意比尺寸更重要 | P2 | Issue #3 |
| E33 | Explore | 28歲螢幕放大器使用者 | 追蹤焦點 | 焦點清楚 | 搜尋→跳結果→答題 | 搜尋跳轉可見；選項無焦點 | FAIL | 需 focusable radio | P2 | Issue #3 |
| E34 | Explore | 30歲偏好減少動效 | 避免暈動 | 尊重 reduced motion | 搜尋下一筆 | smooth scroll/shake | UNKNOWN | 未見 prefers-reduced-motion | P3 research | 證據不足，不建 Issue |
| E35 | Explore | 21歲繁中輸入法使用者 | 用關鍵詞搜尋 | 組字不誤觸快捷鍵 | 輸入「/」與中文 | 全域 / 快捷鍵避開 input | LIKELY SUCCESS | 未做 IME Runtime | P3 | 加入未來 smoke |
| E36 | Explore | 26歲跨年比較者 | 同科目並排 | 科目檢視保留語意 | 切科目→練習 | clone subject HTML | FRICTION | clone 不繼承完整 ARIA/handler contract | P2 | 納入 #3 AC |
| E37 | Explore | 38歲低電量手機使用者 | 最少 JS/CPU | 互動輕量 | 搜尋大量內容 | 遞迴 DOM 高亮整頁 | UNKNOWN | 可能有成本但無 Runtime | P3 | 拒絕效能缺陷宣稱 |
| E38 | Explore | 20歲考前一天使用者 | 取得最新115年題目 | 涵蓋最新年度 | 首頁查 115 | 僅105–114 | FAIL | 產品範圍明示到114；不是 bug | P3 strategic | 先定更新責任 |
| E39 | Explore | 29歲信任官方答案者 | 核對更正答案 | 來源與版本可查 | 查看 corrected cell | 頁面有 correction 樣式，來源鏈未知 | FRICTION | 需 provenance research，但被 #1/PR鎖住 | P2 existing | 不另建 |
| E40 | Explore | 24歲分享特定題目給同學 | 深連結精確 | URL可定位試卷/題 | 複製 hash | 只到 card id | PARTIAL | 題級深連結未知 | P3 | 先看真實需求 |
| E41 | Explore | 31歲教學助理 | 建立自訂題單 | 可挑題分享 | 收藏多卷 | localStorage 書籤 | PARTIAL | 無跨裝置/分享 | P3 | 不在此 repo建協作 |
| E42 | Explore | 22歲 Android TalkBack | 選項與結果可讀 | radio群組可操作 | 練習選 C | 探索控制 | 無 radio semantics | FAIL | 同根因 | P2 | Issue #3 |
| E43 | Explore | 40歲公共電腦使用者 | 不留下資料 | 可清除本機狀態 | 練習與書籤 | localStorage 持續存在 | FRICTION | 未提供全清除 | P3 research | 低影響，未建 Issue |
| E44 | Explore | 27歲離線保存者 | 下載單檔備份 | 一檔即用 | 另存網頁 | 內容內嵌、字型外部 | LIKELY SUCCESS | local-first 是優勢 | None | 保留單檔出口 |
| E45 | Explore | 33歲法規敏感維護者 | 確認引用條件 | 來源與授權清楚 | 查 repo license | main 無 README/LICENSE | UNKNOWN/LOCKED | PR #2觸及但未合併 | P3 research | 不與 active PR競爭 |
| E46 | Explore | 18歲免費替代方案使用者 | 免登入刷題 | 立即開始 | 比較阿摩/Quizlet後打開 | 本產品免帳號 | SUCCESS | 差異化為窄領域、零帳號 | None | 強化而非複製平台 |
| E47 | Explore | 35歲教練；多名學生 | 追蹤班級進度 | 群組報表 | 分派題目 | 本機單人 | FAIL（不承諾） | Quizlet較合適 | DON'T | 不建教師後台 |
| E48 | Explore | 23歲 Anki power user | 間隔複習 | 錯題自動排程 | 練習後回顧 | 僅最近分數摘要 | FAIL（替代品優勢） | 非本產品核心 | LATER | 留給 sibling practice app |
| E49 | Explore | 25歲低資料方案使用者 | 精準下載一科 | 不載全部年份 | 進入單科 | 首載全檔 | FRICTION | 既有 #1 | P2 existing | 分割資料，不另開 |
| E50 | Explore | 39歲產品維護決策者 | 避免三個 repo重疊 | 清楚 canonical boundary | 比較 sibling repos | README僅在PR；界線未上main | FAIL/LOCKED | Portfolio simplification needed | P2 existing | 先完成 #1/PR #2 |

### Coverage summary

- Age: 17–62.
- Roles: first-time and repeat candidates, working police, teachers, maintainers, coaches and analysts.
- Skill: low, medium, high and power users.
- Devices: Android/iPhone/tablet/Chromebook/Windows/macOS/public desktop.
- Network: broadband, 5G/4G/3G, unstable/offline-after-load.
- Accessibility/edge: NVDA, mobile screen reader, keyboard-only, switch control, motor impairment, low vision, 200% zoom, color vision, reduced-motion hypothesis, IME, public-computer privacy.
- Core journeys: discovery, search, year/subject navigation, practice, score/reset, bookmarks, print, deep-link/share, source checking, maintenance.

## Competitor Switching Test

The same 50 synthetic personas chose the best tool for their stated scenario after seeing only the evidence-backed capabilities above.

| Choice | Personas | Synthetic preference share | Main reason |
|---|---:|---:|---|
| exam-archive | 14 | 28% | Free, narrow scope, no login, searchable single artifact |
| police-exam-practice | 12 | 24% | Better fit for interactive answering and canonical practice |
| Yamol | 10 | 20% | Current 115-year coverage, breadth and exam community |
| MOEX official | 7 | 14% | Authoritative source and answer provenance |
| Quizlet | 4 | 8% | Personalized/multi-mode study and class workflows |
| Anki | 3 | 6% | Durable offline spaced repetition and power-user control |

**Synthetic Preference Share is a scenario simulation, not real market share, traffic, conversion or human research.** The product wins archive/privacy scenarios but loses keyboard-accessible practice, latest-year and adaptive-study scenarios.

## Red Team

- Persona bias: the cohort over-represents exam candidates already comfortable with digital archives and may understate paper/PDF-first preference.
- Competitor bias: Quizlet and Anki are indirect learning substitutes, not police-IT content authorities; they should inform interaction baselines, not roadmap copying.
- Evidence risk: missing semantics are statically confirmed, but actual screen-reader announcements and deployed focus order remain Runtime pending.
- Over-engineering risk: a framework rewrite is not required to fix #3. Native form controls and small deterministic tests are sufficient.
- Feature bloat: AI tutor, accounts, social features, SRS and teacher dashboards would dilute the archive.
- Confirmation bias: the old audit emphasizes payload size; this round deliberately looked for an independent root cause and found practice operability.
- Growth risk: adding tracking to measure usage would weaken the strongest privacy advantage.
- Simplification alternative: if practice remains unmaintainable, remove the practice CTA and route users to `police-exam-practice` instead of preserving a broken duplicate.

## Findings and Quality Gate

| ID | Type | Priority | User impact | Strategic value | Gap | Risk reduction | Confidence | Effort | Gate result | Tracking |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| F-20260909-01 | ACCESSIBILITY / UX | P2 | 8/50 synthetic personas blocked | High | MUST MATCH | High | HIGH static | Medium | PASS: evidence, distinctness, actionability, impact, AC, duplicate check all satisfied | NEW [#3](https://github.com/Reese-max/exam-archive/issues/3) |

Stable fingerprint: `exam-archive + practice MCQ controls + keyboard/AT attempt + non-focusable div onclick + missing native/ARIA state`.

### Duplicate avoided

- Keyboard-only failure, screen-reader invisibility, switch-control failure, color-only result, subject-view cloned control drift and voice-control failure are six symptoms of the same option-semantics root cause; all are combined in #3.
- Monolithic payload, no README, no build and no performance budget remain one existing root issue in #1; no duplicate issue was created.

### Rejected findings

1. **Add 115-year papers immediately:** rejected as a new Issue; coverage ends at 114 by explicit product copy and update authority/source contract is unresolved under #1.
2. **Build an AI tutor or essay grader:** rejected for feature bloat, cost/safety burden and overlap with other products.
3. **Add accounts/cloud sync:** rejected because no validated demand offsets privacy and operations cost.
4. **Build a PWA/native app:** rejected; no installation/offline failure evidence.
5. **Create a second “split the HTML” Issue:** rejected as duplicate of #1.
6. **Close #1 because README PR exists:** rejected; PR #2 is unmerged and explicitly partial.
7. **Declare a licensing violation:** rejected; no legal determination or content-by-content provenance audit was performed.
8. **Declare CI broken:** rejected; latest audited default-branch Pages run is successful.
9. **Declare a performance defect from size alone:** rejected; 1.35 MB is confirmed but target-device Runtime budgets are not.
10. **Declare print, Safari, IME or reduced-motion failures:** rejected; only static hypotheses exist and no Runtime reproduction was performed.

## Regression

| Object | Status | Evidence | Action |
|---|---|---|---|
| #1 repository contract / monolith | STILL REPRODUCIBLE on main; **SKIPPED_LOCKED** | main still contains only workflow, audit and index; PR #2 is active and partial | No Issue/PR comment or state change |
| #3 practice answer semantics | NEW / NEEDS_RUNTIME_VERIFICATION | Static code confirms root cause | Lock acquired, issue created; verify after fix |

No issue is marked VERIFIED FIXED. A green Pages deploy is not acceptance evidence for interaction behavior.

## Runtime Pending

- Deployed keyboard-only path: search → open paper → enable practice → choose answer → reset → switch view.
- NVDA/Firefox or NVDA/Chrome announcement of question, option, checked state and result.
- One mobile screen-reader smoke.
- 200% zoom focus visibility.
- Constrained-network first usable result for #1.
- Print/PDF and deep-link representative samples.
- Content-to-MOEX source/version reconciliation.
- Fix-SHA Pages deploy receipt and post-deploy smoke.

## NOW / NEXT / LATER / DON'T

### NOW

- Fix #3 with native semantic controls and deterministic tests.
- Resolve active PR #2 without overstating that the product is non-interactive.
- Keep #1 open until its chosen acceptance path is genuinely complete.

### NEXT

- Under #1, choose: reproducible generated chunks with a payload budget, or a measured single-file contract with explicit limits.
- Create a shared data/source manifest consumed by the archive and practice sibling, after the active work unlocks.
- Add current-year freshness and source-drift checks only after ownership is defined.

### LATER

- Exact question deep links and exportable local progress, only if validated by real users.
- Human accessibility/usability research with exam candidates.
- Consider a read-only offline bundle as a first-class distribution artifact.

### DON'T

- AI grading/tutoring in this repo.
- Accounts, social/community, ads, analytics or teacher administration.
- General-purpose flashcards/SRS.
- Framework migration without a measured need.
- Duplicate source datasets across sibling repos.

Priority order applied: **SIMPLIFY → FIX → IMPROVE → ADD**; no removal is required now, though removing practice is the fallback if it cannot be made reliable.

## Difference From Previous Round

Previous audit round recorded only #1 and explicitly stated no browser Runtime was run. This round:

- preserved #1 as existing and locked;
- inspected the actual practice/search/bookmark/ARIA code paths;
- confirmed a distinct practice-control semantics defect;
- created #3 with complete acceptance and regression criteria;
- refreshed competitive evidence through 2026-09-09;
- expanded 50-persona coverage while retaining 30 baseline and rotating 20 exploratory personas.

## Decision Memo

- **What this product should become:** the fastest, most trustworthy, no-login police-IT past-paper archive, with a deliberately small accessible practice layer or a clear handoff to the canonical practice sibling.
- **Who it should serve:** candidates who need focused 105–current police-IT retrieval, offline-friendly reading, print and lightweight self-check.
- **Why users would choose it:** narrow curation, zero account, no ads/analytics, fast local search after load and single-artifact portability.
- **Why users choose competitors:** MOEX for authority, Yamol for current/broad content, `police-exam-practice` for real interactive practice, Quizlet for polished modes, Anki for spaced repetition.
- **Biggest competitive gaps:** answer operability, current-year/source contract, reproducible maintenance and portfolio clarity.
- **Potential moat:** a verified, versioned police-IT corpus with trustworthy source lineage and accessible local-first retrieval.
- **Top strategic/engineering/UX priorities:** #3; complete #1; shared source manifest/canonical routing.
- **What NOT to build:** AI tutor, accounts, LMS, comments, marketplace, analytics, native app, general SRS.
- **Features worth removing:** none immediately; remove or redirect practice only if the accessible semantic contract cannot be maintained.
- **Biggest risks:** inaccessible core flow, stale or weakly sourced content, three-repo duplication, manual monolith drift.
- **Next experiments:** five real candidate usability sessions including keyboard/AT; constrained-network measurement; compare one shared data manifest powering both archive and practice.
- **Decision:** **SIMPLIFY / MAINTAIN** — valuable narrow artifact, but only if accessibility and ownership are made truthful before growth.

## Portfolio CEO Review

This round refreshed `exam-archive` only; other repositories use the existing portfolio baseline and are not claimed as re-audited.

- `exam-archive` and `police-exam-archive` overlap in historical content and should not maintain independent canonical datasets.
- `police-exam-practice` should own interactive answering, attempts, mastery and future adaptive learning.
- Shared opportunity: one versioned exam Data Layer + source/provenance receipt + static generation contract; two thin consumers at most (archive and practice).
- Do not share Auth/AI Gateway here; the no-account/no-AI boundary is intentional.
- Incremental ranking for this product family:
  1. `police-exam-practice` — MAINTAIN as compatibility/canonical practice entry.
  2. `exam-archive` — SIMPLIFY/MAINTAIN as archive if #1/#3 close.
  3. `police-exam-archive` — evaluate MERGE WITH ANOTHER PROJECT after its active branches/PRs clear.

## Issue Mapping and Mandatory Verification

- **Total Findings:** 1
- **New Issues Created:** 1 — [Reese-max/exam-archive #3 — [P2][ACCESSIBILITY][UX] Make practice answers operable and announced without a pointer](https://github.com/Reese-max/exam-archive/issues/3)
- **Updated Existing Issues:** 0
- **Reopened Issues:** 0
- **Research Issues:** 0
- **Duplicate Avoided:** 7 root-cause duplicate groups (6 mapped to #3, monolith group retained in #1)
- **Issue Write Blocked:** 0
- **SKIPPED_LOCKED:** #1 / PR #2 / `docs/issue-1-root-readme`
- **Rejected Findings:** 10, listed above with reasons
- **Verified Fixed:** 0
- **Priority distribution:** P0 0 / P1 0 / P2 1 / P3 0 / STRATEGIC 0
- **Highest Priority:** #3
- **Finding mapping:** 1/1 → NEW
- **Closure validation:** every Quality-Gate finding maps to NEW / UPDATED / REOPENED / RESEARCH. **PASS.**

## Evidence Labels

- **CONFIRMED:** file size/tree, functions and event wiring, missing option semantics, Pages workflow/run status, issue/PR/branch state.
- **LIKELY:** target user distribution, competitive switching reasons, business value and moat.
- **UNKNOWN / NEEDS_RUNTIME_VERIFICATION:** real assistive-tech behavior, real user prevalence, production performance, content completeness, source/legal status and post-fix deployment behavior.
