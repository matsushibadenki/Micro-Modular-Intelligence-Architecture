import unittest

from scripts.align_stage_predictions import align


class AlignStagePredictionTests(unittest.TestCase):
    def test_replaces_only_id_and_rejects_duplicate_source(self):
        row = {"id": "s2-x", "source_id": "x", "prediction": "7", "correct": True}
        result = align([row])[0]
        self.assertEqual(result["id"], "x")
        self.assertEqual(result["stage_view_id"], "s2-x")
        self.assertEqual(result["prediction"], "7")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            align([row, row])


if __name__ == "__main__":
    unittest.main()
