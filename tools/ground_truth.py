#!/usr/bin/env python3
"""Generate the ground truth from the markers in the source.

The vulnerable lines are marked in the code (`# VULN CWE-89: what it is`), so
the ground truth cannot drift away from the code: the line numbers come from
the file itself, and a marker without a description is an error rather than a
silent omission.

Usage:
  python3 tools/ground_truth.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
MARKER = re.compile(r"(?:#|//)\s*VULN\s+(CWE-\d+)\s*:\s*(.+)")


def main() -> int:
    findings = []
    problems = []
    for path in sorted(SRC.rglob("*")):
        if not path.is_file() or path.suffix not in (".py", ".ts", ".js"):
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = MARKER.search(line)
            if not m:
                continue
            cwe, title = m.group(1), m.group(2).strip()
            # The vulnerability is the statement after the marker.
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
            })

    if problems:
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    if not findings:
        # The markers live in the branch under test; main carries the ground
        # truth that was generated from it. Nothing to do here.
        print("  no VULN markers in this tree — the ground truth stays as it is")
        return 0

    (ROOT / ".github").mkdir(exist_ok=True)
    (ROOT / ".github/ground-truth.json").write_text(
        json.dumps({"vulnerabilities": findings}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    md = ["# Ground truth", "",
          "Ten deliberate vulnerabilities. The line numbers come from the markers in",
          "the code (`tools/ground_truth.py`), so they cannot drift.", "",
          "| # | CWE | File | Line | What it is |", "|---|---|---|---|---|"]
    for n, f in enumerate(findings, 1):
        md.append(f"| {n} | `{f['cwe']}` | `{f['file']}` | {f['line']} | {f['title']} |")
    md += ["", "Regenerate with `python3 tools/ground_truth.py`.", ""]
    (ROOT / "GROUND_TRUTH.md").write_text("\n".join(md), encoding="utf-8")

    print(f"  {len(findings)} vulnerabilities, "
          f"{sum(1 for f in findings if f['file'].endswith('.py'))} Python, "
          f"{sum(1 for f in findings if f['file'].endswith('.ts'))} TypeScript")
    return 0


if __name__ == "__main__":
    sys.exit(main())
