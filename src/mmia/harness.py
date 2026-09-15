"""A bounded, offline, single-example greedy Core evaluation pilot."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import re
import resource
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


LANGUAGES = ("en", "ja", "zh")
DOMAINS = ("math", "physics", "coding", "logic")
SUFFIX = {
    "en": "Reply with only the integer answer. Do not explain.",
    "ja": "答えの整数だけを出力してください。説明は不要です。",
    "zh": "只输出整数答案，不要解释。",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def generate(seed=20260911, groups_per_domain=10):
    """Template-based smoke problems, NOT a capability benchmark.

    Each semantic group has exactly three translations in a single split.
    Splits are shuffled per domain; no semantic group is duplicated.
    """
    if groups_per_domain < 10:
        raise ValueError("Use at least 10 groups per domain")
    rng = random.Random(seed)
    rows = []
    for domain in DOMAINS:
        groups = []
        seen = set()
        while len(groups) < groups_per_domain:
            a, b, c = (rng.randint(2, 30) for _ in range(3))
            params = [a, b, c]
            if domain == "math":
                answer = (a + b) * c
                prompts = [f"Calculate ({a} + {b}) * {c}.",
                           f"({a} + {b}) × {c} を計算してください。",
                           f"计算 ({a} + {b}) × {c}。"]
            elif domain == "physics":
                params = [a, b]
                answer = a * b
                prompts = [f"A mass of {a} kg accelerates at {b} m/s^2. Using F=ma, find the net force in N.",
                           f"質量{a} kgの物体の加速度は{b} m/s²です。F=maを用いて合力をN単位で求めてください。",
                           f"物体质量为{a} kg，加速度为{b} m/s²。用F=ma求合力，单位为N。"]
            elif domain == "coding":
                answer = b + c
                code = f"values = [{a}, {b}, {c}]\nprint(sum(values[1:]))"
                prompts = [f"What integer does this Python code print?\n{code}",
                           f"次のPythonコードが出力する整数は何ですか？\n{code}",
                           f"以下Python代码输出哪个整数？\n{code}"]
            else:
                reverse = rng.choice([False, True])
                names = [f"K{a}", f"K{b}", f"K{c}"]
                if len(set(names)) < 3:
                    continue
                x, y, z = names
                left, right = (z, x) if reverse else (x, z)
                params = [a, b, c, reverse]
                answer = int(not reverse)
                prompts = [f"In a strict total order, {x} > {y} and {y} > {z}. Is {left} > {right}? Reply 1 for true, 0 for false.",
                           f"厳密な全順序で{x} > {y}、{y} > {z}です。{left} > {right}は真ですか？真なら1、偽なら0。",
                           f"在严格全序中，{x} > {y}且{y} > {z}。{left} > {right}是否为真？真输出1，假输出0。"]
            key = digest([domain, params])
            if key in seen:
                continue
            seen.add(key)
            groups.append((key, prompts, answer, params))
        rng.shuffle(groups)
        for index, (key, prompts, answer, params) in enumerate(groups):
            split = "train" if index < int(groups_per_domain * .6) else (
                "validation" if index < int(groups_per_domain * .8) else "test")
            for lang, prompt in zip(LANGUAGES, prompts):
                rows.append({"id": f"{key[:16]}-{lang}", "group_id": key,
                             "domain": domain, "language": lang, "split": split,
                             "prompt": prompt + "\n" + SUFFIX[lang],
                             "answer": str(answer), "parameters": params,
                             "world_seed": seed, "generator_version": 1})
    validate_rows(rows)
    return rows


def validate_rows(rows):
    ids, groups = set(), defaultdict(list)
    for row in rows:
        if row["id"] in ids:
            raise ValueError("Duplicate example id")
        ids.add(row["id"])
        groups[row["group_id"]].append(row)
    if not groups:
        raise ValueError("Empty dataset")
    for group in groups.values():
        if len(group) != 3 or {r["language"] for r in group} != set(LANGUAGES):
            raise ValueError("Every group must contain three translations")
        if len({r["split"] for r in group}) != 1:
            raise ValueError("Semantic group leaks across splits")
        if len({r["answer"] for r in group}) != 1:
            raise ValueError("Translations disagree on target")


def score(text, target, status="ok"):
    """Strict integer-only answer contract; never extract a convenient number."""
    normalized = text.strip()
    valid = re.fullmatch(r"[+-]?[0-9]+", normalized) is not None
    return {"format_valid": valid,
            "correct": status == "ok" and valid and int(normalized) == int(target)}


def percentile(values, q):
    if not values:
        return None
    values = sorted(values)
    p = (len(values) - 1) * q
    low, high = math.floor(p), math.ceil(p)
    return values[low] + (values[high] - values[low]) * (p - low)


def summarize(records):
    metrics = {}
    slices = {"all": records}
    for field in ("language", "domain", "difficulty"):
        for value in sorted({r[field] for r in records if field in r}):
            slices[f"{field}/{value}"] = [r for r in records if r[field] == value]
    for name, group in slices.items():
        # Error/timeout outcomes remain in quality denominator; successful timing
        # excludes those censored outcomes and reports their count explicitly.
        timings = [r["completion_seconds"] for r in group if r["status"] == "ok"]
        ttft = [r["ttft_seconds"] for r in group if r.get("ttft_seconds") is not None]
        metrics[name] = {"count": len(group),
                         "correct": sum(r["correct"] for r in group),
                         "accuracy": sum(r["correct"] for r in group) / len(group) if group else None,
                         "non_ok": sum(r["status"] != "ok" for r in group),
                         "format_invalid": sum(not r["format_valid"] for r in group),
                         "successful_latency_count": len(timings),
                         "completion_p50_seconds": percentile(timings, .5),
                         "completion_p95_seconds": percentile(timings, .95),
                         "ttft_p50_seconds": percentile(ttft, .5)}
    return metrics


class Core:
    def __init__(self, config):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.device = config["device"]
        torch.set_num_threads(config["cpu_threads"])
        torch.manual_seed(config["seed"])
        torch.use_deterministic_algorithms(True)
        if self.device == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("MPS unavailable; choose CPU explicitly")
        self.tokenizer = AutoTokenizer.from_pretrained(config["model_path"], local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            config["model_path"], local_files_only=True, dtype=torch.float32,
            attn_implementation="eager")
        if config.get("adapter_path"):
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(
                self.model, config["adapter_path"], local_files_only=True)
        self.model = self.model.to(self.device).eval()
        eos = self.model.generation_config.eos_token_id
        self.eos = set(eos if isinstance(eos, list) else [eos])

    def sync(self):
        if self.device == "mps":
            self.torch.mps.synchronize()

    def predict(self, prompt, max_tokens, timeout_seconds):
        # No targets, split labels, or latent semantic parameters enter this API.
        t = self.torch
        self.sync()
        start = time.perf_counter()
        inputs = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=True,
            add_generation_prompt=True, return_tensors="pt").to(self.device)
        input_tokens = inputs.shape[1]
        mask = t.ones_like(inputs)
        past, output, first = None, [], None
        status = "truncated"
        with t.inference_mode():
            for _ in range(max_tokens):
                if time.perf_counter() - start > timeout_seconds:
                    status = "timeout"
                    break
                result = self.model(input_ids=inputs, attention_mask=mask,
                                    past_key_values=past, use_cache=True)
                next_id = result.logits[:, -1, :].argmax(dim=-1, keepdim=True)
                past = result.past_key_values
                output.append(next_id.item())
                self.sync()
                now = time.perf_counter()
                if first is None:
                    first = now - start
                if now - start > timeout_seconds:
                    status = "timeout"
                    break
                if output[-1] in self.eos:
                    status = "ok"
                    break
                inputs = next_id
                mask = t.cat([mask, t.ones_like(next_id)], dim=1)
        text = self.tokenizer.decode(output, skip_special_tokens=True)
        elapsed = time.perf_counter() - start
        return {"prediction": text, "token_ids": output, "status": status,
                "input_tokens": input_tokens,
                "output_tokens": len(output), "ttft_seconds": first,
                "completion_seconds": elapsed}


def run(config, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)  # Never overwrite a research run.
    manifest = {"status": "running", "registered_at": datetime.now(timezone.utc).isoformat(),
                "config": config, "platform": platform.platform(), "python": platform.python_version(),
                "energy_joules": None, "estimated_flops": None,
                "memory_method": "process lifetime ru_maxrss (not per-example GPU peak)",
                "latency_method": "tokenization through detokenization, synchronized; model load excluded",
                "timeout_method": "cooperative token-boundary deadline; cannot interrupt one forward"}
    write_json(output / "manifest.json", manifest)
    try:
        if config["max_new_tokens"] < 1 or config["timeout_seconds"] <= 0 or config["cpu_threads"] < 1:
            raise ValueError("Token, time, and thread limits must be positive")
        manifest["source_hashes"] = {str(p): file_hash(p) for p in sorted(Path("src/mmia").glob("*.py"))}
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        manifest["git_commit"] = git.stdout.strip() if git.returncode == 0 else None
        manifest["versions"] = {p: importlib.metadata.version(p) for p in ["torch", "transformers", "numpy", "huggingface-hub"]}
        if config.get("adapter_path"):
            manifest["versions"]["peft"] = importlib.metadata.version("peft")
        manifest["model_file_hashes"] = {p.name: file_hash(p) for p in sorted(Path(config["model_path"]).iterdir()) if p.is_file()}
        if config.get("adapter_path"):
            manifest["adapter_file_hashes"] = {
                p.name: file_hash(p) for p in sorted(Path(config["adapter_path"]).iterdir()) if p.is_file()}
        manifest["dataset_hash"] = file_hash(config["dataset"])
        rows = [json.loads(line) for line in Path(config["dataset"]).read_text().splitlines()]
        validate_rows(rows)
        domain_filter = config.get("domain_filter")
        if domain_filter is not None and domain_filter not in DOMAINS:
            raise ValueError(f"Unknown domain_filter: {domain_filter}")
        selected = [r for r in rows if r["split"] == config["split"]
                    and (domain_filter is None or r["domain"] == domain_filter)]
        if not selected:
            raise ValueError("No examples in selected split")
        random.Random(config["seed"]).shuffle(selected)
        write_json(output / "manifest.json", manifest)
        load_start = time.perf_counter()
        core = Core(config)
        manifest["model_load_seconds"] = time.perf_counter() - load_start
        manifest["parameters"] = sum(p.numel() for p in core.model.parameters())
        manifest["trainable_parameters"] = sum(p.numel() for p in core.model.parameters() if p.requires_grad)
        warmup = core.predict("Return only the integer 2.", config["max_new_tokens"], config["timeout_seconds"])
        write_json(output / "warmup.json", warmup)
        if warmup["status"] != "ok":
            raise RuntimeError("Warmup failed to finish")
        records = []
        with (output / "predictions.jsonl").open("x") as stream:
            for row in selected:
                try:
                    prediction = core.predict(row["prompt"], config["max_new_tokens"], config["timeout_seconds"])
                except Exception as error:
                    prediction = {"prediction": "", "status": "error", "error": repr(error),
                                  "ttft_seconds": None, "completion_seconds": None}
                record = {**row, **prediction, **score(prediction["prediction"], row["answer"], prediction["status"])}
                records.append(record)
                stream.write(canonical(record) + "\n")
                stream.flush()
                print(f'{len(records)}/{len(selected)} {row["domain"]}/{row["language"]} {record["status"]}', flush=True)
        write_json(output / "summary.json", summarize(records))
        manifest["status"] = "completed" if all(r["status"] != "error" for r in records) else "failed"
        manifest["example_count"] = len(records)
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
    sub = parser.add_subparsers(dest="command", required=True)
    data = sub.add_parser("generate")
    data.add_argument("--output", required=True)
    data.add_argument("--seed", type=int, default=20260911)
    data.add_argument("--groups", type=int, default=10)
    evaluate = sub.add_parser("run")
    evaluate.add_argument("--config", required=True)
    evaluate.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "generate":
        rows = generate(args.seed, args.groups)
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write("".join(canonical(r) + "\n" for r in rows))
        print(f"Generated {len(rows)} examples; sha256={file_hash(path)}")
    else:
        run(json.loads(Path(args.config).read_text()), args.output)


if __name__ == "__main__":
    main()
