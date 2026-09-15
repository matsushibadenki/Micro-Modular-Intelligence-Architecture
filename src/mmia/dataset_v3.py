"""Generate and audit the multilingual MMIA compositional pilot-v3."""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .dataset_v2 import DIFFICULTIES, SPLITS
from .harness import LANGUAGES, SUFFIX, canonical, digest, file_hash, validate_rows


COMPOSITIONS = ("math_to_physics", "code_to_math", "logic_to_math", "code_to_physics")


def _prompts(en, ja, zh):
    return [en + "\n" + SUFFIX["en"], ja + "\n" + SUFFIX["ja"],
            zh + "\n" + SUFFIX["zh"]]


def compute(row):
    """Recompute intermediate and final targets without reading stored targets."""
    p, family = row["parameters"], row["task_family"]
    if family == "acceleration_sum_then_force":
        intermediate, answer = p["a"] + p["b"], p["mass"] * (p["a"] + p["b"])
    elif family == "acceleration_product_sum_then_force":
        intermediate = (p["a"] + p["b"]) * p["scale"]
        answer = p["mass"] * intermediate
    elif family == "acceleration_two_products_then_force":
        intermediate = p["a"] * p["b"] + p["c"] * p["d"]
        answer = p["mass"] * intermediate
    elif family == "code_sum_then_product":
        intermediate, answer = p["a"] + p["b"], (p["a"] + p["b"]) * p["factor"]
    elif family == "code_weighted_then_offset":
        intermediate = p["a"] + 2 * p["b"] + 3 * p["c"]
        answer = intermediate - p["offset"]
    elif family == "code_even_sum_then_scale":
        intermediate = sum(x for x in p["values"] if x % 2 == 0)
        answer = intermediate * p["factor"]
    elif family.startswith("logic_"):
        intermediate = p["truth"]
        answer = p["a"] + p["b"] if intermediate else p["a"] - p["b"]
    elif family == "code_acceleration_then_force":
        intermediate, answer = p["a"] + p["b"], p["mass"] * (p["a"] + p["b"])
    elif family == "code_weighted_acceleration_then_force":
        intermediate = p["a"] + 2 * p["b"]
        answer = p["mass"] * intermediate
    elif family == "code_filtered_acceleration_then_work":
        intermediate = sum(x for x in p["values"] if x > p["threshold"])
        answer = p["mass"] * intermediate * p["distance"]
    else:
        raise ValueError(f"Unknown task family: {family}")
    return [str(intermediate)], str(answer)


def _logic_facts(rng, difficulty, truth):
    names = [f"R{x}" for x in rng.sample(range(1000, 9999), 5)]
    hops = {"easy": 1, "medium": 2, "hard": 4}[difficulty]
    chain = names[:hops + 1]
    facts = "; ".join(f"{chain[i]} > {chain[i + 1]}" for i in range(hops))
    query = f"{chain[0]} > {chain[-1]}" if truth else f"{chain[-1]} > {chain[0]}"
    return facts, query


