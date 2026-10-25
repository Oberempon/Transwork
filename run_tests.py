"""
run_tests.py — Runs every sample input through the assistant, saves the outputs
to sample_outputs/, and writes TESTING_RESULTS.md with a results table.

Run:  python run_tests.py
Then open TESTING_RESULTS_latest_run.md and copy anything new into TESTING_RESULTS.md. Fill in the "Observation" column yourself —
that is the part that shows you understand where the AI works and fails.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import assistant

ROOT = Path(__file__).parent
INPUTS = ROOT / "sample_inputs"
OUTPUTS = ROOT / "sample_outputs"
OUTPUTS.mkdir(exist_ok=True)

TEST_LABELS = {
    "01_normal": "Normal enquiry",
    "02_very_long": "Very long enquiry",
    "03_ambiguous": "Ambiguous enquiry",
    "04_missing_info": "Missing information",
    "05_poorly_written": "Poorly written enquiry",
    "06_unexpected": "Unexpected input",
}


def timed(fn, *args, **kwargs):
    start = time.time()
    result = fn(*args, **kwargs)
    return result, round(time.time() - start, 1)


def main():
    rows = []

    # Function 1 — Business writing
    req = json.loads((INPUTS / "writing_request.json").read_text(encoding="utf-8"))
    reply, secs1 = timed(assistant.draft_customer_response, **req)
    (OUTPUTS / "writing_output.txt").write_text(reply, encoding="utf-8")
    print(f"[writing] done in {secs1}s")

    # Function 2 — Summarisation
    report = (INPUTS / "business_report.txt").read_text(encoding="utf-8")
    summary, secs2 = timed(assistant.summarise_document, report)
    (OUTPUTS / "summary_output.txt").write_text(summary, encoding="utf-8")
    print(f"[summary] done in {secs2}s")

    # Function 3 — Extraction on all six test types
    for path in sorted((INPUTS / "enquiries").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        try:
            result, secs3 = timed(assistant.extract_enquiry, text)
        except Exception as err:
            result, secs3 = {"error": str(err), "human_review_required": True}, 0
        (OUTPUTS / f"{path.stem}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        rows.append((TEST_LABELS.get(path.stem, path.stem), path.name, result, secs3))
        print(f"[extract] {path.name} done in {secs3}s")

    # Write the results report
    lines = [
        "# Testing Results — Transwork Business Assistant v1",
        "",
        f"Run on {datetime.now():%d %B %Y, %H:%M} using model `{assistant.MODEL}`.",
        "",
        "## Information extraction tests",
        "",
        "| Test type | Input file | Name | Category | Urgency | Confidence | Human review? | Time (s) | Observation |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for label, fname, r, secs in rows:
        lines.append(
            f"| {label} | `{fname}` | {r.get('customer_name') or '—'} | {r.get('category', 'ERROR')} | "
            f"{r.get('urgency', '—')} | {r.get('confidence', '—')} | "
            f"{'Yes: ' + ', '.join(r.get('review_reasons', [])) if r.get('human_review_required') else 'No'} | "
            f"{secs} | _fill in_ |"
        )
    lines += [
        "",
        "Full JSON for each test is in `sample_outputs/`.",
        "",
        f"## Business writing test\n\nOutput: `sample_outputs/writing_output.txt` ({secs1}s)\n",
        "Check: Did it use only the promises in the staff notes? Correct name and reference? Under 200 words?\n",
        f"## Summarisation test\n\nOutput: `sample_outputs/summary_output.txt` ({secs2}s)\n",
        "Check: Are all numbers copied exactly from the report? Did it add anything that is not in the report?\n",
        "## Findings (write in your own words)",
        "",
        "**What works well:**\n- \n",
        "**What does not work:**\n- \n",
        "**Where the AI can make mistakes:**\n- \n",
        "**Where a human must review the output:**\n- \n",
    ]
    (ROOT / "TESTING_RESULTS_latest_run.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nSaved outputs to sample_outputs/ and results to TESTING_RESULTS_latest_run.md (your write-up in TESTING_RESULTS.md is not touched)")


if __name__ == "__main__":
    main()
