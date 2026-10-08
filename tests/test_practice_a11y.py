import os
import re
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        candidates = [
            os.environ.get("CHROME_PATH"),
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
        ]
        executable = next((candidate for candidate in candidates if candidate), None)
        launch_options = {"headless": True}
        if executable:
            launch_options["executable_path"] = executable
        browser = playwright.chromium.launch(**launch_options)
        yield browser
        browser.close()


@pytest.fixture()
def page(browser, site_url):
    page = browser.new_page()
    page.goto(site_url, wait_until="load")
    page.locator("#year-114 fieldset.mc-field").first.wait_for(state="attached")
    yield page
    page.close()


@pytest.fixture(scope="session")
def site_url():
    # A loopback origin works in managed browsers that prohibit file:// pages.
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.html"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def score(page):
    return {
        "correct": int(page.locator("#scoreCorrect").inner_text()),
        "total": int(page.locator("#scoreTotal").inner_text()),
    }


def practice_on(page):
    toggle = page.locator("#practiceToggle")
    toggle.focus()
    page.keyboard.press("Enter")
    assert page.locator("body").evaluate("body => body.classList.contains('practice-mode')")


def open_card(field):
    card = field.locator("xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' subject-card ')]")
    card.evaluate("card => card.classList.add('open')")
    return card


def answer_for(field):
    return field.evaluate(
        """field => {
            const card = field.closest('.subject-card');
            const cell = card.querySelectorAll('.answer-section .answer-cell')[Number(field.dataset.qidx)];
            const answer = cell && cell.querySelector('.q-ans');
            return answer ? answer.textContent.trim() : '';
        }"""
    )


def choose(page, field, letter):
    radio = field.locator(f'input.mc-radio[value="{letter}"]')
    radio.focus()
    page.keyboard.press(" ")
    return radio


def test_options_are_native_radios_in_labelled_groups(page):
    report = page.evaluate(
        r"""() => {
            const fields = [...document.querySelectorAll('#yearView fieldset.mc-field')];
            const names = [];
            const problems = [];
            for (const field of fields) {
                const legend = field.querySelector(':scope > legend');
                const options = [...field.querySelectorAll(':scope > .mc-option')];
                if (!legend || !/^第\s*\S+\s*題/.test(legend.textContent)) problems.push('legend');
                if (options.length < 2) problems.push('options');
                const optionNames = [];
                for (const option of options) {
                    const radio = option.querySelector('input.mc-radio[type=radio]');
                    if (option.tagName !== 'LABEL' || !radio || !/^[A-Z]$/.test(radio.value) || !option.textContent.trim()) {
                        problems.push('option');
                    }
                    optionNames.push(radio && radio.name);
                }
                if (new Set(optionNames).size !== 1) problems.push('group name');
                names.push(optionNames[0]);
            }
            return { count: fields.length, names, problems };
        }"""
    )
    assert report["count"] > 0
    assert report["problems"] == []
    assert len(set(report["names"])) == report["count"]


def test_practice_can_be_entered_and_answer_selected_by_keyboard(page):
    header = page.locator("#yearView .subject-card").first.locator(".subject-header")
    header.focus()
    page.keyboard.press("Enter")
    assert page.locator("#yearView .subject-card").first.evaluate(
        "card => card.classList.contains('open')"
    )
    practice_on(page)
    field = page.locator("#yearView fieldset.mc-field").first
    open_card(field)
    answer = answer_for(field)
    wrong = "B" if answer != "B" else "A"
    radio = choose(page, field, wrong)
    assert radio.is_checked()
    option = radio.locator("xpath=..")
    assert "selected" in (option.get_attribute("class") or "")
    verdict = field.locator(".mc-verdict")
    assert verdict.get_attribute("role") == "status"
    assert verdict.get_attribute("aria-live") == "polite"
    assert "答錯" in verdict.inner_text()
    assert answer in verdict.inner_text()
    assert score(page) == {"correct": 0, "total": 1}


