"""Accessibility regression suite for practice mode multiple-choice options.

Issue #3: every multiple-choice option must be operable and announced without
a pointer. These tests drive the real page in headless Chromium via
Playwright: real keyboard events, real focus handling, real AX tree.

Contract under test (see README "練習模式的無障礙結構"):
- each question is a <fieldset class="mc-field"> with a <legend> group label
- each option is <label class="mc-option"> wrapping a native
  <input type="radio" class="mc-radio"> (unique name per question)
- radios are disabled until practice mode is on
- answering fires a text verdict in .mc-verdict (role=status) and updates
  the aria-live #practiceScore region once per question (first-attempt policy)
- subject view clones keep unique names and share the data-akey dedup key
"""
import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"

# Wait budget for the enhanced option markup. The enhancement pass is one
# synchronous DOMContentLoaded handler, so the first fieldset appearing means
# all of them exist.
ENHANCED_TIMEOUT_MS = 20000

CARD_XPATH = "xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' subject-card ')]"


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    pg = browser.new_page()
    pg.goto(INDEX.as_uri())
    # state=attached: question groups live inside collapsed .subject-card
    # bodies, so they are never "visible" until the card is opened.
    pg.wait_for_selector("fieldset.mc-field", state="attached",
                         timeout=ENHANCED_TIMEOUT_MS)
    yield pg
    pg.close()


def open_card(locator):
    """Open the .subject-card containing the element (the toggleCard result)
    and activate its subject-view section if any, so its body is visible."""
    card = locator.locator(CARD_XPATH)
    card.evaluate(
        """c => {
            c.classList.add('open');
            const s = c.closest('.subject-view-section');
            if (s) s.classList.add('active');
        }""")
    return card


def practice_on(page):
    """Enable practice mode the way a keyboard user does: focus the toolbar
    button and press Enter."""
    page.locator("#practiceToggle").focus()
    page.keyboard.press("Enter")
    page.wait_for_function("document.body.classList.contains('practice-mode')")


def score(page):
    return {
        "correct": int(page.locator("#scoreCorrect").inner_text()),
        "total": int(page.locator("#scoreTotal").inner_text()),
    }


def pick(page, field, letter):
    """Select an option by clicking its <label> — the pointer path that must
    forward to the wrapped radio."""
    opt = field.locator(".mc-option", has=page.locator(
        f'input.mc-radio[value="{letter}"]'))
    opt.click()
    return field.locator(f'input.mc-radio[value="{letter}"]')


def correct_letter(field):
    """Read this question's answer key from its card's answer section."""
    qidx = field.get_attribute("data-qidx")
    return field.evaluate(
        """(f, qidx) => {
            const card = f.closest('.subject-card');
            const cell = card.querySelectorAll('.answer-section .answer-cell')[qidx];
            const el = cell && cell.querySelector('.q-ans');
            return el ? el.textContent.trim() : '';
        }""", qidx)


def test_every_option_is_a_radio_inside_a_labelled_fieldset(page):
    fields = page.locator("fieldset.mc-field")
    assert fields.count() > 1000, f"expected >1000 question groups, got {fields.count()}"
    problems = page.evaluate(
        """() => {
            const bad = [];
            for (const f of document.querySelectorAll('fieldset.mc-field')) {
                const legend = f.firstElementChild;
                if (!legend || legend.tagName !== 'LEGEND' || !legend.textContent.trim()) {
                    bad.push('missing legend'); continue;
                }
                const opts = f.querySelectorAll('.mc-option');
                if (opts.length < 2) { bad.push('fewer than 2 options'); continue; }
                for (const o of opts) {
                    if (o.tagName !== 'LABEL') { bad.push('option not a label'); break; }
                    const r = o.querySelector('input.mc-radio[type=radio]');
                    if (!r || !/^[A-Z]$/.test(r.value)) { bad.push('missing radio'); break; }
                    if (!o.textContent.trim()) { bad.push('empty option name'); break; }
                }
            }
            return bad;
        }""")
    assert problems == [], f"malformed groups: {problems[:5]}"


def test_radio_group_names_are_unique_per_question(page):
    dup = page.evaluate(
        """() => {
            const byName = new Map();
            for (const r of document.querySelectorAll('input.mc-radio')) {
                if (!byName.has(r.name)) byName.set(r.name, new Set());
                byName.get(r.name).add(r.closest('.mc-field'));
            }
            return [...byName].filter(([, fs]) => fs.size > 1).map(([n]) => n);
        }""")
    assert dup == [], f"radio names shared across questions: {dup[:5]}"


