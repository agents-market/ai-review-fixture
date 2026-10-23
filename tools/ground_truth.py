#!/usr/bin/env python3
"""Generate the ground truth from the markers in the source.

The vulnerable lines are marked in the code (`# VULN CWE-89: what it is`), so
the ground truth cannot drift away from the code: the line numbers come from
the file itself, and a marker without a description is an error rather than a
silent omission.

The markers are also a leak. The review reads the diff, and a diff that
carries the answers measures nothing: the model is handed the CWE id and a
description of the weakness it is supposed to find. So the markers are taken
out before the code is measured — `--strip` removes them and keeps the line
count, so the line numbers stay true — and `--verify` then checks that the
truth still matches the code it describes.

Usage:
  python3 tools/ground_truth.py                    # regenerate the truth
  python3 tools/ground_truth.py --strip            # take the answers out of the diff
  python3 tools/ground_truth.py --verify           # check the truth against the code
  python3 tools/ground_truth.py --fixture large    # the second fixture
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# name -> (directory with the code, truth file, markdown file)
FIXTURES = {
    "small": ("src", ".github/ground-truth.json", "GROUND_TRUTH.md"),
    "large": ("src-large", ".github/ground-truth-large.json", "GROUND_TRUTH_LARGE.md"),
}

MARKER = re.compile(r"(?:#|//)\s*VULN\s+(CWE-\d+)\s*:\s*(.+)")


def sources(directory: pathlib.Path):
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix in (".py", ".ts", ".js"):
            yield path


def scan(directory: pathlib.Path):
    """The planted weaknesses, with the line of code each one sits on."""
    findings, problems = [], []
    for path in sources(directory):
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = MARKER.search(line)
            if not m:
                continue
            cwe, title = m.group(1), m.group(2).strip()
            # The weakness is the statement after the marker.
            target = None
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].strip():
                    target = j + 1
                    break
            if target is None:
                problems.append(f"{path}:{i+1} — the marker has no code after it")
                continue
            findings.append({
                "id": f"{path.name}:{target}",
                "cwe": cwe,
                "file": str(path.relative_to(ROOT)),
                "line": target,
                "title": title,
                "snippet": lines[target - 1].strip(),
            })
    return findings, problems


def write_truth(fixture: str, findings: list[dict]) -> None:
    _, truth_path, md_path = FIXTURES[fixture]
    (ROOT / truth_path).write_text(
        json.dumps({"vulnerabilities": findings}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md = ["# Ground truth", "",
          f"{len(findings)} deliberate vulnerabilities. The line numbers come from the",
          "markers in the code (`tools/ground_truth.py`), so they cannot drift; the",
          "markers themselves are taken out of the diff before the review runs, so",
          "the review does not read the answers.", "",
          "| # | CWE | File | Line | What it is |", "|---|---|---|---|---|"]
    for n, f in enumerate(findings, 1):
        md.append(f"| {n} | `{f['cwe']}` | `{f['file']}` | {f['line']} | {f['title']} |")
    md += ["", "Regenerate with `python3 tools/ground_truth.py`, check with",
           "`python3 tools/ground_truth.py --verify`.", ""]
    (ROOT / md_path).write_text("\n".join(md), encoding="utf-8")


def strip(fixture: str) -> int:
    """Take the markers out of the code, keeping the line count."""
    directory = ROOT / FIXTURES[fixture][0]
    removed = 0
    for path in sources(directory):
        lines = path.read_text(encoding="utf-8").split("\n")
        changed = False
        for i, line in enumerate(lines):
            if MARKER.search(line):
                lines[i] = ""
                removed += 1
                changed = True
        if changed:
            path.write_text("\n".join(lines), encoding="utf-8")
    return removed


def verify(fixture: str) -> int:
    """The truth must still describe the code it was written for."""
    directory, truth_path, _ = FIXTURES[fixture]
    truth_file = ROOT / truth_path
    if not truth_file.exists():
        print(f"  no truth at {truth_path}")
        return 1
    truth = json.loads(truth_file.read_text(encoding="utf-8"))["vulnerabilities"]
    problems = []
    for v in truth:
        path = ROOT / v["file"]
        if not path.exists():
            problems.append(f"{v['file']} — the file is gone")
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        if v["line"] > len(lines):
            problems.append(f"{v['file']}:{v['line']} — past the end of the file")
            continue
        if v.get("snippet") and lines[v["line"] - 1].strip() != v["snippet"]:
            problems.append(f"{v['file']}:{v['line']} — the line moved or changed")
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"  {len(truth)} vulnerabilities, every one of them still on its line")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", choices=sorted(FIXTURES), default="small")
    ap.add_argument("--strip", action="store_true", help="take the markers out of the code")
    ap.add_argument("--verify", action="store_true", help="check the truth against the code")
    args = ap.parse_args()

    directory = ROOT / FIXTURES[args.fixture][0]

    if args.verify:
        return verify(args.fixture)

    if args.strip:
        removed = strip(args.fixture)
        print(f"  {removed} markers taken out of {directory.relative_to(ROOT)}")
        return 0

    if not directory.exists():
        print(f"  no {directory.relative_to(ROOT)} in this tree — the truth stays as it is")
        return 0

    findings, problems = scan(directory)
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    if problems:
        return 1
    if not findings:
        print("  no VULN markers in this tree — the ground truth stays as it is")
        return 0

    write_truth(args.fixture, findings)
    print(f"  {len(findings)} vulnerabilities, "
          f"{sum(1 for f in findings if f['file'].endswith('.py'))} Python, "
          f"{sum(1 for f in findings if f['file'].endswith('.ts'))} TypeScript")
    return 0


if __name__ == "__main__":
    sys.exit(main())