def _problem(composition, split, difficulty, index, rng):
    a, b, c, d, e = (rng.randint(2, 15) for _ in range(5))
    template_id = f"v3-{composition}-{split}-{difficulty}"
    style = {"train": ("First solve both stages.", "2段階を順に解いてください。", "请依次完成两个阶段。"),
             "validation": ("Combine the two required operations.", "必要な2つの処理を組み合わせてください。", "请组合所需的两个操作。"),
             "test": ("Determine the final result after the intermediate step.", "中間段階を経た最終結果を求めてください。", "求经过中间步骤后的最终结果。")} [split]
    if composition == "math_to_physics":
        skills = ["math", "physics"]
        if difficulty == "easy":
            family = "acceleration_sum_then_force"
            p = {"a": a, "b": b, "mass": c}
            body = (f"Add acceleration components {a} and {b} m/s^2, then use the result in F=ma for mass {c} kg.",
                    f"加速度成分{a}と{b} m/s²を足し、その結果を質量{c} kgのF=maに使ってください。",
                    f"先将加速度分量{a}与{b} m/s²相加，再将结果用于质量{c} kg的F=ma。")
        elif difficulty == "medium":
            family = "acceleration_product_sum_then_force"
            p = {"a": a, "b": b, "scale": c, "mass": d}
            body = (f"Compute acceleration ({a}+{b})*{c} m/s^2, then use it in F=ma for mass {d} kg.",
                    f"加速度({a}+{b})×{c} m/s²を計算し、それを質量{d} kgのF=maに使ってください。",
                    f"计算加速度({a}+{b})×{c} m/s²，再用于质量{d} kg的F=ma。")
        else:
            family = "acceleration_two_products_then_force"
            p = {"a": a, "b": b, "c": c, "d": d, "mass": e}
            body = (f"Compute acceleration {a}*{b}+{c}*{d} m/s^2, then use it in F=ma for mass {e} kg.",
                    f"加速度{a}×{b}+{c}×{d} m/s²を計算し、それを質量{e} kgのF=maに使ってください。",
                    f"计算加速度{a}×{b}+{c}×{d} m/s²，再用于质量{e} kg的F=ma。")
    elif composition == "code_to_math":
        skills = ["coding", "math"]
        if difficulty == "easy":
            family, p = "code_sum_then_product", {"a": a, "b": b, "factor": c}
            code, operation = f"print(sum([{a}, {b}]))", (f"multiply the printed value by {c}", f"出力値を{c}倍", f"将输出值乘以{c}")
        elif difficulty == "medium":
            family, p = "code_weighted_then_offset", {"a": a, "b": b, "c": c, "offset": d}
            code = f"v=[{a},{b},{c}]\nprint(sum((i+1)*x for i,x in enumerate(v)))"
            operation = (f"subtract {d} from the printed value", f"出力値から{d}を引く", f"从输出值中减去{d}")
        else:
            family, p = "code_even_sum_then_scale", {"values": [a, b, c, d], "factor": e}
            code = f"v=[{a},{b},{c},{d}]\nprint(sum(x for x in v if x%2==0))"
            operation = (f"multiply the printed value by {e}", f"出力値を{e}倍", f"将输出值乘以{e}")
        body = (f"Trace this Python code, then {operation[0]}:\n{code}",
                f"次のPythonコードを追跡し、{operation[1]}してください。\n{code}",
                f"跟踪以下Python代码，然后{operation[2]}：\n{code}")
    elif composition == "logic_to_math":
        skills = ["logic", "math"]
        truth = index % 2 == 0
        facts, query = _logic_facts(rng, difficulty, truth)
        family = f"logic_{difficulty}_then_branch"
        p = {"truth": int(truth), "a": a, "b": b, "facts": facts, "query": query}
        body = (f"In a strict total order, {facts}. If {query} follows, compute {a}+{b}; otherwise compute {a}-{b}.",
                f"厳密な全順序で{facts}です。{query}が導けるなら{a}+{b}、そうでなければ{a}-{b}を計算してください。",
                f"在严格全序中，{facts}。若能推出{query}，计算{a}+{b}；否则计算{a}-{b}。")
    else:
        skills = ["coding", "physics"]
        if difficulty == "easy":
            family, p = "code_acceleration_then_force", {"a": a, "b": b, "mass": c}
            code = f"a=sum([{a},{b}])\nprint(a)"
        elif difficulty == "medium":
            family, p = "code_weighted_acceleration_then_force", {"a": a, "b": b, "mass": c}
            code = f"v=[{a},{b}]\na=sum((i+1)*x for i,x in enumerate(v))\nprint(a)"
        else:
            threshold = min(a, b, c) - 1
            family = "code_filtered_acceleration_then_work"
            p = {"values": [a, b, c], "threshold": threshold, "mass": d, "distance": e}
            code = f"v=[{a},{b},{c}]\na=sum(x for x in v if x>{threshold})\nprint(a)"
        tail = (f"Treat the printed value as acceleration in m/s^2 for a {p['mass']} kg object"
                + (f" moving {p['distance']} m; compute W=mad." if difficulty == "hard" else "; compute F=ma."),
                f"出力値を{p['mass']} kgの物体の加速度m/s²として"
                + (f"、距離{p['distance']} mのW=madを求めてください。" if difficulty == "hard" else "、F=maを求めてください。"),
                f"将输出值作为{p['mass']} kg物体的加速度m/s²，"
                + (f"移动{p['distance']} m并计算W=mad。" if difficulty == "hard" else "计算F=ma。"))
        body = (f"Trace the code. {tail[0]}\n{code}", f"コードを追跡してください。{tail[1]}\n{code}",
                f"跟踪代码。{tail[2]}\n{code}")
    prompts = _prompts(*(style[i] + " " + body[i] for i in range(3)))
    row = {"parameters": p, "task_family": family}
    intermediate, answer = compute(row)
    return prompts, intermediate, answer, p, family, template_id, skills