def test_native_arrow_selection_and_first_attempt_scoring(page):
    practice_on(page)
    field = page.locator("#yearView fieldset.mc-field").first
    open_card(field)
    first = field.locator("input.mc-radio").first
    second = field.locator("input.mc-radio").nth(1)
    first.focus()
    page.keyboard.press("ArrowDown")
    assert second.is_checked()
    assert second.evaluate("radio => document.activeElement === radio")
    assert score(page)["total"] == 1
    page.keyboard.press("ArrowUp")
    assert first.is_checked()
    assert score(page)["total"] == 1


def test_changing_answer_does_not_double_count(page):
    practice_on(page)
    field = page.locator("#yearView fieldset.mc-field").first
    open_card(field)
    answer = answer_for(field)
    wrong = "B" if answer != "B" else "A"
    choose(page, field, wrong)
    assert score(page) == {"correct": 0, "total": 1}
    choose(page, field, answer)
    assert score(page) == {"correct": 0, "total": 1}
    assert field.locator(f'input.mc-radio[value="{answer}"]').is_checked()


def test_reset_clears_state_and_allows_a_new_attempt(page):
    practice_on(page)
    field = page.locator("#yearView fieldset.mc-field").first
    open_card(field)
    choose(page, field, answer_for(field))
    assert score(page) == {"correct": 1, "total": 1}
    page.locator(".score-reset").focus()
    page.keyboard.press("Enter")
    assert score(page) == {"correct": 0, "total": 0}
    assert page.locator("input.mc-radio:checked").count() == 0
    assert page.locator(".mc-option.selected, .mc-option.correct, .mc-option.wrong").count() == 0
    assert page.locator(".mc-verdict").evaluate_all(
        "verdicts => verdicts.every(verdict => !verdict.textContent.trim())"
    )
    choose(page, field, answer_for(field))
    assert score(page) == {"correct": 1, "total": 1}


def test_no_answer_key_is_announced_without_scoring(page):
    field = page.locator("#yearView fieldset.mc-field").first
    card = open_card(field)
    card.locator(".answer-section").evaluate("section => section.remove()")
    practice_on(page)
    choose(page, field, "A")
    assert score(page) == {"correct": 0, "total": 0}
    assert re.search(r"已選擇|無標準答案", field.locator(".mc-verdict").inner_text())


def test_subject_view_keeps_keyboard_behavior_and_deduplicates_score(page):
    practice_on(page)
    year_field = page.locator("#yearView fieldset.mc-field").first
    open_card(year_field)
    choose(page, year_field, answer_for(year_field))
    assert score(page) == {"correct": 1, "total": 1}
    answer_key = year_field.get_attribute("data-akey")
    assert answer_key

    view_button = page.locator("#viewBySubject")
    view_button.focus()
    page.keyboard.press("Enter")
    subject_view = page.locator("#subjectView")
    subject_view.locator("fieldset.mc-field").first.wait_for(state="attached")
    assert subject_view.locator("fieldset.mc-field").count() > 0
    assert page.evaluate(
        """() => {
            const yearNames = new Set([...document.querySelectorAll('#yearView input.mc-radio')].map(r => r.name));
            return [...document.querySelectorAll('#subjectView input.mc-radio')].every(r => !yearNames.has(r.name));
        }"""
    )

    clone = subject_view.locator(f'fieldset.mc-field[data-akey="{answer_key}"]').first
    open_card(clone)
    before = score(page)
    choose(page, clone, "A")
    assert score(page) == before

    different_field = clone.locator("xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' subject-card ')]").locator("fieldset.mc-field").nth(1)
    open_card(different_field)
    answer = answer_for(different_field)
    if answer:
        choose(page, different_field, answer)
        assert score(page) == {"correct": before["correct"] + 1, "total": before["total"] + 1}