def test_options_are_inert_until_practice_mode_is_enabled(page):
    radios = page.locator("input.mc-radio")
    assert radios.count() > 0
    assert page.evaluate(
        "[...document.querySelectorAll('input.mc-radio')].every(r => r.disabled)"
    ), "radios must stay disabled (out of Tab order) before practice mode"
    practice_on(page)
    assert page.evaluate(
        "[...document.querySelectorAll('input.mc-radio')].every(r => !r.disabled)"
    ), "radios must be enabled in practice mode"
    # practice off again restores inert state
    page.evaluate("togglePractice()")
    assert page.evaluate(
        "[...document.querySelectorAll('input.mc-radio')].every(r => r.disabled)"
    )


def test_keyboard_selection_marks_and_announces_answer(page):
    field = page.locator("fieldset.mc-field").first
    open_card(field)
    practice_on(page)
    ans = correct_letter(field)
    assert re.match(r"^[A-D]$", ans), "first card must have an answer key"
    wrong = "B" if ans == "A" else "A"
    radio = field.locator(f'input.mc-radio[value="{wrong}"]')
    radio.focus()
    assert radio.evaluate("el => document.activeElement === el"), \
        "radio must be focusable without a pointer"
    page.keyboard.press(" ")
    assert radio.is_checked()
    opt = radio.locator("xpath=..")
    assert "selected" in (opt.get_attribute("class") or "")
    verdict = field.locator(".mc-verdict")
    assert verdict.get_attribute("role") == "status"
    assert "答錯" in verdict.inner_text()
    assert ans in verdict.inner_text()


def test_arrow_keys_move_within_radio_group(page):
    field = page.locator("fieldset.mc-field").first
    open_card(field)
    practice_on(page)
    first = field.locator("input.mc-radio").first
    second = field.locator("input.mc-radio").nth(1)
    first.focus()
    page.keyboard.press("ArrowDown")
    # native radio-group behaviour: arrow moves focus+selection within group
    assert second.is_checked()
    assert second.evaluate("el => document.activeElement === el")
    # an arrow-selection is a real selection: it is the scored first attempt.
    # Arrow-past steps therefore count — the documented first-attempt policy.
    assert score(page)["total"] == 1
    page.keyboard.press("ArrowUp")
    assert first.is_checked()
    assert score(page)["total"] == 1, "re-selection within the group must not recount"


def test_first_attempt_scoring_recounts_never(page):
    f1 = page.locator("fieldset.mc-field").first
    card = open_card(f1)
    practice_on(page)
    ans = correct_letter(f1)
    wrong = "B" if ans == "A" else "A"
    pick(page, f1, wrong)
    assert score(page) == {"correct": 0, "total": 1}
    # re-picking the right answer must not change the recorded first attempt
    pick(page, f1, ans)
    assert score(page) == {"correct": 0, "total": 1}
    # a different question still counts exactly once
    field2 = card.locator("fieldset.mc-field").nth(1)
    ans2 = correct_letter(field2)
    pick(page, field2, ans2)
    assert score(page) == {"correct": 1, "total": 2}


def test_paper_without_answer_key_announces_but_never_scores(page):
    field = page.locator("fieldset.mc-field").first
    card = open_card(field)
    card.evaluate("c => c.querySelector('.answer-section').remove()")
    practice_on(page)
    pick(page, field, "A")
    assert score(page) == {"correct": 0, "total": 0}
    assert re.search(r"已選擇|無標準答案", field.locator(".mc-verdict").inner_text())


def test_reset_clears_radios_classes_verdicts_and_allows_recount(page):
    field = page.locator("fieldset.mc-field").first
    open_card(field)
    practice_on(page)
    pick(page, field, correct_letter(field))
    assert score(page) == {"correct": 1, "total": 1}
    page.locator(".score-reset").click()
    assert score(page) == {"correct": 0, "total": 0}
    assert page.evaluate(
        "[...document.querySelectorAll('input.mc-radio')].every(r => !r.checked)")
    assert page.evaluate(
        """[...document.querySelectorAll('.mc-option')].every(o =>
            !['selected','correct','wrong'].some(c => o.classList.contains(c)))""")
    assert page.evaluate(
        """[...document.querySelectorAll('.mc-verdict')].every(v => !v.textContent.trim())""")
    pick(page, field, correct_letter(field))
    assert score(page) == {"correct": 1, "total": 1}


