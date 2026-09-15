"""Create explicit stage-1 and teacher-intermediate stage-2 views of pilot-v3."""

import argparse
import json
from pathlib import Path

from .harness import LANGUAGES, SUFFIX, canonical, file_hash, validate_rows, write_json


def _finish(text, language):
    return text + "\n" + SUFFIX[language]


def stage1_text(row):
    p, family, language = row["parameters"], row["task_family"], row["language"]
    if family == "acceleration_sum_then_force":
        texts = {"en": f"Compute only the intermediate acceleration {p['a']}+{p['b']} m/s^2.",
                 "ja": f"中間加速度{p['a']}+{p['b']} m/s²だけを計算してください。",
                 "zh": f"只计算中间加速度{p['a']}+{p['b']} m/s²。"}
    elif family == "acceleration_product_sum_then_force":
        texts = {"en": f"Compute only the intermediate acceleration ({p['a']}+{p['b']})*{p['scale']} m/s^2.",
                 "ja": f"中間加速度({p['a']}+{p['b']})×{p['scale']} m/s²だけを計算してください。",
                 "zh": f"只计算中间加速度({p['a']}+{p['b']})×{p['scale']} m/s²。"}
    elif family == "acceleration_two_products_then_force":
        expression = f"{p['a']}*{p['b']}+{p['c']}*{p['d']}"
        texts = {"en": f"Compute only the intermediate acceleration {expression} m/s^2.",
                 "ja": f"中間加速度{expression} m/s²だけを計算してください。",
                 "zh": f"只计算中间加速度{expression} m/s²。"}
    elif family in {"code_sum_then_product", "code_weighted_then_offset", "code_even_sum_then_scale",
                    "code_acceleration_then_force", "code_weighted_acceleration_then_force",
                    "code_filtered_acceleration_then_work"}:
        if family in {"code_sum_then_product", "code_acceleration_then_force"}:
            code = f"print(sum([{p['a']}, {p['b']}]))"
        elif family == "code_weighted_then_offset":
            code = f"v=[{p['a']},{p['b']},{p['c']}]\nprint(sum((i+1)*x for i,x in enumerate(v)))"
        elif family == "code_even_sum_then_scale":
            code = f"v={p['values']}\nprint(sum(x for x in v if x%2==0))"
        elif family == "code_weighted_acceleration_then_force":
            code = f"v=[{p['a']},{p['b']}]\nprint(sum((i+1)*x for i,x in enumerate(v)))"
        else:
            code = f"v={p['values']}\nprint(sum(x for x in v if x>{p['threshold']}))"
        texts = {"en": f"What intermediate integer does this Python code print?\n{code}",
                 "ja": f"次のPythonコードが中間値として出力する整数は何ですか？\n{code}",
                 "zh": f"以下Python代码输出哪个中间整数？\n{code}"}
    elif family.startswith("logic_"):
        texts = {"en": f"In a strict total order, {p['facts']}. Does {p['query']} follow? True=1, false=0.",
                 "ja": f"厳密な全順序で{p['facts']}です。{p['query']}は導けますか？真=1、偽=0。",
                 "zh": f"在严格全序中，{p['facts']}。能否推出{p['query']}？真=1，假=0。"}
    else:
        raise ValueError(f"Unknown family: {family}")
    return _finish(texts[language], language)


