import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse


INDEX_FILE = Path(__file__).with_name("index.html")
ALGORITHMS = (
    "rsasha256",
    "ecdsap256sha256",
    "ed25519",
    "ed448",
)
EXPECTED_PATTERNS = (
    "success",
    "keytag.ds.error",
    "hash.ds.error",
    "sign.ds.error",
    "sign.dnskey.error",
    "expire.dnskey.error",
    "corrupted.sign.a.error",
)
BASE_DOMAIN = "dnssec-check.jp"


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading = ""
        self.in_heading = False
        self.in_tbody = False
        self.current_row = None
        self.current_cell = None
        self.current_cell_links = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "table":
            self.tables.append({"heading": self.heading, "rows": []})
        elif tag == "h3":
            self.heading = ""
            self.in_heading = True
        elif tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.current_row = []
        elif tag == "td" and self.current_row is not None:
            self.current_cell = ""
            self.current_cell_links = []
        elif tag == "a" and self.current_cell is not None:
            href = attributes.get("href")
            if href:
                self.current_cell_links.append(href)

    def handle_data(self, data):
        if self.in_heading:
            self.heading += data
        if self.current_cell is not None:
            self.current_cell += data

    def handle_endtag(self, tag):
        if tag == "h3":
            self.in_heading = False
        elif tag == "td" and self.current_cell is not None:
            self.current_row.append(
                {
                    "text": " ".join(self.current_cell.split()),
                    "links": self.current_cell_links,
                }
            )
            self.current_cell = None
            self.current_cell_links = []
        elif tag == "tr" and self.current_row is not None:
            self.tables[-1]["rows"].append(self.current_row)
            self.current_row = None
        elif tag == "tbody":
            self.in_tbody = False


def parse_tables():
    parser = TableParser()
    parser.feed(INDEX_FILE.read_text(encoding="utf-8"))
    return parser.tables


def domains_in_cell(cell):
    return re.findall(r"[A-Za-z0-9.-]+\.dnssec-check\.jp", cell["text"])


class DomainNamingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = parse_tables()

    def assert_link_domain_matches_display(self, cell):
        linked_domains = [
            domain
            for link in cell["links"]
            for domain in parse_qs(urlparse(link).query).get("domain", [])
        ]
        displayed_domains = re.findall(
            r"[A-Za-z0-9.-]+\.dnssec-check\.jp", cell["text"]
        )
        self.assertEqual(linked_domains, displayed_domains, cell["text"])

    def test_algorithm_tables_have_consistent_domain_patterns(self):
        self.assertGreaterEqual(len(self.tables), 4)
        for table, algorithm in zip(self.tables[:4], ALGORITHMS):
            self.assertEqual(table["heading"].lower(), algorithm)
            self.assertEqual(len(table["rows"]), len(EXPECTED_PATTERNS))
            for row, pattern in zip(table["rows"], EXPECTED_PATTERNS):
                self.assertEqual(len(row), 4)
                chain_cell, a_record_cell = row[2], row[3]
                self.assert_link_domain_matches_display(chain_cell)
                self.assert_link_domain_matches_display(a_record_cell)

                expected_domain = f"{pattern}.{algorithm}.{BASE_DOMAIN}"
                self.assertEqual(
                    domains_in_cell(chain_cell), [expected_domain]
                    if pattern != "corrupted.sign.a.error"
                    else [],
                )
                expected_a_domain = f"www.{expected_domain}"
                self.assertEqual(domains_in_cell(a_record_cell), [expected_a_domain])

    def test_nsec_tables_use_consistent_names_and_links(self):
        self.assertEqual([table["heading"] for table in self.tables[4:6]], ["NSEC", "NSEC3"])
        expected_domains = (
            "missing.cover.mismatch.nsec.rsasha256.dnssec-check.jp",
            "target.type.mismatch.nsec.rsasha256.dnssec-check.jp",
            "missing.cover.mismatch.nsec3.rsasha256.dnssec-check.jp",
            "target.type.mismatch.nsec3.rsasha256.dnssec-check.jp",
        )
        actual_domains = []
        for table in self.tables[4:6]:
            for row in table["rows"]:
                self.assertEqual(len(row), 3)
                self.assert_link_domain_matches_display(row[2])
                actual_domains.extend(domains_in_cell(row[2]))
        self.assertEqual(actual_domains, list(expected_domains))


if __name__ == "__main__":
    unittest.main()