def test_subject_view_clones_share_akey_dedup_but_unique_names(page):
    practice_on(page)
    year_field = page.locator("#yearView fieldset.mc-field").first
    open_card(year_field)
    pick(page, year_field, correct_letter(year_field))
    assert score(page) == {"correct": 1, "total": 1}
    akey = year_field.get_attribute("data-akey")
    assert akey

    page.evaluate("switchView('subject')")
    sv = page.locator("#subjectView")
    sv.locator("fieldset.mc-field").first.wait_for(state="attached")
    assert sv.locator("fieldset.mc-field").count() > 1000
    overlap = page.evaluate(
        """() => {
            const yn = new Set([...document.querySelectorAll('#yearView input.mc-radio')].map(r => r.name));
            return [...document.querySelectorAll('#subjectView input.mc-radio')].some(r => yn.has(r.name));
        }""")
    assert not overlap, "subject view must not reuse year-view radio names"

    # the same logical question answered again in subject view must not double
    # count (a card may be cloned into several subject sections, so >= 1 clone)
    sv_field = sv.locator(f'fieldset.mc-field[data-akey="{akey}"]').first
    open_card(sv_field)
    before = score(page)
    pick(page, sv_field, "A")
    assert score(page) == before

    # a different, unanswered question in subject view counts once more
    card = sv_field.locator(CARD_XPATH)
    field2 = card.locator("fieldset.mc-field").nth(1)
    pick(page, field2, correct_letter(field2))
    assert score(page) == {"correct": before["correct"] + 1, "total": before["total"] + 1}


def test_toggles_and_view_switches_never_duplicate_structures(page):
    practice_on(page)
    page.evaluate("switchView('subject')")
    page.evaluate("switchView('year')")
    page.evaluate("togglePractice()")
    practice_on(page)
    page.evaluate("switchView('subject')")
    page.evaluate("switchView('year')")
    page.evaluate("togglePractice()")
    practice_on(page)

    report = page.evaluate(
        """() => {
            const out = {badLegend: 0, badVerdict: 0, dupIds: 0, stackedBtns: 0};
            for (const f of document.querySelectorAll('fieldset.mc-field')) {
                if ([...f.children].filter(c => c.tagName === 'LEGEND').length !== 1) out.badLegend++;
                if (f.querySelectorAll('.mc-verdict').length !== 1) out.badVerdict++;
            }
            const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
            out.dupIds = ids.length - new Set(ids).size;
            for (const s of document.querySelectorAll('.answer-section')) {
                const p = s.previousElementSibling;
                if (p && p.classList.contains('reveal-btn') &&
                    p.previousElementSibling && p.previousElementSibling.classList.contains('reveal-btn'))
                    out.stackedBtns++;
            }
            return out;
        }""")
    assert report == {"badLegend": 0, "badVerdict": 0, "dupIds": 0, "stackedBtns": 0}

    page.evaluate("togglePractice()")  # off
    assert page.locator(".reveal-btn").count() == 0


def test_score_region_and_verdicts_are_live_regions(page):
    region = page.locator("#practiceScore")
    assert region.get_attribute("role") == "status"
    assert region.get_attribute("aria-live") == "polite"
    field = page.locator("fieldset.mc-field").first
    open_card(field)
    practice_on(page)
    pick(page, field, correct_letter(field))
    assert page.locator("#scoreCorrect").inner_text() == "1"


def test_ax_tree_exposes_question_group_and_named_radios(page):
    """Assistive-technology smoke check via Chromium's real accessibility tree:
    the question group and its named radio options must be exposed."""
    field = page.locator("fieldset.mc-field").first
    open_card(field)
    practice_on(page)
    pick(page, field, correct_letter(field))
    cdp = page.context.new_cdp_session(page)
    doc = cdp.send("DOM.getDocument")
    node = cdp.send("DOM.querySelector", {
        "nodeId": doc["root"]["nodeId"],
        "selector": "#yearView fieldset.mc-field",
    })
    desc = cdp.send("DOM.describeNode", {"nodeId": node["nodeId"]})
    ax = cdp.send("Accessibility.queryAXTree", {
        "backendNodeId": desc["node"]["backendNodeId"],
    })
    nodes = ax.get("nodes", [])
    roles = [n.get("role", {}).get("value") for n in nodes]
    radios = [n for n in nodes if n.get("role", {}).get("value") == "radio"]
    assert len(radios) >= 2, f"AX tree must expose radios, got roles {set(roles)}"

    def name_of(n):
        return n.get("name", {}).get("value", "")

    def prop(n, key):
        for p in n.get("properties", []):
            if p.get("name") == key:
                return p.get("value", {}).get("value")
        return None

    assert any(re.search(r"第\s*\S+\s*題", name_of(n)) for n in nodes), \
        "question group label must be exposed to AT"
    assert all(name_of(r).strip() for r in radios), "every option needs a name"
    assert any(prop(r, "checked") in ("true", True) for r in radios), \
        "checked state must be exposed to AT"

    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "ax-tree.json").write_text(
        json.dumps(nodes[:60], ensure_ascii=False, indent=2))
