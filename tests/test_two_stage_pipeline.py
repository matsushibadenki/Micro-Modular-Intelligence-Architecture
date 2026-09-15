import unittest

from scripts.analyze_two_stage_pipeline import analyze


class TwoStagePipelineTests(unittest.TestCase):
    def test_propagation_and_latency(self):
        stage1 = [{"source_id": "a", "correct": True, "completion_seconds": 1.0},
                  {"source_id": "b", "correct": False, "completion_seconds": 2.0}]
        stage2 = [{"id": "a", "correct": False, "completion_seconds": 3.0},
                  {"id": "b", "correct": True, "completion_seconds": 4.0}]
        result = analyze(stage1, stage2)
        self.assertEqual(result["final_correct_despite_wrong_intermediate"], 1)
        self.assertEqual(result["final_wrong_despite_correct_intermediate"], 1)
        self.assertEqual(result["end_to_end_completion_p50_seconds"], 5.0)


if __name__ == "__main__":
    unittest.main()
