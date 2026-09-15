import json
import tempfile
import unittest
from pathlib import Path

from scripts.combine_specialist_predictions import combine


class CombineSpecialistsTests(unittest.TestCase):
    def test_requires_exact_domain_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "data.jsonl"
            rows = [{"id": domain, "domain": domain, "split": "validation"}
                    for domain in ("math", "physics", "coding", "logic")]
            dataset.write_text("".join(json.dumps(row) + "\n" for row in rows))
            inputs = {}
            for row in rows:
                path = root / f"{row['domain']}.jsonl"
                path.write_text(json.dumps({**row, "status": "ok", "correct": True,
                                            "format_valid": True,
                                            "completion_seconds": 1.0}) + "\n")
                inputs[row["domain"]] = path
            combined, hashes = combine(dataset, "validation", inputs)
            self.assertEqual(len(combined), 4)
            self.assertEqual(set(hashes), set(inputs))

            bad = json.loads(inputs["math"].read_text())
            bad["domain"] = "logic"
            inputs["math"].write_text(json.dumps(bad) + "\n")
            with self.assertRaisesRegex(ValueError, "specialist contains"):
                combine(dataset, "validation", inputs)

    def test_arbitrary_composition_domain_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "data.jsonl"
            prediction = root / "prediction.jsonl"
            row = {"id": "x", "domain": "code_to_math", "split": "validation"}
            dataset.write_text(json.dumps(row) + "\n")
            prediction.write_text(json.dumps({**row, "status": "ok", "correct": True,
                                               "format_valid": True,
                                               "completion_seconds": 1.0}) + "\n")
            records, _ = combine(dataset, "validation", {"code_to_math": prediction})
            self.assertEqual(records[0]["domain"], "code_to_math")


if __name__ == "__main__":
    unittest.main()
