"""Scan eval/labels/*.json and print any label that looks wrong.
Run from project root: uv run python -m eval.check_labels
If 'No module named eval': create an empty eval/__init__.py"""
import json
from pathlib import Path

from pydantic import ValidationError

from app.schema import Invoice  # Phase 2 schema: valid dates, currencies, totals

LABEL_DIR = Path("eval/labels")  # folder holding doc_001.json ... doc_050.json
FIELDS = ["vendor", "invoice_number", "invoice_date", "currency", "subtotal", "tax", "total"]  # the 7 labeled fields
NUMBER_FIELDS = ["subtotal", "tax", "total"]  # must be numbers: 108.5, not "108.5"


def check_one(path: Path) -> list[str]:
    """Return a list of problems for one label file. Empty list = OK.
    (': Path' and '-> list[str]' are only hints: takes a path, gives back text messages)"""
    # CHECK 1: is the file valid JSON? (a missing comma or quote breaks it)
    try:
        label = json.loads(path.read_text(encoding="utf-8"))  # file text -> dict
    except json.JSONDecodeError as e:
        return [f"not valid JSON ({e})"]  # return ends the function here; main() prints the message

    problems = []  # each failed check below adds one message

    # CHECK 2: every expected key exists (a deleted line shows up here)
    # FIELDS + [...] joins two lists: the 7 fields plus 2 more = 9 expected keys
    missing = [k for k in FIELDS + ["line_items", "_note"] if k not in label]
    if missing:  # non-empty list counts as True
        problems.append(f"missing keys: {missing}")

    # CHECK 3: label never filled (all 7 fields still null)
    # .get() gives None for a missing key instead of crashing
    if all(label.get(f) is None for f in FIELDS):
        problems.append("looks unfilled (every field is null)")

    # CHECK 4: numbers typed as text, e.g. "48.95" instead of 48.95
    for f in NUMBER_FIELDS:
        v = label.get(f)
        if v is not None and not isinstance(v, (int, float)):  # null is fine, a string is not
            problems.append(f"{f} must be a number, got text: {v!r}")  # !r shows quotes, so "48.95" looks like text

    # CHECK 5: run the Phase 2 Invoice schema on the label
    data = {k: v for k, v in label.items() if not k.startswith("_")}  # drop _note, _sroie_hint
    if data.get("line_items") is None:
        data.pop("line_items", None)  # null = not labeled, so don't pass it to the schema
    note = label.get("_note") or ""  # "or" makes a null note safe for the 'in' test
    try:
        Invoice(**data)
    except ValidationError as e:
        for err in e.errors():
            msg = err["msg"]
            if "does not match total" in msg and "math inconsistent" in note:
                continue  # deliberately flagged mismatch, skip this one error
            where = ".".join(str(x) for x in err["loc"]) or "totals"
            problems.append(f"{where}: {msg}")

    return problems


def main():
    paths = sorted(LABEL_DIR.glob("*.json"))
    bad = 0
    for path in paths:
        problems = check_one(path)
        if problems:
            bad += 1
            print(path.name)
            for p in problems:
                print("   -", p)
    print(f"\n{len(paths) - bad} of {len(paths)} label files OK")


main()