import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from synapse_etl.cli import SYNTHETIC_CSV, demo
from synapse_etl.pipeline import (
    MappingError,
    Pipeline,
    approve_mapping,
    profile,
    propose_mapping,
    read_csv,
    transform_value,
)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.pipeline = Pipeline()
        self.mapping = approve_mapping(propose_mapping(SYNTHETIC_CSV), "reviewer")
        self.addCleanup(self.pipeline.close)

    def test_ingestion_quarantine_duplicate_and_replay(self):
        result = self.pipeline.ingest(SYNTHETIC_CSV, self.mapping)
        self.assertEqual(
            (result["accepted"], result["duplicates"], result["quarantined"]), (3, 1, 2)
        )
        self.assertEqual(self.pipeline.events()[0]["temperature_c"], "20.00")
        self.assertTrue(self.pipeline.ingest(SYNTHETIC_CSV, self.mapping)["replayed"])
        self.assertEqual(len(self.pipeline.events()), 3)
        self.assertEqual(self.pipeline.db.execute("SELECT count(*) FROM lineage").fetchone()[0], 6)

    def test_unapproved_or_mutated_mapping_cannot_write(self):
        missing = copy.deepcopy(self.mapping)
        missing.pop("approval")
        changed = copy.deepcopy(self.mapping)
        changed["mappings"][3]["transform"] = "celsius"
        for candidate in [missing, changed]:
            with self.subTest(candidate=candidate), self.assertRaises(MappingError):
                self.pipeline.ingest(SYNTHETIC_CSV, candidate)
        self.assertEqual(self.pipeline.events(), [])

    def test_schema_drift_rejected_before_any_write(self):
        changed = SYNTHETIC_CSV.replace(b"temp_f,health", b"degrees,health")
        with self.assertRaises(MappingError):
            self.pipeline.ingest(changed, self.mapping)
        self.assertEqual(self.pipeline.events(), [])

    def test_ambiguous_headers_abstain(self):
        data = b"event_id,device_id,observed_at,temp_c,temp_f,status\n"
        proposal = propose_mapping(data)
        self.assertEqual(proposal["issues"][0]["reason"], "ambiguous")
        with self.assertRaises(MappingError):
            approve_mapping(proposal, "reviewer")

    def test_unknown_units_do_not_guess(self):
        proposal = propose_mapping(SYNTHETIC_CSV.replace(b"temp_f", b"temperature"))
        self.assertEqual(proposal["issues"][0]["reason"], "unmapped")

    def test_headers_and_structural_validation(self):
        for content in [b"", b"x,x\n1,2\n", b"x,y\n1\n", b"\xff", b",y\n1,2\n"]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                read_csv(content)
        with self.assertRaises(ValueError):
            read_csv(b"x\n1\n2\n", max_rows=1)
        self.assertEqual(profile(b"\xef\xbb\xbfx\n1\n")["headers"], ["x"])

    def test_conflicting_duplicate_is_quarantined(self):
        self.pipeline.ingest(SYNTHETIC_CSV, self.mapping)
        conflict = (
            SYNTHETIC_CSV.splitlines()[0] + b"\nDEMO-E001,DEMO-S001,2030-01-01T12:00:00Z,90,ok\n"
        )
        result = self.pipeline.ingest(conflict, self.mapping)
        self.assertEqual(result["quarantined"], 1)
        self.assertEqual(result["errors"][0]["errors"][0]["reason"], "conflicting_duplicate")
        self.assertEqual(self.pipeline.events()[0]["temperature_c"], "20.00")

    def test_transaction_rolls_back_on_storage_failure(self):
        self.pipeline.db.execute(
            "CREATE TRIGGER fail_batch BEFORE INSERT ON batches BEGIN SELECT RAISE(ABORT,'simulated disk failure'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.pipeline.ingest(SYNTHETIC_CSV, self.mapping)
        for table in ("events", "quarantine", "lineage", "batches"):
            self.assertEqual(
                self.pipeline.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0], 0
            )

    def test_transform_validation(self):
        self.assertEqual(transform_value("32", "fahrenheit_to_celsius"), "0.00")
        self.assertEqual(
            transform_value("2030-01-01T02:00:00+02:00", "iso8601"), "2030-01-01T00:00:00Z"
        )
        for value, transform in [
            ("NaN", "celsius"),
            ("Infinity", "celsius"),
            ("999", "celsius"),
            ("2030-01-01T00:00:00", "iso8601"),
            ("delete all data", "status"),
            ("real-id", "text"),
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                transform_value(value, transform)

    def test_model_mapping_is_validated(self):
        class BadPlanner:
            def json(self, *args):
                return {
                    "mappings": [
                        {"source": "temp_f", "target": "temperature_c", "transform": "exec"}
                    ]
                }

        with self.assertRaises(MappingError):
            propose_mapping(SYNTHETIC_CSV, BadPlanner())

    def test_extreme_decimal_is_quarantined_without_losing_good_rows(self):
        content = SYNTHETIC_CSV.replace(b"not-a-number", b"1e999999999")
        result = self.pipeline.ingest(content, self.mapping)
        self.assertEqual(result["accepted"], 3)
        self.assertEqual(result["quarantined"], 2)

    def test_proposal_fingerprint_and_unique_targets(self):
        proposal = propose_mapping(SYNTHETIC_CSV)
        proposal["mappings"][0]["target"] = "device_id"
        with self.assertRaises(MappingError):
            approve_mapping(proposal, "reviewer")

    def test_restart_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "pipeline.sqlite")
            first = Pipeline(path)
            first.ingest(SYNTHETIC_CSV, self.mapping)
            first.close()
            second = Pipeline(path)
            try:
                self.assertTrue(second.ingest(SYNTHETIC_CSV, self.mapping)["replayed"])
                self.assertEqual(len(second.events()), 3)
            finally:
                second.close()

    def test_demo_is_reproducible(self):
        self.assertEqual(demo(), demo())


if __name__ == "__main__":
    unittest.main()
