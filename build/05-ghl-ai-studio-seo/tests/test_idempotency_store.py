import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.idempotency_store import IdempotencyStore  # noqa: E402


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


class IdempotencyStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock = Clock()
        self.store = IdempotencyStore(Path(self.tmp.name) / "idem.db", clock=self.clock)

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_claim_then_replay_prior_outcome(self):
        claimed, rec = self.store.begin("sub-00000001")
        self.assertTrue(claimed)
        self.assertEqual(rec.state, "in_flight")
        self.store.complete("sub-00000001", "saved", 201, {"inquiry_reference": "inq_x"}, "crm-1")
        claimed, rec = self.store.begin("sub-00000001")
        self.assertFalse(claimed)
        self.assertEqual((rec.state, rec.response_status, rec.response_body, rec.crm_reference),
                         ("saved", 201, {"inquiry_reference": "inq_x"}, "crm-1"))
        self.assertEqual(self.store.count(), 1)

    def test_in_flight_is_not_claimed_twice(self):
        self.assertTrue(self.store.begin("sub-00000002")[0])
        claimed, rec = self.store.begin("sub-00000002")
        self.assertFalse(claimed)
        self.assertEqual(rec.state, "in_flight")

    def test_failed_can_be_reattempted_with_same_id(self):
        self.store.begin("sub-00000003")
        self.store.complete("sub-00000003", "failed", 503, {"error": "x"})
        claimed, rec = self.store.begin("sub-00000003")
        self.assertTrue(claimed)
        self.assertEqual(self.store.count(), 1)

    def test_queued_is_final(self):
        self.store.begin("sub-00000004")
        self.store.complete("sub-00000004", "queued", 202, {"status": "received_for_processing"}, "q-1")
        self.assertFalse(self.store.begin("sub-00000004")[0])

    def test_complete_requires_in_flight(self):
        with self.assertRaises(ValueError):
            self.store.complete("missing-000", "saved", 201, {})
        self.store.begin("sub-00000005")
        with self.assertRaises(ValueError):
            self.store.complete("sub-00000005", "in_flight", 201, {})

    def test_retention_and_purge(self):
        self.store.begin("old-00000001")
        self.store.complete("old-00000001", "saved", 201, {}, "crm-old")
        self.clock.now += timedelta(hours=23)
        self.assertIsNotNone(self.store.get("old-00000001"))
        self.clock.now += timedelta(hours=2)
        self.assertIsNone(self.store.get("old-00000001"))
        self.store.begin("new-00000001")
        self.assertEqual(self.store.purge_expired(), 1)
        self.assertEqual(self.store.count(), 1)

    def test_expired_record_is_reclaimable(self):
        self.store.begin("exp-00000001")
        self.store.complete("exp-00000001", "saved", 201, {}, "crm")
        self.clock.now += timedelta(hours=25)
        self.assertTrue(self.store.begin("exp-00000001")[0])

    def test_persists_across_instances(self):
        self.store.begin("per-00000001")
        self.store.complete("per-00000001", "saved", 201, {"a": 1}, "crm")
        again = IdempotencyStore(Path(self.tmp.name) / "idem.db", clock=self.clock)
        self.assertEqual(again.get("per-00000001").response_body, {"a": 1})

    def test_concurrent_claims_only_one_wins(self):
        results = []
        barrier = threading.Barrier(8)

        def worker():
            store = IdempotencyStore(Path(self.tmp.name) / "idem.db", clock=self.clock)
            barrier.wait()
            results.append(store.begin("race-0000001")[0])

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(results.count(True), 1)


if __name__ == "__main__":
    unittest.main()
