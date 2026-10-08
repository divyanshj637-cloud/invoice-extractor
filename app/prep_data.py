import json    # read/write JSON (label files, split file)
import random  # random picking and shuffling
from pathlib import Path  # file and folder locations

# ---------- SETTINGS (change values here only) ----------
OCR_DIR = Path("data/sroie/ICDAR-2019-SROIE-master/data/box")  # receipt csvs: 8 position numbers + text per line
KEY_DIR = Path("data/sroie/ICDAR-2019-SROIE-master/data/key")  # dataset's own answers (hints only, can be wrong)
OUT_DIR = Path("data/raw")       # clean receipt text goes here (git ignores data/)
LABEL_DIR = Path("eval/labels")  # your answer sheets (these get pushed to GitHub)
# Paths start from the project folder, so always run from C:\invoice-extractor.

N_SROIE = 35  # receipts taken from the dataset
N_OWN = 15    # spots for your own documents (35 + 15 = 50)
N_DEV = 15    # of the 50, kept for practice; the other 35 are the locked test set


def sroie_to_text(path: Path) -> str:
    # Input: one receipt csv. Output: its text with the 8 position numbers removed.
    lines = []  # collects the cleaned lines

    for one_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        # read whole file -> cut into lines -> loop one line at a time
        # (errors="ignore" skips unreadable characters instead of crashing)
        parts = one_line.split(",", 8)  # cut at first 8 commas only -> 8 numbers + 1 text piece
        # stopping at 8 keeps commas inside the text (like addresses) in one piece
        if len(parts) == 9:  # skips blank or broken lines
            lines.append(parts[8].strip())  # [8] = the text (counting starts at 0); strip trims edge spaces

    return "\n".join(lines)  # runs once, after the loop: one text, one line per item
    # This only returns the text. Saving happens later, in main().


def empty_label() -> dict:
    # One blank answer sheet. Field names match the Invoice schema (schema.py).
    # None = not filled in yet (saved as null in the file).
    return {
        "vendor": None,
        "invoice_number": None,  # no "#"
        "invoice_date": None,    # YYYY-MM-DD
        "currency": None,        # INR/USD/EUR/MYR, only if printed
        "subtotal": None,
        "tax": None,
        "total": None,           # final amount to pay
        "line_items": None,      # None = rows not labeled (skipped); [] = labeled, no rows
        "_note": "",             # your comments; keys starting with _ are ignored by evaluation
    }