def test_toggling_practice_and_views_does_not_duplicate_state(page):
    base_fields = page.locator("fieldset.mc-field").count()
    practice_on(page)
    page.locator("#viewBySubject").click()
    page.locator("#viewByYear").click()
    page.locator("#practiceToggle").click()
    page.locator("#practiceToggle").click()
    page.locator("#viewBySubject").click()
    page.locator("#viewByYear").click()
    assert page.locator("#yearView fieldset.mc-field").count() == base_fields
    assert page.locator("fieldset.mc-field").evaluate_all(
        "fields => fields.every(field => field.querySelectorAll(':scope > legend').length === 1 && field.querySelectorAll(':scope > .mc-verdict').length === 1)"
    )
    assert page.locator("[id]").evaluate_all(
        "nodes => { const ids = nodes.map(node => node.id); return new Set(ids).size === ids.length; }"
    )
    assert page.locator(".answer-section").evaluate_all(
        "sections => sections.every(section => !(section.previousElementSibling && section.previousElementSibling.previousElementSibling && section.previousElementSibling.classList.contains('reveal-btn') && section.previousElementSibling.previousElementSibling.classList.contains('reveal-btn')))"
    )
    page.locator("#practiceToggle").click()
    assert page.locator("input.mc-radio:not(:disabled)").count() == 0
    assert page.locator(".reveal-btn").count() == 0


def test_accessibility_tree_exposes_group_names_radio_names_and_checked_state(page):
    field = page.locator("#yearView fieldset.mc-field").first
    open_card(field)
    practice_on(page)
    choose(page, field, answer_for(field))
    cdp = page.context.new_cdp_session(page)
    document = cdp.send("DOM.getDocument")
    node = cdp.send("DOM.querySelector", {
        "nodeId": document["root"]["nodeId"],
        "selector": "#yearView fieldset.mc-field",
    })
    described = cdp.send("DOM.describeNode", {"nodeId": node["nodeId"]})
    tree = cdp.send("Accessibility.queryAXTree", {
        "backendNodeId": described["node"]["backendNodeId"],
    })["nodes"]
    radios = [item for item in tree if item.get("role", {}).get("value") == "radio"]
    assert len(radios) >= 2
    assert any(re.search(r"第\s*\S+\s*題", item.get("name", {}).get("value", "")) for item in tree)
    assert all(item.get("name", {}).get("value", "").strip() for item in radios)
    assert any(
        property_["name"] == "checked" and property_.get("value", {}).get("value") in (True, "true")
        for item in radios
        for property_ in item.get("properties", [])
    )


def test_dark_mode_keeps_answer_feedback_visible(page):
    page.locator("#darkToggle").click()
    practice_on(page)
    field = page.locator("#yearView fieldset.mc-field").first
    open_card(field)
    answer = answer_for(field)
    wrong = "B" if answer != "B" else "A"
    choose(page, field, wrong)
    assert field.locator(".mc-verdict").evaluate(
        "verdict => getComputedStyle(verdict).color"
    ) == "rgb(252, 129, 129)"


def synthetic_card(year, subject):
    """Small fake papers; canonical exam questions and answers stay untouched."""
    number, title = {"constitution": (1, "中華民國憲法"), "chinese": (2, "國文")}[subject]
    questions = "".join(
        f'<div class="mc-question"><span class="q-number">{question}</span>'
        f'<span class="q-text">合成測試題 {question}</span></div>'
        + "".join(
            f'<div class="mc-option"><span class="opt-label">({letter})</span>'
            f'<span class="opt-text">測試選項 {letter}</span></div>'
            for letter in "ABCD"
        )
        for question in range(1, 4)
    )
    return (
        f'<div class="subject-card" id="y{year}-{number}">'
        f'<div class="subject-header"><h3>{title}</h3></div>'
        f'<div class="subject-body">{questions}<div class="answer-section">'
        '<div class="answer-cell"><span class="q-num">1</span><span class="q-ans">A</span></div>'
        '<div class="answer-cell"><span class="q-num">2</span><span class="q-ans">C</span></div>'
        '</div></div></div>'
    )


@pytest.fixture()
def synthetic_page(browser, site_url):
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    origin = site_url.removesuffix("/index.html")

    def serve(route):
        path = urlparse(route.request.url).path
        if not route.request.url.startswith(origin + "/"):
            route.abort()
        elif path.startswith("/data/"):
            year = re.search(r"year-(\d+)\.txt$", path).group(1)
            if path.startswith("/data/subjects/"):
                html = synthetic_card(year, path.split("/")[3])
            else:
                html = (
                    f'<div class="year-section" id="year-{year}">'
                    f'<h2 class="year-heading">{year}年</h2>'
                    + synthetic_card(year, "constitution")
                    + synthetic_card(year, "chinese")
                    + '</div>'
                )
            route.fulfill(status=200, content_type="text/plain; charset=utf-8", body=html)
        else:
            route.continue_()

    page.route("**/*", serve)
    page.goto(site_url, wait_until="load")
    page.locator("#year-114 fieldset.mc-field").first.wait_for(state="attached")
    yield page
    page.close()
    assert errors == []


