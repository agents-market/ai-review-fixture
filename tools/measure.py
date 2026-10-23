#!/usr/bin/env python3
"""Measure the review against the ground truth.

Reads the findings the review posted on the pull request (inline comments and
the summary comment) and compares them with `.github/ground-truth.json`:

  found    — a comment names the same weakness class on the same file
  missed   — nothing on that file names it
  invented — a comment that no planted vulnerability accounts for

Matching is by file and CWE id, not by line: a reviewer that reports the right
weakness three lines away from the planted one found it. The line distance is
printed, so a near miss is visible.

Usage:
  python3 tools/measure.py [pull_request_number] [--since ISO8601] [--truth PATH]

`--since` measures one run: a pull request accumulates the comments of every
run, and the union of two runs answers a different question than either of
them does.

`--truth` picks the ground truth of another fixture — the second pull request
has its own.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "agents-market/ai-review-fixture"
CWE = re.compile(r"CWE-\d+", re.I)

# Words that carry no meaning in a title: "the user id goes into the SQL as
# text" must not match every comment because it starts with "the".
STOPWORDS = {
    "there", "their", "these", "those", "which", "while", "where", "into",
    "onto", "from", "with", "into", "that", "this", "the", "and", "for",
    "not", "but", "can", "may", "its", "are", "was", "were", "has", "have",
    "when", "than", "then", "them", "they", "here", "over", "under",
}


def gh(*args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return out.stdout


def comments(pr: int) -> list[dict]:
    raw = gh("api", f"repos/{REPO}/pulls/{pr}/comments", "--paginate")
    return json.loads(raw or "[]")


def issue_comments(pr: int) -> list[dict]:
    raw = gh("api", f"repos/{REPO}/issues/{pr}/comments", "--paginate")
    return json.loads(raw or "[]")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pr = int(args[0]) if args else 1
    since = None
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]
    truth_path = ROOT / ".github/ground-truth.json"
    if "--truth" in sys.argv:
        truth_path = ROOT / sys.argv[sys.argv.index("--truth") + 1]
    truth = json.loads(truth_path.read_text())["vulnerabilities"]
    every = comments(pr)
    summary = issue_comments(pr)
    # The reference workflow reviews with both pipelines. Each owns its threads
    # through a body marker, and only the security audit has a ground truth.
    marker = "am:code-review-security-audit"
    inline = [c for c in every if marker in (c.get("body") or "")]
    if since:
        # A re-run *updates* the comments it already posted instead of
        # creating new ones, so a comment can be older than the run that
        # wrote it. The time that belongs to a run is the last touch.
        inline = [c for c in inline
                  if max(c.get("created_at") or "", c.get("updated_at") or "") >= since]
    other = len(every) - len(inline)

    print(f"  PR #{pr}: {len(inline)} audit comments (+{other} from the other pipelines), "
          f"{len(summary)} summary comments")
    body = "\n".join(c.get("body", "") for c in summary)

    found, missed, invented = [], [], []
    for v in truth:
        cwe = v["cwe"].upper()
        hits = [
            c for c in inline
            if c.get("path") == v["file"] and cwe in (c.get("body") or "").upper()
        ]
        if hits:
            best = min(hits, key=lambda c: abs((c.get("line") or c.get("original_line") or 0) - v["line"]))
            line = best.get("line") or best.get("original_line")
            found.append((v, line, best.get("body", "").split("\n")[0][:70]))
        else:
            # The weakness may still be reported without its id. The words of
            # the title that carry the meaning — the stopwords of a title like
            # "The user id goes into the SQL as text" match every comment.
            words = [w for w in v["title"].lower().split()
                     if len(w) >= 5 and w not in STOPWORDS]
            loose = [
                c for c in inline
                if c.get("path") == v["file"]
                and any(w in (c.get("body") or "").lower() for w in words)
            ]
            missed.append((v, bool(loose)))

    claimed = {c.get("path") for c in inline}
    for c in inline:
        path = c.get("path")
        ids = set(CWE.findall(c.get("body") or ""))
        match = [
            v for v in truth
            if v["file"] == path and v["cwe"].upper() in {i.upper() for i in ids}
        ]
        if not match:
            invented.append((path, c.get("line"), sorted(ids), (c.get("body") or "").split("\n")[0][:70]))

    print(f"\n  FOUND {len(found)}/{len(truth)}")
    for v, line, title in found:
        d = (line - v["line"]) if line else None
        print(f"    ✓ {v['cwe']:>9} {v['file']}:{v['line']} → line {line}"
              f"{'' if d is None else f' (δ{d:+d})'}  {v['title'][:44]}")
    print(f"\n  MISSED {len(missed)}")
    for v, loose in missed:
        note = "  (reported without the id)" if loose else ""
        print(f"    ✗ {v['cwe']:>9} {v['file']}:{v['line']}  {v['title'][:44]}{note}")
    print(f"\n  INVENTED {len(invented)}")
    for path, line, ids, title in invented:
        print(f"    ? {path}:{line} {','.join(ids) or '—'}  {title}")

    ids_in_summary = sorted({m.upper() for m in CWE.findall(body)})
    print(f"\n  CWE ids in the summary comment: {', '.join(ids_in_summary) or '—'}")
    print(f"  files with comments: {', '.join(sorted(claimed)) or '—'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
