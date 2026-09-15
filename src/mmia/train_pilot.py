"""Bounded LoRA training smoke test with target-only causal loss."""

import argparse
import importlib.metadata
import json
import math
import platform
import random
import resource
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .harness import file_hash, write_json


def choose_rows(rows, seed, limit, domain=None):
    candidates = [row for row in rows if row["split"] == "train"
                  and (domain is None or row["domain"] == domain)]
    random.Random(seed).shuffle(candidates)
    if limit < 1 or limit > len(candidates):
        raise ValueError("sample_limit must be between 1 and the train row count")
    return candidates[:limit]


def choose_stratified_rows(rows, seed, samples_per_cell):
    """Balance domain/language/difficulty while avoiding translated group reuse."""
    if samples_per_cell < 1:
        raise ValueError("samples_per_cell must be positive")
    rng = random.Random(seed)
    by_group = defaultdict(dict)
    metadata = {}
    for row in rows:
        if row["split"] == "train":
            by_group[row["group_id"]][row["language"]] = row
            metadata[row["group_id"]] = (row["domain"], row["difficulty"])
    cells = defaultdict(list)
    for group_id, cell in metadata.items():
        cells[cell].append(group_id)
    selected = []
    languages = ("en", "ja", "zh")
    for cell in sorted(cells):
        group_ids = sorted(cells[cell])
        rng.shuffle(group_ids)
        needed = samples_per_cell * len(languages)
        if len(group_ids) < needed:
            raise ValueError(f"Not enough distinct semantic groups in cell {cell}")
        for offset, language in enumerate(languages):
            chosen = group_ids[offset * samples_per_cell:(offset + 1) * samples_per_cell]
            selected.extend(by_group[group_id][language] for group_id in chosen)
    rng.shuffle(selected)
    return selected


def encode_target_only(tokenizer, prompt, answer):
    prompt_ids = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=True,
        add_generation_prompt=True, return_tensors="pt")[0]
    full_ids = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}],
        tokenize=True, add_generation_prompt=False, return_tensors="pt")[0]
    if len(full_ids) <= len(prompt_ids) or not full_ids[:len(prompt_ids)].equal(prompt_ids):
        raise ValueError("Chat template prompt is not a prefix of supervised sequence")
    labels = full_ids.clone()
    labels[:len(prompt_ids)] = -100
    return full_ids, labels, len(prompt_ids), int((labels != -100).sum())


def run(config, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "running", "registered_at": datetime.now(timezone.utc).isoformat(),
                "config": config, "python_executable": sys.executable,
                "python": platform.python_version(), "platform": platform.platform(),
                "energy_joules": None, "estimated_flops": None,
                "memory_method": "process lifetime ru_maxrss; model load and training included"}
    write_json(output / "manifest.json", manifest)
    losses = []
    try:
        import torch
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if config["device"] != "cpu":
            raise ValueError("This bounded pilot has only validated CPU")
        torch.set_num_threads(config["cpu_threads"])
        torch.manual_seed(config["seed"])
        torch.use_deterministic_algorithms(True)
        versions = ["torch", "transformers", "numpy", "peft", "accelerate"]
        manifest["versions"] = {name: importlib.metadata.version(name) for name in versions}
        manifest["source_sha256"] = file_hash(__file__)
        manifest["dataset_sha256"] = file_hash(config["dataset"])
        rows = [json.loads(line) for line in Path(config["dataset"]).read_text().splitlines()]
        if config.get("sampling") == "stratified":
            selected = choose_stratified_rows(rows, config["seed"], config["samples_per_cell"])
        else:
            selected = choose_rows(rows, config["seed"], config["sample_limit"],
                                   config.get("domain_filter"))
        manifest["selected_ids"] = [row["id"] for row in selected]
        manifest["selected_semantic_groups"] = len({row["group_id"] for row in selected})
        tokenizer = AutoTokenizer.from_pretrained(config["model_path"], local_files_only=True)
        base = AutoModelForCausalLM.from_pretrained(
            config["model_path"], local_files_only=True, dtype=torch.float32,
            attn_implementation="eager")
        lora = LoraConfig(r=config["lora_rank"], lora_alpha=config["lora_alpha"],
                          lora_dropout=0.0, bias="none", task_type=TaskType.CAUSAL_LM,
                          target_modules=config["target_modules"])
        model = get_peft_model(base, lora).train()
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        manifest["trainable_parameters"] = trainable
        manifest["total_parameters_with_adapter"] = total
        optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),
                                      lr=config["learning_rate"], weight_decay=0.0)
        processed_input_tokens = processed_target_tokens = 0
        started = time.perf_counter()
        for step, row in enumerate(selected, 1):
            input_ids, labels, prompt_tokens, target_tokens = encode_target_only(
                tokenizer, row["prompt"], row["answer"])
            if len(input_ids) > config["max_sequence_tokens"]:
                raise ValueError(f"Sequence exceeds fixed maximum: {row['id']}")
            input_ids, labels = input_ids.unsqueeze(0), labels.unsqueeze(0)
            optimizer.zero_grad(set_to_none=True)
            result = model(input_ids=input_ids, attention_mask=torch.ones_like(input_ids), labels=labels)
            if not torch.isfinite(result.loss):
                raise RuntimeError("Non-finite training loss")
            result.loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config["max_grad_norm"])
            optimizer.step()
            loss = float(result.loss.detach())
            losses.append({"step": step, "id": row["id"], "domain": row["domain"],
                           "language": row["language"], "difficulty": row["difficulty"],
                           "input_tokens": len(input_ids[0]), "prompt_tokens": prompt_tokens,
                           "target_tokens": target_tokens, "loss": loss,
                           "grad_norm": float(grad_norm)})
            processed_input_tokens += len(input_ids[0])
            processed_target_tokens += target_tokens
            print(f"{step}/{len(selected)} loss={loss:.6f} {row['domain']}/{row['language']}", flush=True)
        manifest["training_seconds"] = time.perf_counter() - started
        manifest["optimizer_steps"] = len(selected)
        manifest["processed_input_tokens"] = processed_input_tokens
        manifest["processed_target_tokens"] = processed_target_tokens
        manifest["first_loss"] = losses[0]["loss"]
        manifest["last_loss"] = losses[-1]["loss"]
        manifest["all_losses_finite"] = all(math.isfinite(row["loss"]) for row in losses)
        with (output / "steps.jsonl").open("x") as stream:
            stream.write("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in losses))
        adapter = output / "adapter"
        model.save_pretrained(adapter, safe_serialization=True)
        tokenizer.save_pretrained(adapter)
        manifest["adapter_files"] = {p.name: file_hash(p) for p in sorted(adapter.iterdir()) if p.is_file()}
        manifest["status"] = "completed"
    except BaseException as error:
        manifest["status"] = "failed"
        manifest["error"] = repr(error)
        raise
    finally:
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        manifest["process_peak_rss_bytes"] = rss if platform.system() == "Darwin" else rss * 1024
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        write_json(output / "manifest.json", manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(json.loads(Path(args.config).read_text()), args.output)


if __name__ == "__main__":
    main()
