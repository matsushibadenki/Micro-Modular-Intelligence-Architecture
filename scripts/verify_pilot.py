"""Read-only run comparison plus independent Transformers.generate check."""

import json
from pathlib import Path

from mmia.harness import Core, file_hash, write_json


def main():
    root = Path("results/MMIA-R001")
    def read(name):
        return {r["id"]: r for r in map(json.loads, (root / name / "predictions.jsonl").read_text().splitlines())}
    first, second = read("run-02"), read("run-03")
    identical = first.keys() == second.keys() and all(
        all(first[key][field] == second[key][field] for field in ("token_ids", "correct", "status"))
        for key in first)
    config = json.loads(Path("configs/pilot-core.json").read_text())
    core = Core(config)
    from transformers import GenerationConfig
    generation = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=config["max_new_tokens"],
                                  eos_token_id=list(core.eos), pad_token_id=core.tokenizer.pad_token_id,
                                  use_cache=True, repetition_penalty=1.0)
    mismatches = []
    for row in first.values():
        inputs = core.tokenizer.apply_chat_template(
            [{"role": "user", "content": row["prompt"]}], tokenize=True,
            add_generation_prompt=True, return_tensors="pt").to(core.device)
        with core.torch.inference_mode():
            result = core.model.generate(input_ids=inputs, attention_mask=core.torch.ones_like(inputs),
                                         generation_config=generation)
        tokens = result[0, inputs.shape[1]:].tolist()
        if tokens != row["token_ids"]:
            mismatches.append({"id": row["id"], "manual": row["token_ids"], "generate": tokens})
    report = {"repeated_run_token_and_grade_identity": identical,
              "compared_examples": len(first), "generate_mismatches": mismatches,
              "scope": "Standard generate with identical greedy settings; no prompt/target changes",
              "verification_script_sha256": file_hash(__file__),
              "harness_sha256": file_hash("src/mmia/harness.py")}
    path = root / "verification.json"
    if path.exists():
        raise FileExistsError(path)
    write_json(path, report)
    print(json.dumps(report, indent=2))
    if not identical or mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
