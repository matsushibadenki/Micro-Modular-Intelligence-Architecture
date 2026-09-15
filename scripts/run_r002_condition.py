"""Run one registered R002 condition from an immutable seed-1 template."""

import argparse
import json
from pathlib import Path


def effective_config(template, seed, experiment_id, adapter_path=None,
                     domain_filter=None, sample_limit=None):
    config = json.loads(Path(template).read_text())
    config["seed"] = seed
    config["experiment_id"] = experiment_id
    if adapter_path is not None:
        config["adapter_path"] = adapter_path
    if domain_filter is not None:
        config["domain_filter"] = domain_filter
    if sample_limit is not None:
        config["sample_limit"] = sample_limit
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("train", "eval"))
    parser.add_argument("--template", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--adapter-path")
    parser.add_argument("--domain-filter")
    parser.add_argument("--sample-limit", type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = effective_config(
        args.template, args.seed, args.experiment_id, args.adapter_path,
        args.domain_filter, args.sample_limit)
    if args.mode == "train":
        if args.adapter_path is not None:
            raise ValueError("Training does not accept --adapter-path")
        from mmia.train_pilot import run
    else:
        if args.adapter_path is None:
            raise ValueError("Evaluation requires --adapter-path")
        from mmia.harness import run
    run(config, args.output)


if __name__ == "__main__":
    main()
