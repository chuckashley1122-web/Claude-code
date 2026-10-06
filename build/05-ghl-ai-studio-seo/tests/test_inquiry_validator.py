import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import constants as C  # noqa: E402
from src import inquiry_validator as V  # noqa: E402

CFG = {"service_allowlist": ["synthetic_test_service"], "allowed_source_origins": ["https://example.com"]}


def good(**overrides):
    body = {"submission_id": "synthetic-0001", "name": "Synthetic Tester", "email": "tester@example.com",
            "service_interest": "synthetic_test_service"}
    body.update(overrides)
    return body


def codes(errors):
    return {(e["field"], e["code"]) for e in errors}


class Normalize(unittest.TestCase):
    def test_trim_collapse_lowercase_phone(self):
        n = V.normalize({"name": "  Synthetic \t  Tester ", "email": " Tester@Example.COM ",
                         "phone": "+1 (512) 555-0100", "message": "line  one\r\n\r\n\r\n\r\nline   two  ",
                         "consent": "on"})
        self.assertEqual(n["name"], "Synthetic Tester")
        self.assertEqual(n["email"], "tester@example.com")
        self.assertEqual(n["phone"], "+15125550100")
        self.assertEqual(n["message"], "line one\n\nline two")
        self.assertIs(n["consent"], True)

    def test_phone_without_plus(self):
        self.assertEqual(V.normalize({"phone": "512.555.0101"})["phone"], "5125550101")


class Validate(unittest.TestCase):
    def test_valid(self):
        ok, errors = V.validate(V.normalize(good(phone="512-555-0100", source_page="https://example.com/contact",
                                                 consent=True, service_area="Example area")), CFG)
        self.assertTrue(ok, errors)

    def test_required_fields(self):
        ok, errors = V.validate({}, CFG)
        self.assertFalse(ok)
        self.assertTrue({("name", "required"), ("submission_id", "required"), ("service_interest", "required"),
                         ("contact", "one_contact_method_required")} <= codes(errors))

    def test_contact_methods(self):
        self.assertTrue(V.validate(good(email="", phone="5125550100"), CFG)[0])
        ok, errors = V.validate(good(email="not-an-email"), CFG)
        self.assertIn(("email", "invalid"), codes(errors))
        ok, errors = V.validate(good(phone="12345"), CFG)
        self.assertIn(("phone", "invalid"), codes(errors))

    def test_allowlist(self):
        self.assertIn(("service_interest", "not_in_allowlist"), codes(V.validate(good(service_interest="x"), CFG)[1]))
        # shipped config: allowlist is NEEDS_EVIDENCE -> empty -> reject all
        self.assertIn(("service_interest", "service_allowlist_unconfigured"), codes(V.validate(good())[1]))

    def test_lengths_and_payload(self):
        self.assertIn(("name", "too_long"), codes(V.validate(good(name="n" * (C.MAX_NAME_LEN + 1)), CFG)[1]))
        self.assertTrue(V.validate(good(name="n" * C.MAX_NAME_LEN), CFG)[0])
        self.assertIn(("message", "too_long"),
                      codes(V.validate(good(message="m" * (C.MAX_MESSAGE_LEN + 1)), CFG)[1]))
        big = good(service_area="a" * 100, message="m" * C.MAX_MESSAGE_LEN)
        self.assertTrue(V.validate(big, CFG)[0])
        self.assertIn(("_body", "payload_too_large"),
                      codes(V.validate(big, {**CFG, "max_payload_bytes": 500})[1]))

    def test_privileged_and_unknown_fields(self):
        for field in C.INQUIRY_PRIVILEGED_FIELDS_REJECTED:
            with self.subTest(field=field):
                self.assertIn((field, "privileged_field_rejected"), codes(V.validate(good(**{field: "x"}), CFG)[1]))
        self.assertIn(("utm_hack", "unknown_field"), codes(V.validate(good(utm_hack="x"), CFG)[1]))

    def test_source_origin(self):
        self.assertIn(("source_page", "origin_not_allowed"),
                      codes(V.validate(good(source_page="https://evil.example.net/x"), CFG)[1]))
        self.assertIn(("source_page", "invalid_url"),
                      codes(V.validate(good(source_page="javascript:alert(1)"), CFG)[1]))
        self.assertIn(("source_page", "source_origins_unconfigured"),
                      codes(V.validate(good(source_page="https://example.com/x"),
                                       {**CFG, "allowed_source_origins": []})[1]))

    def test_types_and_submission_id(self):
        self.assertIn(("name", "must_be_string"), codes(V.validate(good(name=5), CFG)[1]))
        self.assertIn(("consent", "must_be_boolean"), codes(V.validate(good(consent="maybe"), CFG)[1]))
        self.assertIn(("submission_id", "invalid_format"), codes(V.validate(good(submission_id="a b"), CFG)[1]))
        self.assertEqual(V.validate([], CFG), (False, [{"field": "_body", "code": "not_an_object"}]))

    def test_errors_never_echo_values(self):
        _, errors = V.validate(good(email="secret-person@example.com-bad"), CFG)
        self.assertNotIn("secret-person", repr(errors))


class EscapeAndRedact(unittest.TestCase):
    def test_escape(self):
        self.assertEqual(V.escape_for_display('<b onclick="x">&'), "&lt;b onclick=&quot;x&quot;&gt;&amp;")

    def test_redact(self):
        out = V.redact_pii({"name": "Synthetic Tester", "email": "tester@example.com", "submission_id": "s-1",
                            "nested": [{"phone": "5125550100"}], "note": "mail tester@example.com or +1 512 555 0100",
                            "when": "2026-10-05 12:30"})
        self.assertEqual(out["name"], "[REDACTED]")
        self.assertEqual(out["email"], "[REDACTED]")
        self.assertEqual(out["submission_id"], "s-1")
        self.assertEqual(out["nested"][0]["phone"], "[REDACTED]")
        self.assertNotIn("tester@example.com", out["note"])
        self.assertNotIn("555", out["note"])
        self.assertEqual(out["when"], "2026-10-05 12:30")


if __name__ == "__main__":
    unittest.main()