def press_button(page, selector):
    page.locator(selector).focus()
    page.keyboard.press("Enter")


def synthetic_field(page, view, year="114", question=0, subject=1):
    field = page.locator(
        f'#{view}View fieldset.mc-field[data-akey="y{year}-{subject}-q{question}"]'
    )
    field.wait_for(state="attached")
    return field


def assert_feedback(field, chosen, answer="A"):
    state = field.evaluate(
        """field => {
            const values = selector => [...field.querySelectorAll(selector)].map(radio => radio.value);
            const verdict = field.querySelector('.mc-verdict');
            return {
                checked: values('input:checked'),
                selected: values('.mc-option.selected input'),
                correct: values('.mc-option.correct input'),
                wrong: values('.mc-option.wrong input'),
                verdict: verdict.textContent,
                kind: verdict.className,
                role: verdict.getAttribute('role'),
                live: verdict.getAttribute('aria-live'),
            };
        }"""
    )
    assert state["checked"] == state["selected"] == [chosen]
    assert state["correct"] == ([answer] if answer else [])
    assert state["wrong"] == ([chosen] if answer and chosen != answer else [])
    kind, message = ("na", "無標準答案") if not answer else (
        ("ok", "答對") if chosen == answer else ("err", "答錯")
    )
    assert state["kind"] == f"mc-verdict {kind}"
    assert message in state["verdict"]
    assert state["role"] == "status" and state["live"] == "polite"


def assert_no_feedback(page):
    assert page.locator("input.mc-radio:checked").count() == 0
    assert page.locator(".mc-option.selected, .mc-option.correct, .mc-option.wrong, .mc-option.shake").count() == 0
    assert page.locator(".mc-verdict").evaluate_all(
        "verdicts => verdicts.every(verdict => !verdict.textContent && verdict.className === 'mc-verdict')"
    )


@pytest.mark.parametrize("first_view", ["year", "subject"])
def test_synthetic_feedback_syncs_both_directions_and_first_attempt_score(synthetic_page, first_view):
    page = synthetic_page
    practice_on(page)
    year = "114" if first_view == "year" else "113"
    if first_view == "subject":
        assert page.locator("#year-113 .mc-field").count() == 0
        press_button(page, "#viewBySubject")
    field = synthetic_field(page, first_view, year)
    open_card(field)
    chosen = "B" if first_view == "year" else "A"
    choose(page, field, chosen)
    expected_score = {"correct": int(chosen == "A"), "total": 1}
    assert_feedback(field, chosen)
    assert score(page) == expected_score

    other_view = "subject" if first_view == "year" else "year"
    press_button(page, "#viewBySubject" if other_view == "subject" else "#viewByYear")
    if other_view == "year":
        press_button(page, "#year-113 button")
    other = synthetic_field(page, other_view, year)
    open_card(other)
    assert_feedback(other, chosen)
    assert field.locator("input").first.get_attribute("name") != other.locator("input").first.get_attribute("name")
    other.locator("input:checked").focus()
    page.keyboard.press("ArrowUp" if chosen == "B" else "ArrowDown")
    changed = "A" if chosen == "B" else "B"
    assert_feedback(other, changed)
    assert other.locator("input:checked").evaluate("radio => radio === document.activeElement")
    assert_feedback(field, changed)
    press_button(page, "#viewByYear" if first_view == "year" else "#viewBySubject")
    assert_feedback(field, changed)
    assert score(page) == expected_score
    choose(page, field, chosen)
    assert_feedback(other, chosen)
    assert score(page) == expected_score


