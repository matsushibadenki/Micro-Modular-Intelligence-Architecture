import unittest

from mmia.dataset_v3 import generate_v3
from scripts.build_predicted_stage2 import build


class PredictedStage2Tests(unittest.TestCase):
    def test_prediction_is_inserted_and_upstream_result_retained(self):
        source = [row for row in generate_v3(groups_per_cell=2) if row["split"] == "validation"]
        predictions = [{"source_id": row["id"], "prediction": "777", "status": "ok",
                        "format_valid": True, "correct": False,
                        "completion_seconds": 0.1} for row in source]
        output = build(source, predictions)
        self.assertTrue(all("777" in row["prompt"] for row in output))
        self.assertTrue(all(not row["upstream_correct"] for row in output))
        self.assertEqual({row["id"] for row in output}, {row["id"] for row in source})

    def test_incomplete_coverage_is_rejected(self):
        source = [row for row in generate_v3(groups_per_cell=2) if row["split"] == "validation"]
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            build(source, [])


if __name__ == "__main__":
    unittest.main()
