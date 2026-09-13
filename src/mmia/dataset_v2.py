"""Generate and audit MMIA pilot-v2 without model or third-party dependencies."""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .harness import DOMAINS, LANGUAGES, SUFFIX, canonical, digest, file_hash, validate_rows


SPLITS = ("train", "validation", "test")
DIFFICULTIES = ("easy", "medium", "hard")


def _three(en, ja, zh):
    return [en + "\n" + SUFFIX["en"], ja + "\n" + SUFFIX["ja"], zh + "\n" + SUFFIX["zh"]]


def expected_answer(row):
    """Recompute the target from structured fields, without reading row['answer']."""
    family = row["task_family"]
    if family in {"direct_order", "two_hop_order", "four_hop_order"}:
        return str(row["parameters"][-1])
    a, b, c, d = row["parameters"]
    formulas = {
        "addition": lambda: a + b,
        "parenthesized_arithmetic": lambda: (a + b) * c,
        "two_product_difference": lambda: a * b - c * d,
        "force": lambda: a * b,
        "force_from_velocity_change": lambda: a * (b + c),
        "work": lambda: a * b * c,
        "list_sum": lambda: a + b,
        "weighted_loop": lambda: a + 2 * b + 3 * c,
        "filtered_comprehension": lambda: sum(x for x in (a, b, c, d) if x % 2 == 0),
    }
    if family not in formulas:
        raise ValueError(f"Unknown task family: {family}")
    return str(formulas[family]())


