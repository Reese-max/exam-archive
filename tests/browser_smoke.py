"""Real Chromium smoke for the generated, lazily loaded archive.

Run separately from the fast contract suite:
  python -m pip install -r requirements-browser.txt
  python -m playwright install chromium
  python tests/browser_smoke.py
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import unittest
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class ArchiveBrowserSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT))
        )
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 720})
        # Fonts are optional; core journeys must work without an external origin.
        self.context.route("**/*", lambda route: route.continue_()
                           if route.request.url.startswith(self.origin + "/")
                           else route.abort())
        self.page = self.context.new_page()
        self.page.set_default_timeout(7000)
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda request: self.requests.append(urlparse(request.url).path))

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], "archive journey must not throw browser errors")

    def open_archive(self, suffix=""):
        self.page.goto(self.origin + "/" + suffix)
        expect(self.page.locator("#year-114 .subject-card")).to_have_count(7)

    def assert_reflow(self):
        widths = self.page.evaluate("({content: document.documentElement.scrollWidth, viewport: innerWidth})")
        self.assertLessEqual(widths["content"], widths["viewport"] + 1)

    def test_first_result_fetches_one_year_and_keyboard_opens_a_question(self):
        self.open_archive()
        self.assertEqual([p for p in self.requests if p.startswith("/data/")], ["/data/year-114.txt"])
        expect(self.page.locator("#yearView .subject-card")).to_have_count(7)
        header = self.page.locator("#year-114 .subject-header").first
        header.focus()
        self.page.keyboard.press("Enter")
        expect(header).to_have_attribute("aria-expanded", "true")
        expect(self.page.locator("#year-114 .subject-body").first).to_be_visible()
        self.page.keyboard.press("Space")
        expect(header).to_have_attribute("aria-expanded", "false")

    def test_keyboard_search_loads_scope_and_announces_expanded_results(self):
        self.open_archive()
        self.page.keyboard.press("/")
        search = self.page.locator("#searchInput")
        expect(search).to_be_focused()
        search.fill("警察")
        expect(self.page.locator("#searchStats")).to_contain_text("找到")
        self.assertEqual(len(set(p for p in self.requests if p.startswith("/data/year-"))), 10)
        opened = self.page.locator("#yearView .subject-card.open .subject-header")
        self.assertGreater(opened.count(), 0)
        for header in opened.all():
            expect(header).to_have_attribute("aria-expanded", "true")
        self.page.keyboard.press("Escape")
        expect(search).to_have_value("")
        expect(self.page.locator("#yearView .subject-card.open")).to_have_count(0)

    def test_mobile_navigation_loads_an_older_year_and_opens_its_question(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.open_archive()
        self.assert_reflow()
        self.page.locator("#hamburgerBtn").click()
        expect(self.page.locator("#hamburgerBtn")).to_have_attribute("aria-expanded", "true")
        self.page.locator(".sidebar-year").filter(has_text="113年").press("Enter")
        self.page.locator('.sidebar-link[href="#y113-93826"]').click()
        header = self.page.locator("#y113-93826 .subject-header")
        expect(header).to_have_attribute("aria-expanded", "true")
        expect(self.page.locator("#y113-93826 .subject-body")).to_be_visible()
        expect(self.page.locator("#hamburgerBtn")).to_have_attribute("aria-expanded", "false")
        self.assertEqual(set(p for p in self.requests if p.startswith("/data/")),
                         {"/data/year-114.txt", "/data/year-113.txt"})

    def test_200_percent_equivalent_reflow_keeps_search_and_question_usable(self):
        # Browser zoom at 200% halves a 1280px CSS viewport to 640px. This
        # checks reflow at that effective width, rather than claiming a device
        # or assistive-technology zoom test.
        self.page.set_viewport_size({"width": 640, "height": 360})
        self.open_archive()
        self.assert_reflow()
        self.page.keyboard.press("/")
        expect(self.page.locator("#searchInput")).to_be_focused()
        self.page.locator('.filter-chip[data-year="114"]').click()
        self.page.locator("#searchInput").fill("警察")
        expect(self.page.locator("#searchStats")).to_contain_text("找到")
        expect(self.page.locator("#year-114 .subject-card.open .subject-header").first).to_be_visible()
        self.assert_reflow()

    def test_subject_view_fetches_only_the_chosen_subject(self):
        self.open_archive()
        self.page.locator("#viewBySubject").click()
        expect(self.page.locator("#subjectView .subject-card")).to_have_count(10)
        category_requests = [p for p in self.requests if p.startswith("/data/subjects/")]
        self.assertEqual(len(category_requests), 10)
        self.assertTrue(all("/constitution/" in p for p in category_requests))
        header = self.page.locator("#subjectView .subject-header").first
        header.focus()
        self.page.keyboard.press("Space")
        expect(header).to_have_attribute("aria-expanded", "false")
        self.page.keyboard.press("Enter")
        expect(header).to_have_attribute("aria-expanded", "true")


if __name__ == "__main__":
    unittest.main(verbosity=2)
