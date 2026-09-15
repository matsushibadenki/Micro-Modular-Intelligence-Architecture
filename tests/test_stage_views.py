import copy
import unittest

from mmia.dataset_v3 import generate_v3
from mmia.stage_views import audit_views, make_views


class StageViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = generate_v3(groups_per_cell=2)
        cls.stage1, cls.stage2 = make_views(cls.source)

    def test_views_preserve_rows_groups_and_targets(self):
        report = audit_views(self.source, self.stage1, self.stage2)
        self.assertTrue(report["identity_preserved"])
        self.assertEqual(len(self.source), len(self.stage1))
        self.assertEqual(len(self.source), len(self.stage2))

    def test_stage_prompts_are_distinct_and_multilingual(self):
        for source, first, second in zip(self.source, self.stage1, self.stage2):
            self.assertNotEqual(source["prompt"], first["prompt"])
            self.assertNotEqual(first["prompt"], second["prompt"])
            self.assertEqual(source["language"], first["language"])

    def test_corrupt_teacher_value_is_rejected(self):
        stage2 = copy.deepcopy(self.stage2)
        stage2[0]["prompt"] = stage2[0]["prompt"].replace(self.stage1[0]["answer"], "missing")
        with self.assertRaisesRegex(ValueError, "Teacher intermediate missing"):
            audit_views(self.source, self.stage1, stage2)


if __name__ == "__main__":
    unittest.main()
