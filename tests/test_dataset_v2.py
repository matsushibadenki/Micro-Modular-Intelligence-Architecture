import copy
import unittest
from collections import Counter

from mmia.dataset_v2 import audit_v2, expected_answer, generate_v2
from mmia.train_pilot import choose_rows, choose_stratified_rows


class DatasetV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = generate_v2(groups_per_cell=4)

    def test_reproducible_and_expected_size(self):
        self.assertEqual(self.rows, generate_v2(groups_per_cell=4))
        self.assertNotEqual(self.rows, generate_v2(seed=7, groups_per_cell=4))
        self.assertEqual(len(self.rows), 4 * 3 * 3 * 4 * 3)

    def test_balanced_cells_and_logic_labels(self):
        report = audit_v2(self.rows, 4)
        self.assertEqual(set(report["cell_counts"].values()), {4})
        self.assertEqual(set(report["logic_label_counts"].values()), {2})

    def test_templates_are_split_exclusive(self):
        templates = {}
        for row in self.rows:
            templates.setdefault(row["template_id"], set()).add(row["split"])
        self.assertTrue(all(len(splits) == 1 for splits in templates.values()))

    def test_each_group_has_matching_translations(self):
        groups = Counter(row["group_id"] for row in self.rows)
        self.assertEqual(set(groups.values()), {3})

    def test_all_targets_recomputed_from_structured_parameters(self):
        for row in self.rows:
            self.assertEqual(row["answer"], expected_answer(row))

    def test_wrong_target_rejected(self):
        rows = copy.deepcopy(self.rows)
        group_id = rows[0]["group_id"]
        for row in rows:
            if row["group_id"] == group_id:
                row["answer"] = str(int(row["answer"]) + 1)
        with self.assertRaisesRegex(ValueError, "Incorrect target"):
            audit_v2(rows, 4)

    def test_logic_imbalance_rejected(self):
        rows = copy.deepcopy(self.rows)
        group_id = next(r["group_id"] for r in rows if r["domain"] == "logic" and r["answer"] == "0")
        for row in rows:
            if row["group_id"] == group_id:
                row["answer"] = "1"
                row["parameters"][-1] = 1
        with self.assertRaisesRegex(ValueError, "Logic labels"):
            audit_v2(rows, 4)

    def test_bad_cell_count_rejected(self):
        removed = self.rows[0]["group_id"]
        rows = [row for row in self.rows if row["group_id"] != removed]
        with self.assertRaisesRegex(ValueError, "Unbalanced"):
            audit_v2(rows, 4)

    def test_training_sample_selection_is_reproducible_and_train_only(self):
        first = choose_rows(self.rows, seed=12, limit=5)
        self.assertEqual(first, choose_rows(self.rows, seed=12, limit=5))
        self.assertTrue(all(row["split"] == "train" for row in first))
        with self.assertRaises(ValueError):
            choose_rows(self.rows, seed=12, limit=0)

    def test_stratified_selection_balances_cells_without_translation_reuse(self):
        selected = choose_stratified_rows(self.rows, seed=12, samples_per_cell=1)
        self.assertEqual(selected, choose_stratified_rows(self.rows, seed=12, samples_per_cell=1))
        counts = Counter((row["domain"], row["language"], row["difficulty"]) for row in selected)
        self.assertEqual(set(counts.values()), {1})
        self.assertEqual(len(selected), 4 * 3 * 3)
        self.assertEqual(len({row["group_id"] for row in selected}), len(selected))
        with self.assertRaises(ValueError):
            choose_stratified_rows(self.rows, seed=12, samples_per_cell=2)


if __name__ == "__main__":
    unittest.main()
