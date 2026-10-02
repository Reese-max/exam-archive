import os
import re
import shutil
from pathlib import Path

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
def page(browser):
    page = browser.new_page()
    page.goto(INDEX.as_uri(), wait_until="load")
    yield page
    page.close()


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
