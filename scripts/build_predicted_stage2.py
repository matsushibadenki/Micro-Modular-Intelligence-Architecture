"""Build a stage-2 evaluation view from actual stage-1 predictions."""

import argparse
import json
from pathlib import Path

from mmia.harness import canonical, file_hash, validate_rows, write_json
from mmia.stage_views import stage2_text


def build(source_rows, prediction_rows):
    source = {row["id"]: row for row in source_rows}
    output, seen = [], set()
    for prediction in prediction_rows:
        source_id = prediction.get("source_id")
        if source_id not in source or source_id in seen:
            raise ValueError("Unknown or duplicate stage-1 source_id")
        seen.add(source_id)
        row = source[source_id]
        usable = prediction["status"] == "ok" and prediction["format_valid"]
        value = prediction["prediction"].strip() if usable else "0"
        output.append({**row, "prompt": stage2_text(row, value),
                       "intermediate_source": "stage1_prediction",
                       "predicted_intermediate": value,
                       "upstream_usable": usable,
                       "upstream_correct": prediction["correct"],
                       "upstream_completion_seconds": prediction["completion_seconds"]})
    expected = {row["id"] for row in source_rows if row["split"] == "validation"}
    if seen != expected:
        raise ValueError("Stage-1 predictions do not exactly cover validation source rows")
    validate_rows(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--stage1-predictions", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = [json.loads(line) for line in Path(args.source).read_text().splitlines()]
    predictions = [json.loads(line) for line in Path(args.stage1_predictions).read_text().splitlines()]
    rows = build(source, predictions)
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    with output.open("x") as stream:
        stream.write("".join(canonical(row) + "\n" for row in rows))
    write_json(output.with_suffix(".manifest.json"), {
        "status": "completed", "rows": len(rows),
        "source_sha256": file_hash(args.source),
        "stage1_predictions_sha256": file_hash(args.stage1_predictions),
        "output_sha256": file_hash(output),
        "upstream_usable": sum(row["upstream_usable"] for row in rows),
        "upstream_correct": sum(row["upstream_correct"] for row in rows)})


if __name__ == "__main__":
    main()