def _problem(domain, split, difficulty, index, rng):
    """Return split-specific prompts, integer target, parameters, and task family."""
    a, b, c, d = (rng.randint(2, 19) for _ in range(4))
    template_id = f"{domain}-{split}-{difficulty}-v1"
    if domain == "math":
        if difficulty == "easy":
            answer, family = a + b, "addition"
            forms = {
                "train": (f"Add {a} and {b}.", f"{a}と{b}を足してください。", f"计算{a}加{b}。"),
                "validation": (f"What is the sum of {a} and {b}?", f"{a}と{b}の合計は何ですか？", f"{a}与{b}的和是多少？"),
                "test": (f"Evaluate {a} + {b}.", f"{a} + {b} を計算してください。", f"求{a} + {b}的值。")}
        elif difficulty == "medium":
            answer, family = (a + b) * c, "parenthesized_arithmetic"
            forms = {
                "train": (f"Calculate ({a} + {b}) * {c}.", f"({a} + {b}) × {c}を計算してください。", f"计算({a} + {b}) × {c}。"),
                "validation": (f"Multiply the sum of {a} and {b} by {c}.", f"{a}と{b}の和を{c}倍してください。", f"把{a}与{b}的和乘以{c}。"),
                "test": (f"Evaluate {c}({a} + {b}).", f"{c} × ({a} + {b}) の値を求めてください。", f"求{c} × ({a} + {b})的值。")}
        else:
            answer, family = a * b - c * d, "two_product_difference"
            forms = {
                "train": (f"Calculate {a}*{b} - {c}*{d}.", f"{a}×{b}から{c}×{d}を引いてください。", f"计算{a}×{b}减去{c}×{d}。"),
                "validation": (f"Find the difference between the products {a} by {b} and {c} by {d}.", f"{a}と{b}の積と、{c}と{d}の積の差を求めてください。", f"求{a}与{b}之积减去{c}与{d}之积的结果。"),
                "test": (f"Evaluate ({a} × {b}) − ({c} × {d}).", f"({a} × {b}) − ({c} × {d}) を計算してください。", f"求({a} × {b}) − ({c} × {d})。")}
    elif domain == "physics":
        if difficulty == "easy":
            answer, family = a * b, "force"
            forms = {
                "train": (f"A {a} kg mass accelerates at {b} m/s^2. Use F=ma. Find force in N.", f"質量{a} kg、加速度{b} m/s²です。F=maで力をN単位で求めてください。", f"质量为{a} kg，加速度为{b} m/s²。用F=ma求力，单位N。"),
                "validation": (f"What net force gives a {a} kg object an acceleration of {b} m/s^2? Answer in N.", f"{a} kgの物体を{b} m/s²で加速させる合力は何Nですか？", f"使{a} kg物体产生{b} m/s²加速度的合力是多少N？"),
                "test": (f"Compute ma in newtons when m={a} kg and a={b} m/s^2.", f"m={a} kg、a={b} m/s²のときmaをNで計算してください。", f"当m={a} kg、a={b} m/s²时，以N计算ma。")}
        elif difficulty == "medium":
            answer, family = a * (b + c), "force_from_velocity_change"
            forms = {
                "train": (f"A {a} kg body changes velocity by {b + c} m/s in 1 s. Find average force in N.", f"{a} kgの物体の速度が1秒で{b + c} m/s変化します。平均力をNで求めてください。", f"{a} kg物体在1秒内速度变化{b + c} m/s。求平均力，单位N。"),
                "validation": (f"Over one second, a {a} kg object gains {b} m/s then {c} m/s in the same direction. Find average force in N.", f"{a} kgの物体が1秒間に同じ向きへ{b} m/s、さらに{c} m/s加速します。平均力は何Nですか？", f"{a} kg物体在1秒内同向增加{b} m/s后又增加{c} m/s。平均力是多少N？"),
                "test": (f"For mass {a} kg and one-second velocity change ({b}+{c}) m/s, compute F=mΔv/Δt in N.", f"質量{a} kg、1秒間の速度変化({b}+{c}) m/sについて、F=mΔv/ΔtをNで求めてください。", f"质量{a} kg、1秒速度变化({b}+{c}) m/s，按F=mΔv/Δt求力，单位N。")}
        else:
            answer, family = a * b * c, "work"
            forms = {
                "train": (f"A {a} kg object accelerates at {b} m/s^2 through {c} m. Force is parallel. Find work in J.", f"{a} kgの物体が{b} m/s²で{c} m進み、力は移動方向と平行です。仕事をJで求めてください。", f"{a} kg物体以{b} m/s²加速并移动{c} m，力与位移同向。求功，单位J。"),
                "validation": (f"Using F=ma and W=Fd, find work when m={a} kg, acceleration={b} m/s^2, distance={c} m.", f"F=maとW=Fdを使い、m={a} kg、加速度={b} m/s²、距離={c} mの仕事を求めてください。", f"用F=ma和W=Fd，求m={a} kg、加速度={b} m/s²、距离={c} m时的功。"),
                "test": (f"A constant parallel force accelerates {a} kg at {b} m/s^2 over {c} m. How many joules are transferred?", f"一定の平行な力が{a} kgを{b} m/s²で加速しながら{c} m動かします。移されたエネルギーは何Jですか？", f"恒定同向力使{a} kg物体以{b} m/s²加速并移动{c} m。传递能量是多少J？")}
    elif domain == "coding":
        if difficulty == "easy":
            answer, family = a + b, "list_sum"
            code = f"values = [{a}, {b}]\nprint(sum(values))"
        elif difficulty == "medium":
            answer, family = a + 2 * b + 3 * c, "weighted_loop"
            code = f"values = [{a}, {b}, {c}]\ntotal = 0\nfor i, x in enumerate(values, 1):\n    total += i * x\nprint(total)"
        else:
            answer, family = sum(x for x in (a, b, c, d) if x % 2 == 0), "filtered_comprehension"
            code = f"values = [{a}, {b}, {c}, {d}]\nprint(sum(x for x in values if x % 2 == 0))"
        leads = {
            "train": ("What integer does this Python code print?", "次のPythonコードが出力する整数は何ですか？", "以下Python代码输出哪个整数？"),
            "validation": ("Trace the Python program and give its printed integer.", "このPythonプログラムを追跡し、出力される整数を答えてください。", "请跟踪这个Python程序并给出其输出的整数。"),
            "test": ("Determine the exact integer sent to standard output by this Python snippet.", "このPythonコードが標準出力へ送る整数を特定してください。", "确定这段Python代码输出到标准输出的整数。")}
        forms = {split: tuple(f"{lead}\n{code}" for lead in leads[split])}
    else:
        # Alternating indices guarantee six true and six false cases per
        # split/difficulty, independent of the RNG sequence.
        truth = index % 2 == 0
        opaque_ids = rng.sample(range(1000, 9999), 5)
        names = [f"Q{value}" for value in opaque_ids]
        if difficulty == "easy":
            x, y = names[:2]
            facts = f"{x} > {y}"
            query = f"{x} > {y}" if truth else f"{y} > {x}"
            family = "direct_order"
        elif difficulty == "medium":
            x, y, z = names[:3]
            facts = f"{x} > {y}; {y} > {z}"
            query = f"{x} > {z}" if truth else f"{z} > {x}"
            family = "two_hop_order"
        else:
            x, y, z, u, v = names
            facts = f"{x} > {y}; {y} > {z}; {z} > {u}; {u} > {v}"
            query = f"{x} > {v}" if truth else f"{v} > {x}"
            family = "four_hop_order"
        answer = int(truth)
        leads = {
            "train": (f"In a strict total order: {facts}. Is {query}? True=1, false=0.", f"厳密な全順序で{facts}です。{query}は真ですか？真=1、偽=0。", f"在严格全序中：{facts}。{query}是否为真？真=1，假=0。"),
            "validation": (f"Given the strict ordering {facts}, decide whether {query}. Return 1 if true and 0 otherwise.", f"厳密な順序{facts}が与えられています。{query}か判定し、真なら1、そうでなければ0を返してください。", f"给定严格顺序{facts}，判断{query}。为真返回1，否则返回0。"),
            "test": (f"The symbols obey a strict total order with {facts}. Does {query} follow? Use 1 for yes, 0 for no.", f"記号は{facts}という厳密な全順序に従います。{query}は導けますか？はい=1、いいえ=0。", f"这些符号满足严格全序{facts}。能否推出{query}？是=1，否=0。")}
        forms = {split: leads[split]}
        parameters = [*opaque_ids, int(truth)]
    prompts = _three(*forms[split])
    if domain != "logic":
        parameters = [a, b, c, d]
    return prompts, str(answer), parameters, family, template_id


