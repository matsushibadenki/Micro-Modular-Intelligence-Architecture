import json
import tempfile
import unittest
from pathlib import Path

from scripts.aggregate_r002 import aggregate


class AggregateR002Tests(unittest.TestCase):
    def test_averages_paired_group_differences_across_seeds(self):
        with tempfile.TemporaryDirectory() as directory:
            root, pairs = Path(directory), []
            for seed, candidate_scores in (("a", [1, 0, 1]), ("b", [1, 1, 1])):
                baseline, candidate = root / f"{seed}-b", root / f"{seed}-c"
                base_rows, candidate_rows = [], []
                for index, score in enumerate(candidate_scores):
                    row = {"id": f"id-{index}", "group_id": "group", "correct": False}
                    base_rows.append(row)
                    candidate_rows.append({**row, "correct": bool(score)})
                baseline.write_text("".join(json.dumps(r) + "\n" for r in base_rows))
                candidate.write_text("".join(json.dumps(r) + "\n" for r in candidate_rows))
                pairs.append((seed, baseline, candidate))
            report = aggregate(pairs, samples=100)
            self.assertAlmostEqual(report["mean_candidate_minus_baseline"], 5 / 6)
            self.assertEqual(report["semantic_groups"], 1)


if __name__ == "__main__":
    unittest.main()
