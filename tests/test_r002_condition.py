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


if __name__ == "__main__":
    unittest.main()