def generate_v2(seed=20260913, groups_per_cell=12):
    """Generate 4 domains × 3 splits × 3 difficulties × N semantic groups."""
    if groups_per_cell < 2 or groups_per_cell % 2:
        raise ValueError("groups_per_cell must be an even integer >= 2")
    rng = random.Random(seed)
    rows = []
    for domain in DOMAINS:
        for split in SPLITS:
            for difficulty in DIFFICULTIES:
                seen = set()
                for index in range(groups_per_cell):
                    # Collision retries only affect arithmetic parameters, not quotas.
                    for _ in range(100):
                        prompts, answer, params, family, template = _problem(
                            domain, split, difficulty, index, rng)
                        key = digest([2, domain, split, difficulty, family, params])
                        if key not in seen:
                            seen.add(key)
                            break
                    else:
                        raise RuntimeError("Could not generate a unique problem")
                    for language, prompt in zip(LANGUAGES, prompts):
                        rows.append({"id": f"v2-{key[:16]}-{language}", "group_id": key,
                                     "domain": domain, "language": language, "split": split,
                                     "difficulty": difficulty, "task_family": family,
                                     "template_id": template, "prompt": prompt, "answer": answer,
                                     "parameters": params, "world_seed": seed,
                                     "generator_version": 2})
    validate_rows(rows)
    audit_v2(rows, groups_per_cell)
    return rows


def audit_v2(rows, expected_groups_per_cell=None):
    validate_rows(rows)
    groups = {}
    for row in rows:
        if row.get("generator_version") != 2:
            raise ValueError("pilot-v2 requires generator_version=2")
        if row["answer"] != expected_answer(row):
            raise ValueError(f"Incorrect target for {row['id']}")
        groups.setdefault(row["group_id"], row)
    cell_counts = Counter((r["domain"], r["split"], r["difficulty"]) for r in groups.values())
    if len(cell_counts) != len(DOMAINS) * len(SPLITS) * len(DIFFICULTIES):
        raise ValueError("Missing domain/split/difficulty cell")
    counts = set(cell_counts.values())
    if len(counts) != 1 or (expected_groups_per_cell is not None and counts != {expected_groups_per_cell}):
        raise ValueError("Unbalanced domain/split/difficulty cells")
    template_splits = defaultdict(set)
    for row in groups.values():
        template_splits[row["template_id"]].add(row["split"])
    if any(len(splits) != 1 for splits in template_splits.values()):
        raise ValueError("Template id leaks across splits")
    logic = Counter((r["split"], r["difficulty"], r["answer"])
                    for r in groups.values() if r["domain"] == "logic")
    for split in SPLITS:
        for difficulty in DIFFICULTIES:
            if logic[(split, difficulty, "0")] != logic[(split, difficulty, "1")]:
                raise ValueError("Logic labels are not balanced")
    return {"rows": len(rows), "semantic_groups": len(groups),
            "groups_per_cell": next(iter(counts)),
            "cell_counts": {"/".join(k): v for k, v in sorted(cell_counts.items())},
            "logic_label_counts": {"/".join(k): v for k, v in sorted(logic.items())},
            "template_count": len(template_splits),
            "template_split_disjoint": True,
            "targets_recomputed": True,
            "languages": list(LANGUAGES), "dataset_sha256": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit-output", required=True)
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument("--groups-per-cell", type=int, default=12)
    args = parser.parse_args()
    rows = generate_v2(args.seed, args.groups_per_cell)
    output, audit_output = Path(args.output), Path(args.audit_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    audit_output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write("".join(canonical(row) + "\n" for row in rows))
    report = audit_v2(rows, args.groups_per_cell)
    report["dataset_sha256"] = file_hash(output)
    with audit_output.open("x") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(canonical(report))


if __name__ == "__main__":
    main()
