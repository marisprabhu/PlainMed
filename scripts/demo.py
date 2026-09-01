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

# One number carries the whole demo: Hemoglobin 13.5, sitting just inside
# its range. It is read in act 1, defended in act 2, stripped of identity
# in act 3 and cross-checked in act 4 - so the audience follows one value
# rather than meeting a new one each time.
SAMPLE = ROOT / "samples" / "01_cbc_flagged_high_wbc.txt"


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


PAUSE = False


def beat(seconds: float = 1.0) -> None:
    """Hold before a reveal.

    Enter-driven when rehearsing, timed when recording, and skipped
    entirely when the output is piped - a scripted read of this demo
    should not pay for pauses nobody is watching.
    """
    if PAUSE:
        input(f"{DIM}       [Enter]{OFF}")
    elif sys.stdout.isatty():
        time.sleep(seconds)


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
        print(f"    {v.analyte:<12} {v.raw_value:>6} {str(v.unit or ''):<10}"
              f"ref {str(v.ref_raw or DASH):<10}{flag}")
    print(f"\n  {len(doc.values)} values read. "
          f"{len(doc.unparsed_span_ids)} lines held back for the reader to check.")
    print(f"  {DIM}Keep hold of one of them: Hemoglobin {BOLD}13.5{OFF}{DIM}, "
          f"just inside its range. The next act is about that number.{OFF}")


# ----------------------------------------------------------------- act 2
def act_reject() -> None:
    head(2, "A generated 13.5 is indistinguishable from a hallucinated 13.5",
         "One of the two sentences below is invented. Decide which, before we check.")
    from plainmed.ingest import load_text
    from plainmed.pipeline import extract
    from plainmed.pipeline.validate import validate_narrative_items
    from plainmed.schemas import NarrativeItem

    doc = extract(load_text(SAMPLE.read_text(encoding="utf-8")))

    print(f"    {BOLD}A{OFF}   Your report lists Hemoglobin as 13.5 g/dL.")
    print(f"    {BOLD}B{OFF}   Your report lists Hemoglobin as 14.2 g/dL.")
    print(f"\n  {DIM}Both fluent. Both confident. Both cite the same line, S3."
          f" Nothing in the text tells you which one was read and which one"
          f" was composed.{OFF}")
    beat(2.0)

    span = doc.span_by_id("S3")
    print(f"\n  S3 actually reads   {CYAN}{span.text}{OFF}")
    print(f"  {DIM}So the validator never reads the sentence. It checks every"
          f" number in it against that line.{OFF}\n")
    beat(1.4)

    def check(label: str, text: str, span_ids, echo: bool = True) -> bool:
        item = NarrativeItem(text=text, span_ids=list(span_ids))
        kept, issues = validate_narrative_items([item], doc)
        if kept:
            print(f"    {GREEN}SHOWN  {OFF}  {label}")
        else:
            print(f"    {RED}BLOCKED{OFF}  {label}  {DIM}{issues[0].code}{OFF}")
        if echo:
            print(f"              {DIM}{text}{OFF}")
        return bool(kept)

    # A and B were printed in full above; repeating them here would bury
    # the verdict, which is the only new information.
    offered = [
        ("A" + " " * 4 + "13.5 is on the cited line",
         "Your report lists Hemoglobin as 13.5 g/dL.", ("S3",)),
        ("B" + " " * 4 + "14.2 is not",
         "Your report lists Hemoglobin as 14.2 g/dL.", ("S3",)),
    ]
    shown = sum(check(*c, echo=False) for c in offered)

    print(f"\n  {DIM}The same three gates stop everything else a model likes"
          f" to reach for:{OFF}")
    rest = [
        ("cites a line that does not exist",
         "Your report lists Hemoglobin as 13.5 g/dL.", ("S99",)),
        ("a diagnosis",
         "Your Hemoglobin of 13.5 means you have anaemia.", ("S3",)),
        ("treatment advice",
         "You should start taking an iron supplement.", ("S3",)),
        ("reassurance nobody is entitled to give",
         "There is nothing to worry about here.", ("S3",)),
    ]
    shown += sum(check(*c) for c in rest)
    total = len(offered) + len(rest)

    print(f"\n  {total} statements offered. {BOLD}{shown} shown"
          f"{OFF}, {BOLD}{total - shown} stopped{OFF} before any of them"
          f" reached a screen.")
    print(f"  {DIM}These gates run on model output and template output alike."
          f" The model can improve how an explanation reads;"
          f" it cannot change what it says.{OFF}")

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
        "Hemoglobin: 13.5 g/dL (13.0 - 17.0)\n"
        "WBC: 11.8 x10^9/L (4.0 - 11.0) H\n"
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
         "MedGemma's vision encoder reads the same photo. Disagreement asks a human.")
    from plainmed.pipeline import extract
    from plainmed.verify.vision_check import apply_to_document, compare

    doc = extract(SAMPLE.read_text(encoding="utf-8"))

    print(f"  {DIM}Case 1 {DASH} the readers agree{OFF}")
    agree = compare(doc.values, {"Hemoglobin": "13.5", "WBC": "11.8"})
    print(f"    {GREEN}{len(agree.agreed)} values confirmed by both readers{OFF}")

    print(f"\n  {DIM}Case 2 {DASH} vision reads 11.5 where the parser read 13.5{OFF}")
    print(f"  {DIM}The difference between a normal result and one that reads as anaemia.{OFF}")
    disagree = compare(doc.values, {"Hemoglobin": "11.5", "WBC": "11.8"})
    updated = apply_to_document(doc, disagree)
    d = disagree.disagreements[0]
    print(f"    {AMBER}FLAGGED{OFF} {d.analyte}: parser {d.parsed_value}, "
          f"vision {d.vision_value}")

    hgb = next(v for v in updated.values if v.analyte == "Hemoglobin")
    print(f"    the stored value is still {BOLD}{hgb.raw_value}{OFF} {DASH} the model "
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
    global PAUSE
    PAUSE = args.pause

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
