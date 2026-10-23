#!/usr/bin/env python3
"""Recount the runs with one map and one rule, and print the comparison.

Usage:
  python3 tools/compare_runs.py whole-1.json whole-2.json perfile-1.json ...

Every run wrote its raw findings to a JSON file. This reads them all and
answers two questions with the same rule applied to every run:

  how many of the planted weaknesses the run named by their own id, and
  how many it named under a different id (the weakness was found, the
  model called it something else).

The rule for "the same code": a comment on the same file within two lines
of the planted weakness. The planted weaknesses in one file are at least
five lines apart, so a comment cannot be counted for two of them.
"""
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRUTH = json.loads((ROOT / ".github/ground-truth-large.json").read_text())["vulnerabilities"]

# The same map the workflow uses to key a comment by the weakness it carries.
CANON = {
    "CWE-330": "CWE-338",
    "CWE-259": "CWE-798",
    "CWE-915": "CWE-1321",
    "CWE-321": "CWE-798",
}


def cwe(f):
    return str(f.get("cwe_id") or f.get("cwe") or "").strip().upper()


def cls(f):
    c = cwe(f)
    return CANON.get(c, c)


def visible(findings):
    merged = {}
    for f in findings:
        merged.setdefault(f"{f.get('file')}::{f.get('line')}::{cwe(f)}", f)
    return list(merged.values())


def planted_of(f, planted_ids):
    """The planted weakness this finding is, by id and by place."""
    for v in TRUTH:
        if v["cwe"].upper() == cls(f) and v["file"] == f.get("file"):
            return v
    # The same code, another id: same file, one line off. The planted
    # weaknesses in one file are at least three lines apart, so a comment
    # cannot be counted for two of them.
    for v in TRUTH:
        if v["file"] != f.get("file"):
            continue
        line = f.get("line")
        if line is None:
            continue
        if abs(int(line) - v["line"]) <= 1:
            return v
    return None


def count(path):
    data = json.loads(pathlib.Path(path).read_text())
    findings = data["findings"]
    seen = visible(findings)
    named, drift, extra = {}, {}, []
    for f in seen:
        v = planted_of(f, named)
        if v is None:
            extra.append(f)
            continue
        if v["cwe"].upper() == cls(f):
            named.setdefault(v["id"], v)
        else:
            drift.setdefault(v["id"], (v, f))
    summary = data.get("summary", {})
    return {
        "file": pathlib.Path(path).name,
        "named": len(named),
        "drift": drift,
        "extra": len(extra),
        "comments": len(seen),
        "calls": summary.get("calls"),
        "secs": summary.get("secs"),
    }


def main():
    paths = sys.argv[1:]
    groups = {"whole": [], "per-file": []}
    for p in paths:
        mode = "per-file" if "perfile" in pathlib.Path(p).name else "whole"
        groups[mode].append(count(p))

    for mode, runs in groups.items():
        if not runs:
            continue
        named = [r["named"] for r in runs]
        drift = [len(r["drift"]) for r in runs]
        extra = [r["extra"] for r in runs]
        comments = [r["comments"] for r in runs]
        print(f"\n=== {mode} === прогонов: {len(runs)}")
        print(f"  названо своим id:   {named}  → медиана {statistics.median(named)}")
        print(f"  найдено под чужим id: {drift}")
        print(f"  вместе:            {[n + d for n, d in zip(named, drift)]}  → медиана "
              f"{statistics.median([n + d for n, d in zip(named, drift)])} из {len(TRUTH)}")
        print(f"  лишних комментариев: {extra}  → медиана {statistics.median(extra)}")
        print(f"  всего комментариев: {comments}  → медиана {statistics.median(comments)}")
        print(f"  вызовов модели: {runs[0]['calls']}   времени: {runs[0]['secs']}s")

    if groups["whole"] and groups["per-file"]:
        w = statistics.median([r["named"] for r in groups["whole"]])
        p = statistics.median([r["named"] for r in groups["per-file"]])
        cw = statistics.median([r["comments"] for r in groups["whole"]])
        cp = statistics.median([r["comments"] for r in groups["per-file"]])
        print(f"\n  ИТОГ (по своему id): весь дифф {w} из {len(TRUTH)}, по файлам {p} из {len(TRUTH)}; "
              f"комментариев {cw} против {cp}")

    # The same line under another id. Not a count: a comment on the line of a
    # planted weakness may be a different weakness of the same code. It is a
    # list to read by hand.
    for mode, runs in groups.items():
        for r in runs:
            for v, f in r["drift"].values():
                print(f"  [{mode}] {v['cwe']} {v['file']}:{v['line']} названо как {cwe(f)}")


if __name__ == "__main__":
    main()