def stage2_text(row, intermediate):
    p, family, language, value = row["parameters"], row["task_family"], row["language"], str(intermediate)
    if family.startswith("acceleration_"):
        texts = {"en": f"The intermediate acceleration is {value} m/s^2. For mass {p['mass']} kg, compute F=ma in N.",
                 "ja": f"中間加速度は{value} m/s²です。質量{p['mass']} kgについてF=maをNで計算してください。",
                 "zh": f"中间加速度为{value} m/s²。质量为{p['mass']} kg，按F=ma计算力，单位N。"}
    elif family == "code_sum_then_product" or family == "code_even_sum_then_scale":
        texts = {"en": f"The intermediate code output is {value}. Multiply it by {p['factor']}.",
                 "ja": f"コードの中間出力は{value}です。{p['factor']}倍してください。",
                 "zh": f"代码的中间输出为{value}。将其乘以{p['factor']}。"}
    elif family == "code_weighted_then_offset":
        texts = {"en": f"The intermediate code output is {value}. Subtract {p['offset']} from it.",
                 "ja": f"コードの中間出力は{value}です。そこから{p['offset']}を引いてください。",
                 "zh": f"代码的中间输出为{value}。从中减去{p['offset']}。"}
    elif family.startswith("logic_"):
        texts = {"en": f"The logic result is {value}. If it is 1 compute {p['a']}+{p['b']}; if 0 compute {p['a']}-{p['b']}.",
                 "ja": f"論理結果は{value}です。1なら{p['a']}+{p['b']}、0なら{p['a']}-{p['b']}を計算してください。",
                 "zh": f"逻辑结果为{value}。若为1计算{p['a']}+{p['b']}；若为0计算{p['a']}-{p['b']}。"}
    elif family in {"code_acceleration_then_force", "code_weighted_acceleration_then_force"}:
        texts = {"en": f"The code produced acceleration {value} m/s^2. For mass {p['mass']} kg, compute F=ma in N.",
                 "ja": f"コードが出した加速度は{value} m/s²です。質量{p['mass']} kgについてF=maをNで計算してください。",
                 "zh": f"代码得到加速度{value} m/s²。质量为{p['mass']} kg，按F=ma计算力，单位N。"}
    elif family == "code_filtered_acceleration_then_work":
        texts = {"en": f"The code produced acceleration {value} m/s^2. For mass {p['mass']} kg over {p['distance']} m, compute W=mad in J.",
                 "ja": f"コードが出した加速度は{value} m/s²です。質量{p['mass']} kg、距離{p['distance']} mについてW=madをJで計算してください。",
                 "zh": f"代码得到加速度{value} m/s²。质量{p['mass']} kg、距离{p['distance']} m，按W=mad计算功，单位J。"}
    else:
        raise ValueError(f"Unknown family: {family}")
    return _finish(texts[language], language)


def make_views(rows):
    stage1, stage2 = [], []
    for row in rows:
        common = {k: v for k, v in row.items() if k not in {"id", "prompt", "answer"}}
        stage1.append({**common, "id": "s1-" + row["id"], "source_id": row["id"],
                       "stage": 1, "prompt": stage1_text(row),
                       "answer": row["intermediate_answers"][0]})
        stage2.append({**common, "id": "s2-" + row["id"], "source_id": row["id"],
                       "stage": 2, "intermediate_source": "teacher",
                       "prompt": stage2_text(row, row["intermediate_answers"][0]),
                       "answer": row["answer"]})
    validate_rows(stage1)
    validate_rows(stage2)
    return stage1, stage2


def audit_views(source, stage1, stage2):
    if len(source) != len(stage1) or len(source) != len(stage2):
        raise ValueError("Stage views must preserve every source row")
    source_by_id = {r["id"]: r for r in source}
    for first, second in zip(stage1, stage2):
        original = source_by_id[first["source_id"]]
        if second["source_id"] != original["id"] or first["group_id"] != second["group_id"]:
            raise ValueError("Stage/source identity mismatch")
        if first["answer"] != original["intermediate_answers"][0] or second["answer"] != original["answer"]:
            raise ValueError("Stage target mismatch")
        if str(first["answer"]) not in second["prompt"]:
            raise ValueError("Teacher intermediate missing from stage-2 prompt")
    return {"source_rows": len(source), "stage1_rows": len(stage1), "stage2_rows": len(stage2),
            "source_semantic_groups": len({r["group_id"] for r in source}),
            "identity_preserved": True, "targets_preserved": True,
            "teacher_intermediate_in_stage2": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--stage1-output", required=True)
    parser.add_argument("--stage2-output", required=True)
    parser.add_argument("--audit-output", required=True)
    args = parser.parse_args()
    source = [json.loads(line) for line in Path(args.source).read_text().splitlines()]
    stage1, stage2 = make_views(source)
    for path, rows in ((args.stage1_output, stage1), (args.stage2_output, stage2)):
        with Path(path).open("x") as stream:
            stream.write("".join(canonical(row) + "\n" for row in rows))
    report = audit_views(source, stage1, stage2)
    report.update({"source_sha256": file_hash(args.source),
                   "stage1_sha256": file_hash(args.stage1_output),
                   "stage2_sha256": file_hash(args.stage2_output)})
    write_json(args.audit_output, report)
    print(canonical(report))


if __name__ == "__main__":
    main()
