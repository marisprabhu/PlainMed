"""Stage demo runner.

Five acts, each one a claim the audience watches being tested rather than a
slide asserting it. Runs offline, on CPU, in about fifteen seconds.

    python scripts/demo.py              # run everything
    python scripts/demo.py --act 3      # rehearse one act
    python scripts/demo.py --pause      # wait for Enter between acts
    python scripts/demo.py --plain      # no colour, no box characters

Nothing here is scripted output: every number printed is produced by the run
you are watching.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SAMPLE = ROOT / "samples" / "02_metabolic_panel_mixed.txt"


def _prepare_console() -> bool:
    """Enable ANSI and UTF-8, and report whether Unicode is safe to print.

    Windows consoles default to cp1252, which cannot encode box-drawing
    characters. A demo that raises UnicodeEncodeError on the presenter's own
    laptop is worse than a plain one, so this degrades instead of crashing.
    """
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        return True
    except Exception:
        return False


UNICODE_OK = _prepare_console()

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
AMBER = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
OFF = "\033[0m"

RULE = "--" if not UNICODE_OK else "──"
DOT = "-" if not UNICODE_OK else "·"
DASH = "-" if not UNICODE_OK else "—"


def plain() -> None:
    """Drop all styling, for a projector that mangles ANSI."""
    global BOLD, DIM, GREEN, AMBER, RED, CYAN, OFF, RULE, DOT, DASH
    BOLD = DIM = GREEN = AMBER = RED = CYAN = OFF = ""
    RULE, DOT, DASH = "--", "-", "-"


def head(number: int, title: str, claim: str) -> None:
    print(f"\n{BOLD}{CYAN}{RULE} Act {number} {DOT} {title}{OFF}")
    print(f"{DIM}{claim}{OFF}\n")


def run(command: list[str], label: str) -> bool:
    started = time.perf_counter()
    result = subprocess.run(
        [sys.executable, *command], capture_output=True, text=True, cwd=ROOT
    )
    elapsed = (time.perf_counter() - started) * 1000
    ok = result.returncode == 0
    mark = f"{GREEN}PASS{OFF}" if ok else f"{RED}FAIL{OFF}"
    print(f"  {mark}  {label}  {DIM}{elapsed:.0f} ms{OFF}")
    if not ok:
        print(f"{RED}{result.stdout[-600:]}{result.stderr[-600:]}{OFF}")
    return ok


# ----------------------------------------------------------------- act 1
def act_read() -> None:
    head(1, "It reads a real report",
         "Deterministic parsing. No model touches these numbers.")
    from plainmed.ingest import load_text
    from plainmed.pipeline import extract

    doc = extract(load_text(SAMPLE.read_text(encoding="utf-8")))
    for v in doc.values:
        flag = f"  [{v.flag}]" if v.flag else ""
        print(f"    {v.analyte:<12} {v.raw_value:>6} {str(v.unit or ''):<8}"
              f"ref {str(v.ref_raw or DASH):<10}{flag}")
    print(f"\n  {len(doc.values)} values read. "
          f"{len(doc.unparsed_span_ids)} lines held back for the reader to check.")


# ----------------------------------------------------------------- act 2
def act_reject() -> None:
    head(2, "It refuses to say things the report does not support",
         "The moment that separates this from a retrieval demo.")
    from plainmed.ingest import load_text
    from plainmed.pipeline import extract
    from plainmed.pipeline.validate import validate_narrative_items
    from plainmed.schemas import NarrativeItem

    doc = extract(load_text(SAMPLE.read_text(encoding="utf-8")))
    candidates = [
        ("a real finding, correctly cited",
         "Your report lists Glucose as 108 mg/dL."),
        ("a number that is not on the cited line",
         "Your Glucose is 168 mg/dL."),
        ("a diagnosis",
         "Your Glucose of 108 means you have diabetes."),
        ("reassurance nobody is entitled to give",
         "There is nothing to worry about here."),
    ]

    for label, text in candidates:
        item = NarrativeItem(text=text, span_ids=["S3"])
        kept, issues = validate_narrative_items([item], doc)
        if kept:
            print(f"  {GREEN}SHOWN  {OFF} {label}")
        else:
            print(f"  {RED}BLOCKED{OFF} {label}  {DIM}({issues[0].code}){OFF}")
        print(f"          {DIM}{text}{OFF}")

    print("\n  The same check runs on model output and template output alike.")


# ----------------------------------------------------------------- act 3
def act_boundary() -> None:
    head(3, "The GPU never learns who the patient is",
         "This is what lets the model run on commodity hardware.")
    from plainmed.llm.medgemma import _build_prompt
    from plainmed.pipeline import extract

    identified = (
        "Patient Name: Priya Sharma\n"
        "DOB: 04/11/1988   MRN: 88213-4\n"
        "Ordering physician: Dr A Rao\n"
        "Glucose 108 mg/dL 70-99 H\n"
        "Sodium 140 mmol/L 135-145\n"
    )
    print(f"  {DIM}What the patient uploads:{OFF}")
    for line in identified.strip().split("\n"):
        print(f"    {line}")

    prompt = _build_prompt(extract(identified))
    block = prompt[prompt.find("=== REPORT START"):prompt.find("=== REPORT END")]
    print(f"\n  {DIM}What the GPU receives:{OFF}")
    for line in block.strip().split("\n")[1:]:
        print(f"    {GREEN}{line}{OFF}")

    print()
    run(["scripts/deident_check.py"], "14 identifier categories, all withheld")


# ----------------------------------------------------------------- act 4
def act_second_reader() -> None:
    head(4, "Two readers, and they have to agree",
         "MedGemma's vision encoder checks the parser. Disagreement asks a human.")
    from plainmed.pipeline import extract
    from plainmed.verify.vision_check import apply_to_document, compare

    doc = extract("Glucose 108 mg/dL 70-99 H\nSodium 140 mmol/L 135-145\n")

    print(f"  {DIM}Case 1 {DASH} the readers agree{OFF}")
    agree = compare(doc.values, {"Glucose": "108", "Sodium": "140"})
    print(f"    {GREEN}{len(agree.agreed)} values confirmed by both readers{OFF}")

    print(f"\n  {DIM}Case 2 {DASH} vision reads 168, the parser read 108{OFF}")
    disagree = compare(doc.values, {"Glucose": "168", "Sodium": "140"})
    updated = apply_to_document(doc, disagree)
    d = disagree.disagreements[0]
    print(f"    {AMBER}FLAGGED{OFF} {d.analyte}: parser {d.parsed_value}, "
          f"vision {d.vision_value}")

    glucose = next(v for v in updated.values if v.analyte == "Glucose")
    print(f"    value is still {BOLD}{glucose.raw_value}{OFF} {DASH} the model "
          f"raises a question, it never overwrites an answer")


# ----------------------------------------------------------------- act 5
def act_proofs() -> None:
    head(5, "None of that was a claim",
         "Three checks that run in CI. Watch them run now.")
    ok = True
    ok &= run(["scripts/offline_check.py"], "runs with every socket blocked")
    ok &= run(["scripts/retention_check.py"], "writes nothing to disk or logs")
    ok &= run(["-m", "pytest", "-q"], "full test suite")
    print()
    if ok:
        print(f"  {GREEN}{BOLD}Every claim in this demo was just verified live.{OFF}")
    else:
        print(f"  {RED}Something failed. Do not present until it is green.{OFF}")


ACTS = [act_read, act_reject, act_boundary, act_second_reader, act_proofs]


def main() -> int:
    parser = argparse.ArgumentParser(description="PlainMed stage demo")
    parser.add_argument("--act", type=int, choices=range(1, 6),
                        help="run a single act, for rehearsal")
    parser.add_argument("--pause", action="store_true",
                        help="wait for Enter between acts")
    parser.add_argument("--plain", action="store_true",
                        help="no colour or box characters")
    args = parser.parse_args()

    if args.plain:
        plain()

    print(f"\n{BOLD}PlainMed{OFF} {DIM}{DOT} clear reports, private by design{OFF}")

    acts = [ACTS[args.act - 1]] if args.act else ACTS
    for index, act in enumerate(acts):
        act()
        if args.pause and index < len(acts) - 1:
            input(f"\n{DIM}  [Enter to continue]{OFF}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
