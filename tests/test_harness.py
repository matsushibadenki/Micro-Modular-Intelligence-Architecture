import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mmia.harness import generate, validate_rows, score, summarize, run


class HarnessTests(unittest.TestCase):
    def test_repeatability_and_split_integrity(self):
        rows = generate()
        self.assertEqual(rows, generate())
        self.assertNotEqual(rows, generate(seed=9))
        self.assertEqual(len(rows), 120)
        for split, expected in [("train", 72), ("validation", 24), ("test", 24)]:
            self.assertEqual(sum(r["split"] == split for r in rows), expected)
        validate_rows(rows)

    def test_leakage_rejected(self):
        rows = copy.deepcopy(generate())
        rows[0]["split"] = "test" if rows[1]["split"] != "test" else "train"
        with self.assertRaisesRegex(ValueError, "leaks"):
            validate_rows(rows)

    def test_answer_contract_and_censored_answers(self):
        self.assertTrue(score("  +0042\n", "42")["correct"])
        for text in ["The answer is 42", "42 or 43", "42.0", "４２", "", "4.2e1"]:
            self.assertFalse(score(text, "42")["correct"])
        for status in ["truncated", "timeout", "error"]:
            self.assertFalse(score("42", "42", status)["correct"])

    def test_known_semantics(self):
        for row in generate():
            p = row["parameters"]
            if row["domain"] == "math":
                expected = (p[0] + p[1]) * p[2]
            elif row["domain"] == "physics":
                expected = p[0] * p[1]
            elif row["domain"] == "coding":
                # Python's trusted generator values only; never execute model output.
                expected = sum(p[1:])
            else:
                expected = 0 if p[3] else 1
            self.assertEqual(int(row["answer"]), expected)

    def test_failure_stays_in_denominator(self):
        good = {"domain": "math", "language": "en", "status": "ok",
                "correct": True, "format_valid": True, "completion_seconds": 1,
                "ttft_seconds": .1}
        bad = {**good, "status": "timeout", "correct": False, "completion_seconds": 30}
        result = summarize([good, bad])["all"]
        self.assertEqual(result["accuracy"], .5)
        self.assertEqual(result["successful_latency_count"], 1)
        self.assertEqual(result["non_ok"], 1)

    def test_setup_failure_persisted_and_no_overwrite(self):
        import json
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "failed"
            with self.assertRaises(ValueError):
                run({"max_new_tokens": 0, "timeout_seconds": 1, "cpu_threads": 1}, output)
            self.assertEqual(json.loads((output / "manifest.json").read_text())["status"], "failed")
            with self.assertRaises(FileExistsError):
                run({}, output)


if __name__ == "__main__":
    unittest.main()