def generate_v3(seed=20260915, groups_per_cell=12):
    if groups_per_cell < 2 or groups_per_cell % 2:
        raise ValueError("groups_per_cell must be an even integer >= 2")
    rng, rows = random.Random(seed), []
    for composition in COMPOSITIONS:
        for split in SPLITS:
            for difficulty in DIFFICULTIES:
                seen = set()
                for index in range(groups_per_cell):
                    for _ in range(100):
                        prompts, intermediate, answer, params, family, template, skills = _problem(
                            composition, split, difficulty, index, rng)
                        key = digest([3, composition, split, difficulty, family, params])
                        if key not in seen:
                            seen.add(key)
                            break
                    else:
                        raise RuntimeError("Could not generate a unique problem")
                    for language, prompt in zip(LANGUAGES, prompts):
                        rows.append({"id": f"v3-{key[:16]}-{language}", "group_id": key,
                                     "domain": composition, "composition": skills,
                                     "language": language, "split": split,
                                     "difficulty": difficulty, "task_family": family,
                                     "template_id": template, "prompt": prompt,
                                     "intermediate_answers": intermediate, "answer": answer,
                                     "parameters": params, "world_seed": seed,
                                     "generator_version": 3})
    validate_rows(rows)
    audit_v3(rows, groups_per_cell)
    return rows


def audit_v3(rows, expected_groups_per_cell=None):
    validate_rows(rows)
    groups = {}
    for row in rows:
        if row.get("generator_version") != 3:
            raise ValueError("pilot-v3 requires generator_version=3")
        intermediate, answer = compute(row)
        if row["intermediate_answers"] != intermediate or row["answer"] != answer:
            raise ValueError(f"Incorrect target or intermediate for {row['id']}")
        if len(row["composition"]) != 2 or row["composition"][0] == row["composition"][1]:
            raise ValueError("Every problem must compose two distinct skills")
        groups.setdefault(row["group_id"], row)
    cells = Counter((r["domain"], r["split"], r["difficulty"]) for r in groups.values())
    expected_cells = len(COMPOSITIONS) * len(SPLITS) * len(DIFFICULTIES)
    counts = set(cells.values())
    if len(cells) != expected_cells or len(counts) != 1:
        raise ValueError("Missing or unbalanced composition/split/difficulty cells")
    if expected_groups_per_cell is not None and counts != {expected_groups_per_cell}:
        raise ValueError("Unexpected groups per cell")
    templates = defaultdict(set)
    for row in groups.values():
        templates[row["template_id"]].add(row["split"])
    if any(len(splits) != 1 for splits in templates.values()):
        raise ValueError("Template id leaks across splits")
    logic = Counter((r["split"], r["difficulty"], str(r["parameters"]["truth"]))
                    for r in groups.values() if r["domain"] == "logic_to_math")
    for split in SPLITS:
        for difficulty in DIFFICULTIES:
            if logic[(split, difficulty, "0")] != logic[(split, difficulty, "1")]:
                raise ValueError("Logic branch labels are not balanced")
    return {"rows": len(rows), "semantic_groups": len(groups),
            "groups_per_cell": next(iter(counts)),
            "cell_counts": {"/".join(k): v for k, v in sorted(cells.items())},
            "logic_branch_counts": {"/".join(k): v for k, v in sorted(logic.items())},
            "compositions": list(COMPOSITIONS), "languages": list(LANGUAGES),
            "template_count": len(templates), "template_split_disjoint": True,
            "targets_and_intermediates_recomputed": True, "dataset_sha256": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit-output", required=True)
    parser.add_argument("--seed", type=int, default=20260915)
    parser.add_argument("--groups-per-cell", type=int, default=12)
    args = parser.parse_args()
    rows = generate_v3(args.seed, args.groups_per_cell)
    output, audit_output = Path(args.output), Path(args.audit_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write("".join(canonical(row) + "\n" for row in rows))
    report = audit_v3(rows, args.groups_per_cell)
    report["dataset_sha256"] = file_hash(output)
    with audit_output.open("x") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(canonical(report))


if __name__ == "__main__":
    main()
