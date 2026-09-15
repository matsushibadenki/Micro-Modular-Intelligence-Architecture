import copy
import unittest
from collections import Counter

from mmia.dataset_v3 import COMPOSITIONS, audit_v3, compute, generate_v3


class DatasetV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = generate_v3(groups_per_cell=4)

    def test_reproducible_balanced_size(self):
        self.assertEqual(self.rows, generate_v3(groups_per_cell=4))
        self.assertEqual(len(self.rows), len(COMPOSITIONS) * 3 * 3 * 4 * 3)
        groups = {row["group_id"]: row for row in self.rows}
        counts = Counter((r["domain"], r["split"], r["difficulty"]) for r in groups.values())
        self.assertEqual(set(counts.values()), {4})

    def test_every_problem_has_two_distinct_skills(self):
        self.assertTrue(all(len(row["composition"]) == 2 for row in self.rows))
        self.assertTrue(all(row["composition"][0] != row["composition"][1] for row in self.rows))

    def test_targets_and_intermediates_recompute(self):
        for row in self.rows:
            self.assertEqual((row["intermediate_answers"], row["answer"]), compute(row))

    def test_logic_branches_are_balanced(self):
        report = audit_v3(self.rows, 4)
        self.assertEqual(set(report["logic_branch_counts"].values()), {2})

    def test_corrupt_intermediate_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        group = rows[0]["group_id"]
        for row in rows:
            if row["group_id"] == group:
                row["intermediate_answers"] = ["999"]
        with self.assertRaisesRegex(ValueError, "Incorrect target or intermediate"):
            audit_v3(rows, 4)

    def test_templates_are_split_exclusive(self):
        templates = {}
        for row in self.rows:
            templates.setdefault(row["template_id"], set()).add(row["split"])
        self.assertTrue(all(len(splits) == 1 for splits in templates.values()))


if __name__ == "__main__":
    unittest.main()
