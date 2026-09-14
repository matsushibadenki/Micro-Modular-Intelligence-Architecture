import unittest

from mmia.analysis import analyze, cluster_bootstrap_interval, group_metrics, paired_group_difference


def record(group, language, correct, domain="logic", difficulty="easy"):
    return {"group_id": group, "language": language, "correct": correct,
            "domain": domain, "difficulty": difficulty}


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            record("a", "en", True), record("a", "ja", True), record("a", "zh", True),
            record("b", "en", True), record("b", "ja", False), record("b", "zh", False),
        ]

    def test_group_metrics_do_not_count_translations_as_independent(self):
        result = group_metrics(self.rows)
        self.assertEqual(result["semantic_groups"], 2)
        self.assertAlmostEqual(result["translation_macro_accuracy"], 2 / 3)
        self.assertEqual(result["all_languages_correct_rate"], .5)
        self.assertEqual(result["any_language_correct_rate"], 1)

    def test_bootstrap_is_reproducible_and_bounded(self):
        first = cluster_bootstrap_interval(self.rows, samples=100)
        self.assertEqual(first, cluster_bootstrap_interval(self.rows, samples=100))
        self.assertGreaterEqual(first["lower_95"], 1 / 3)
        self.assertLessEqual(first["upper_95"], 1)

    def test_analysis_has_declared_slices(self):
        report = analyze(self.rows)
        self.assertEqual(set(report), {"all", "domain/logic", "difficulty/easy"})

    def test_incomplete_group_rejected(self):
        with self.assertRaisesRegex(ValueError, "three language"):
            group_metrics(self.rows[:-1])

    def test_paired_group_difference(self):
        baseline = [dict(row, id=f"{row['group_id']}-{row['language']}") for row in self.rows]
        candidate = [dict(row, correct=True) for row in baseline]
        result = paired_group_difference(baseline, candidate, samples=100)
        self.assertAlmostEqual(result["candidate_minus_baseline"], 1 / 3)
        self.assertEqual(result, paired_group_difference(baseline, candidate, samples=100))
        with self.assertRaisesRegex(ValueError, "identical"):
            paired_group_difference(baseline[:-1], candidate, samples=100)


if __name__ == "__main__":
    unittest.main()