def main():
    # ===== PART 1: setup =====
    if any(OUT_DIR.glob("*.txt")):  # any .txt already in data/raw?
        raise SystemExit("data/raw already has files. Delete them first if you really want to redo this.")
        # stops a re-run from wiping out your labeling work

    OUT_DIR.mkdir(parents=True, exist_ok=True)    # creates data/raw
    LABEL_DIR.mkdir(parents=True, exist_ok=True)  # creates eval/labels
    # parents=True: also makes missing folders above it; exist_ok=True: no error if it exists

    random.seed(42)  # fixes the random sequence, so every run (or computer) picks the same receipts
    # your labels are tied to specific receipts, so the picks must never change

    sroie_ids = sorted(p.stem for p in OCR_DIR.glob("*.csv"))
    # every receipt name without ".csv": ['000', '001', ...]. Just names, nothing opened yet.
    # sorted = same order every time, which the seed needs to repeat the same picks

    chosen = random.sample(sroie_ids, N_SROIE)  # picks 35 different names at random ['417', '023', '552', '108', ...]   # 35 names, nothing else

    source_map = {}  # source_map = {"doc_001": "617"}    (the only place that records the link)
    hints_found = 0  # counts dataset answer files found (0 at the end means something is wrong)

       # ===== PART 2: build the 35 SROIE docs (runs once per picked receipt) =====
    for i, sroie_id in enumerate(chosen, start=1):
        # each round gives two values: i = counter (1, 2, 3...), sroie_id = next csv name
        # round 1: i=1, sroie_id="X51005230617"   round 2: i=2, sroie_id="X51005441234"
        doc_id = f"doc_{i:03d}"  # :03d = at least 3 digits, zero-filled: 1 -> "doc_001", 35 -> "doc_035"

        # 1) clean the receipt text and save it as a file
        text = sroie_to_text(OCR_DIR / f"{sroie_id}.csv")
        # OCR_DIR / "name.csv" builds the path: data/sroie/.../box/X51005230617.csv
        # text holds the cleaned receipt in memory only (8 numbers removed, one line per item)
        (OUT_DIR / f"{doc_id}.txt").write_text(text, encoding="utf-8")
        # this line is what creates the file: data/raw/doc_001.txt

        # 2) fresh blank answer sheet (new dictionary each round, so docs never share one)
        label = empty_label()
        # still only in memory: gets saved to eval/labels/doc_001.json later in this loop

        # (answer-file hint, saving the sheet and source_map come next)

        matches = list(KEY_DIR.glob(f"{sroie_id}.*"))
        # Looks in the key folder for the file with this receipt's name and ANY ending
        # (".*"). list(...) turns the result into a list: one item if found, else empty.

        # 3) dataset's own answer as a hint (only if its file exists and is valid JSON)
        matches = list(KEY_DIR.glob(f"{sroie_id}.*"))
        # searches ONLY the key folder for a file named like this receipt (any extension)
        # found: [Path(".../key/617.txt")]    not found: []    (nothing is read yet)

        if matches:  # one yes/no check, NOT a loop: [] = False, so no file skips the block
            try:  # "attempt this; it might fail"
                label["_sroie_hint"] = json.loads(
                    matches[0].read_text(encoding="utf-8", errors="ignore")
                )
                # inside-out: matches[0] = file path
                # -> read_text = its contents as a plain string (looks like JSON, but is just characters)
                # -> json.loads = string to a real dictionary, e.g. {"company": "...", "total": "9.00"}
                # -> stored in the sheet as a new field "_sroie_hint" (the _ means evaluation ignores it)
                # json.loads is the only line that can fail, so the line below is skipped if it does
                hints_found += 1  # counts only hints that were really added
            except json.JSONDecodeError:  # the file's text isn't valid JSON
                pass  # do nothing: no hint for this doc, the loop carries on

        # 4) save the sheet as a .json file (indented under `for`, so it runs every round)
        (LABEL_DIR / f"{doc_id}.json").write_text(
            json.dumps(label, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        # json.dumps = dictionary -> JSON text (write_text can't save a dictionary directly)
        # indent=2 = one field per line, easy to edit by hand; ensure_ascii=False = keep special characters
        # write_text creates: eval/labels/doc_001.json  (the hint is included because this runs after step 3)
        # only the cleaned receipts are .txt; the label sheets are .json

        # 5) record the pair (also every round)
        source_map[doc_id] = sroie_id
        # e.g. "doc_001" -> "617": your new name -> the dataset's real receipt name
        # lives in memory only for now: Part 3 saves it to eval/source_map.json

    # ===== PART 3: your own documents, the dev/test split, and the summary =====

    for i in range(N_SROIE + 1, N_SROIE + N_OWN + 1):
        # range(36, 51) gives the numbers 36 up to 50 (it stops one before the end number).
        # So this loops 15 times, once per spot for your own documents.
        doc_id = f"doc_{i:03d}"
        (OUT_DIR / f"{doc_id}.txt").write_text("", encoding="utf-8")
        # Creates an EMPTY text file. "" is empty text. You paste your own document in later.
        (LABEL_DIR / f"{doc_id}.json").write_text(json.dumps(empty_label(), indent=2), encoding="utf-8")
        # A fresh blank answer sheet for it.
        source_map[doc_id] = "own"
        # Records that this one came from you, not from the dataset.

    all_ids = sorted(source_map)
    # source_map now has all 50 names. Sorting it gives the list doc_001 ... doc_050.

    random.shuffle(all_ids)
    # Shuffles the list like a deck of cards (the same way each run, thanks to the seed).

    split = {"dev": sorted(all_ids[:N_DEV]), "test": sorted(all_ids[N_DEV:])}
    # all_ids[:15] = the first 15 names  -> "dev", the practice pile.
    # all_ids[15:] = everything after the first 15 -> "test", the locked final exam pile.
    # sorted(...) puts each pile back in neat order.

    Path("eval/split.json").write_text(json.dumps(split, indent=2), encoding="utf-8")
    Path("eval/source_map.json").write_text(json.dumps(source_map, indent=2), encoding="utf-8")
    # Saves both lists to files, so the split can never quietly change.

    print(f"Created {len(source_map)} documents: {len(split['dev'])} dev, {len(split['test'])} test")
    print(f"Answer hints found for {hints_found} of {N_SROIE} SROIE documents")
    # len(...) counts items. These two lines show you what happened.


main()
# Everything above only DESCRIBES the functions. Nothing runs until this line calls main().
# This line has NO indentation, because it's outside the function.
                            
                              
                              
                              
                                                                        