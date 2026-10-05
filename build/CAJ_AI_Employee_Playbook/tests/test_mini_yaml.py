import unittest

from _paths import ROOT
from scripts import mini_yaml as my


class MiniYamlTests(unittest.TestCase):
    def test_scalars_and_list(self):
        text = """# comment
currency: USD
count: 3
ratio: 2.5
flag: false
nothing: ~
quoted: "a: b # not a comment"
items:
  - name: one
    amount: 0   # trailing comment
    verified: true
  - name: two
    note: 'x'
"""
        data = my.loads(text)
        self.assertEqual(data["currency"], "USD")
        self.assertEqual(data["count"], 3)
        self.assertEqual(data["ratio"], 2.5)
        self.assertIs(data["flag"], False)
        self.assertIsNone(data["nothing"])
        self.assertEqual(data["quoted"], "a: b # not a comment")
        self.assertEqual(data["items"], [{"name": "one", "amount": 0, "verified": True},
                                         {"name": "two", "note": "x"}])

    def test_rejects_unsupported_syntax(self):
        for bad in ("a: [1, 2]\n", "a: {b: 1}\n", "a:\n  b: 1\n", "a: 1\na: 2\n", "  - x: 1\n",
                    "a:\n  - b:\n", "a: 'open\n", "a:\n\t- b: 1\n", "just text\n",
                    "a:\n  - b: 1\n      c: 2\n", "a:\n  - b: 1\n    b: 2\n"):
            with self.subTest(bad=bad):
                with self.assertRaises(my.MiniYamlError):
                    my.loads(bad)

    def test_repo_rates_file_parses(self):
        data = my.loads((ROOT / "rates.yaml").read_text(encoding="utf-8"))
        self.assertEqual(data["currency"], "USD")
        self.assertTrue(all(r["verified"] is False for r in data["rates"]))
        self.assertTrue(all(r["evidence"] == "NEEDS_EVIDENCE" for r in data["rates"]))


if __name__ == "__main__":
    unittest.main()
