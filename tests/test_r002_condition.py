import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_r002_condition import effective_config


class R002ConditionTests(unittest.TestCase):
    def test_only_registered_runtime_fields_are_overridden(self):
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "template.json"
            template.write_text(json.dumps({
                "seed": 1, "experiment_id": "old", "lora_rank": 8,
                "adapter_path": "old-adapter"}))
            config = effective_config(template, 2, "new", "new-adapter")
            self.assertEqual(config["seed"], 2)
            self.assertEqual(config["experiment_id"], "new")
            self.assertEqual(config["adapter_path"], "new-adapter")
            self.assertEqual(config["lora_rank"], 8)

    def test_path_specialist_overrides_are_explicit(self):
        root = Path(__file__).parents[1]
        config = effective_config(
            root / "configs/r007-seed-20260915-mixed.json", 20260915,
            "MMIA-R007-S1-C2-CODE-MATH", domain_filter="code_to_math",
            sample_limit=108)
        self.assertEqual(config["domain_filter"], "code_to_math")
        self.assertEqual(config["sample_limit"], 108)
        self.assertEqual(config["lora_rank"], 8)

    def test_rank32_template_keeps_registered_capacity(self):
        root = Path(__file__).parents[1]
        config = effective_config(
            root / "configs/r002-seed-20260915-mixed-rank32.json",
            20260917, "MMIA-R002-S3-C3")
        self.assertEqual(config["lora_rank"], 32)
        self.assertEqual(config["lora_alpha"], 64)
        self.assertEqual(config["sample_limit"], 432)


if __name__ == "__main__":
    unittest.main()
