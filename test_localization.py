import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from test_domains import TableParser, domains_in_cell


ROOT = Path(__file__).parent
PAGE_NAMES = tuple(sorted(path.name for path in ROOT.glob("*.html")))


class PageParser(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.elements = []
        self.text = []
        self.title = ""
        self.in_title = False
        self.feed(path.read_text(encoding="utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        if tag == "title":
            self.in_title = True

    def handle_data(self, data):
        self.text.append(data)
        if self.in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False


class LocalizationTest(unittest.TestCase):
    def test_japanese_and_english_page_sets_match(self):
        japanese_pages = {path.name for path in ROOT.glob("*.html")}
        english_pages = {path.name for path in (ROOT / "en").glob("*.html")}
        self.assertTrue(japanese_pages)
        self.assertEqual(japanese_pages, english_pages)

    def test_pages_have_responsive_semantic_structure(self):
        for directory in (ROOT, ROOT / "en"):
            for name in PAGE_NAMES:
                path = directory / name
                page = PageParser(path)
                tags = [tag for tag, _ in page.elements]
                headings = [
                    int(tag[1]) for tag in tags
                    if tag in ("h1", "h2", "h3", "h4", "h5", "h6")
                ]
                with self.subTest(path=path):
                    self.assertEqual(headings.count(1), 1)
                    self.assertTrue(headings)
                    self.assertTrue(
                        all(
                            current <= previous + 1
                            for previous, current in zip(headings, headings[1:])
                        )
                    )
                    self.assertEqual(tags.count("main"), 1)
                    self.assertTrue(
                        any(
                            tag == "meta"
                            and attrs.get("name") == "viewport"
                            for tag, attrs in page.elements
                        )
                    )

    def test_language_metadata_and_switches(self):
        for name in PAGE_NAMES:
            versions = {"ja": ROOT / name, "en": ROOT / "en" / name}
            for language, path in versions.items():
                with self.subTest(path=path):
                    page = PageParser(path)
                    html_elements = [
                        attrs for tag, attrs in page.elements if tag == "html"
                    ]
                    self.assertEqual(len(html_elements), 1)
                    self.assertEqual(html_elements[0].get("lang"), language)
                    self.assertTrue(page.title.strip())
                    alternatives = [
                        attrs for tag, attrs in page.elements
                        if tag == "link" and attrs.get("rel") == "alternate"
                    ]
                    self.assertEqual(len(alternatives), 2)
                    self.assertEqual(
                        {attrs["hreflang"] for attrs in alternatives}, {"ja", "en"}
                    )
                    for attrs in alternatives:
                        self.assertEqual(
                            (path.parent / attrs["href"]).resolve(),
                            versions[attrs["hreflang"]].resolve(),
                        )
                    other = "en" if language == "ja" else "ja"
                    switches = [
                        attrs for tag, attrs in page.elements
                        if tag == "a" and attrs.get("hreflang") == other
                        and not urlparse(attrs.get("href", "")).scheme
                    ]
                    self.assertEqual(len(switches), 1)
                    self.assertEqual(switches[0]["lang"], other)
                    self.assertEqual(
                        (path.parent / switches[0]["href"]).resolve(),
                        versions[other].resolve(),
                    )
                    current = [
                        attrs for _, attrs in page.elements
                        if attrs.get("aria-current") == "page"
                    ]
                    self.assertEqual(len(current), 1)
                    self.assertEqual(current[0]["lang"], language)

    def test_local_links_and_anchors_resolve(self):
        for directory in (ROOT, ROOT / "en"):
            for name in PAGE_NAMES:
                path = directory / name
                page = PageParser(path)
                ids = [attrs["id"] for _, attrs in page.elements if "id" in attrs]
                self.assertEqual(len(ids), len(set(ids)), path)
                for tag, attrs in page.elements:
                    if tag not in ("a", "link") or "href" not in attrs:
                        continue
                    link = urlparse(attrs["href"])
                    if link.scheme or link.netloc:
                        continue
                    with self.subTest(path=path, href=attrs["href"]):
                        target = path.parent / unquote(link.path) if link.path else path
                        if target.is_dir():
                            target /= "index.html"
                        self.assertTrue(target.is_file(), target)
                        if link.fragment:
                            target_page = PageParser(target)
                            self.assertIn(
                                unquote(link.fragment),
                                [attrs.get("id") for _, attrs in target_page.elements],
                            )

    def test_english_pages_are_translated_and_preserve_external_links(self):
        for name in PAGE_NAMES:
            japanese = PageParser(ROOT / name)
            english = PageParser(ROOT / "en" / name)
            with self.subTest(page=name):
                for text in english.text:
                    if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text):
                        self.assertEqual(text.strip(), "日本語")
                self.assertEqual(
                    [attrs["href"] for tag, attrs in japanese.elements
                     if tag == "a" and urlparse(attrs.get("href", "")).scheme],
                    [attrs["href"] for tag, attrs in english.elements
                     if tag == "a" and urlparse(attrs.get("href", "")).scheme],
                )
                self.assertEqual(
                    [attrs["id"] for _, attrs in japanese.elements if "id" in attrs],
                    [attrs["id"] for _, attrs in english.elements if "id" in attrs],
                )
                for tag in ("table", "tr", "td", "th", "h1", "h2", "h3", "pre"):
                    self.assertEqual(
                        sum(element == tag for element, _ in japanese.elements),
                        sum(element == tag for element, _ in english.elements),
                        tag,
                    )
                self.assertEqual(
                    [attrs["class"] for _, attrs in japanese.elements
                     if attrs.get("class", "").startswith("badge ")],
                    [attrs["class"] for _, attrs in english.elements
                     if attrs.get("class", "").startswith("badge ")],
                )

    def test_english_test_domains_match_japanese_tables(self):
        tables = []
        for path in (ROOT / "index.html", ROOT / "en/index.html"):
            parser = TableParser()
            parser.feed(path.read_text(encoding="utf-8"))
            tables.append(parser.tables)
        self.assertEqual(len(tables[0]), len(tables[1]))
        for japanese, english in zip(*tables):
            self.assertEqual(len(japanese["rows"]), len(english["rows"]))
            for japanese_row, english_row in zip(japanese["rows"], english["rows"]):
                self.assertEqual(len(japanese_row), len(english_row))
                for japanese_cell, english_cell in zip(japanese_row, english_row):
                    self.assertEqual(japanese_cell["links"], english_cell["links"])
                    self.assertEqual(
                        domains_in_cell(japanese_cell), domains_in_cell(english_cell)
                    )


if __name__ == "__main__":
    unittest.main()