def test_synthetic_subject_rebuild_restores_feedback_without_recounting(synthetic_page):
    page = synthetic_page
    practice_on(page)
    year_field = synthetic_field(page, "year")
    open_card(year_field)
    choose(page, year_field, "B")
    press_button(page, "#viewBySubject")
    subject_field = synthetic_field(page, "subject")
    assert_feedback(subject_field, "B")
    old_node = subject_field.element_handle()
    page.locator("#subjectFilter").select_option("國文")
    other_subject = synthetic_field(page, "subject", subject=2)
    choose(page, other_subject, "A")
    assert not old_node.evaluate("field => field.isConnected")
    page.locator("#subjectFilter").select_option("憲法")
    rebuilt = synthetic_field(page, "subject")
    assert_feedback(rebuilt, "B")
    choose(page, rebuilt, "A")
    assert_feedback(year_field, "A")
    assert score(page) == {"correct": 1, "total": 2}


def test_synthetic_restored_selection_keeps_keyboard_and_accessibility_state(synthetic_page):
    page = synthetic_page
    practice_on(page)
    year_field = synthetic_field(page, "year")
    open_card(year_field)
    choose(page, year_field, "B")
    press_button(page, "#viewBySubject")
    field = synthetic_field(page, "subject")
    header = field.locator("xpath=ancestor::div[contains(@class, 'subject-card')]").locator(".subject-header")
    header.focus()
    page.keyboard.press("Enter")
    assert header.get_attribute("aria-expanded") == "false"
    page.keyboard.press("Space")
    assert header.get_attribute("aria-expanded") == "true"
    page.keyboard.press("Tab")
    selected = field.locator('input[value="B"]')
    assert selected.evaluate("radio => radio === document.activeElement")
    page.keyboard.press("Tab")
    next_field = synthetic_field(page, "subject", question=1)
    assert next_field.locator("input").first.evaluate("radio => radio === document.activeElement")
    page.keyboard.press("Shift+Tab")
    assert selected.evaluate("radio => radio === document.activeElement")
    snapshot = field.aria_snapshot()
    assert 'group "第1題：合成測試題 1"' in snapshot
    assert 'radio "(B) 測試選項 B" [checked]' in snapshot
    assert "status: 第1題：答錯了，正確答案是 A" in snapshot
    assert_feedback(field, "B")
    assert score(page) == {"correct": 0, "total": 1}


@pytest.mark.parametrize("reset_method", ["score", "toggle"])
def test_synthetic_reset_clears_mounted_and_evicted_feedback(synthetic_page, reset_method):
    page = synthetic_page
    practice_on(page)
    year_field = synthetic_field(page, "year")
    open_card(year_field)
    choose(page, year_field, "B")
    press_button(page, "#viewBySubject")
    choose(page, synthetic_field(page, "subject", "113"), "A")
    page.locator("#subjectFilter").select_option("國文")
    choose(page, synthetic_field(page, "subject", subject=2), "A")
    assert score(page) == {"correct": 2, "total": 3}
    if reset_method == "score":
        press_button(page, ".score-reset")
    else:
        press_button(page, "#practiceToggle")
        assert page.locator("input.mc-radio:not(:disabled)").count() == 0
        press_button(page, "#practiceToggle")
    assert_no_feedback(page)
    page.locator("#subjectFilter").select_option("憲法")
    rebuilt = synthetic_field(page, "subject")
    assert_no_feedback(page)
    press_button(page, "#viewByYear")
    press_button(page, "#year-113 button")
    synthetic_field(page, "year", "113")
    assert_no_feedback(page)
    assert score(page) == {"correct": 0, "total": 0}
    press_button(page, "#viewBySubject")
    choose(page, rebuilt, "A")
    assert_feedback(year_field, "A")
    assert score(page) == {"correct": 1, "total": 1}


def test_synthetic_missing_answer_feedback_survives_rebuild_without_scoring(synthetic_page):
    page = synthetic_page
    practice_on(page)
    field = synthetic_field(page, "year", question=2)
    open_card(field)
    choose(page, field, "B")
    press_button(page, "#viewBySubject")
    assert_feedback(synthetic_field(page, "subject", question=2), "B", answer="")
    page.locator("#subjectFilter").select_option("國文")
    synthetic_field(page, "subject", subject=2)
    page.locator("#subjectFilter").select_option("憲法")
    assert_feedback(synthetic_field(page, "subject", question=2), "B", answer="")
    assert score(page) == {"correct": 0, "total": 0}
