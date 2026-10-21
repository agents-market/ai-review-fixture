# Results

Six runs over the same pull request, the same diff, the same pipeline
(`code-review-security-audit@3.2.0`). The question each run answers: **how
many of the eleven planted weaknesses did it find, and what did it make up?**

The runs differ in one thing each — where they ran, the severity floor, and
how many findings the prompt allowed.

| # | Where | Severity floor | Prompt cap | Planted found | Missed | Invented |
|---|-------|----------------|-------------|----------------|--------|----------|
| 1 | CI, first run | medium | 8 | **8 / 11** | open redirect, prototype pollution, ReDoS | 0 |
| 2 | CI, second run | medium | 8 | **8 / 11** | path traversal, prototype pollution, ReDoS | 0 |
| 3 | local | medium | 8 | **8 / 11** | open redirect, prototype pollution, ReDoS | 0 |
| 4 | local | medium | 15 | **8 / 11** | SQL injection, command injection, path traversal | 0 |
| 5 | local | low | 8 | **5 / 11** | six of them | 3 |
| 6 | local | low | 15 | **7 / 11** | hardcoded secret, SQL injection, path traversal | 0 |

## What this says

**Every run finds eight of eleven. Which eight changes.** Run 1 found the
SQL injection and missed the open redirect; run 2 found the open redirect and
missed the path traversal; run 4 found both and missed the SQL injection
instead. The union across the four medium runs covers **all eleven** planted
weaknesses. A single review is a sample, not a census.

**The prompt's cap is not what limits it.** Raising "at most 8 findings" to
"at most 15" changed nothing — the model returned eight both times. The limit
is the model's own selection, not the instruction, so a cap change is not a
fix.

**The severity floor matters more than the cap.** At `low` the audit dropped
the hardcoded password and the SQL injection while adding three findings that
account for no planted vulnerability (an unclosed SQLite connection, a route
without authentication, unbounded resource use). At `medium` — the default —
no run invented anything. The default is the right one.

**Nothing was dropped for missing metadata.** Every finding carried a file
and a line; the counter that used to hide findings read zero, and the inline
comments landed on real diff lines.

**The catalogue is a closed set, and it shows.** Prototype pollution
(`CWE-1321`) is not among the 268 entries the model may choose from, so the
run that found it named it `CWE-915` — a real weakness class, a different
one. A weakness outside the catalogue has no id to cite, which is the point
of the closed set, and it is a gap worth knowing about.

## What it does not say

Six runs of a two-file diff are not a benchmark. The numbers describe this
fixture: eleven weaknesses, planted to be obvious, in two files. A real
repository has deeper flaws, and this says nothing about them.

## What would move the numbers

- **Review per file instead of per diff.** The model spends its eight
  findings on a diff of any size; two files reviewed separately would each
  get their own budget. This is a change to the pipeline, not to the
  workflow.
- **A second run, and the union.** The workflow already knows how to
  suppress a duplicate comment, so a second pass would add its six unseen
  findings without repeating the eight. It doubles the cost, and it doubles
  the noise.
- **A catalogue that covers what the model wants to say.** The gaps are
  known: `CWE-1321` was reached for, and the model had to settle for
  `CWE-915`.

## The style review, measured the same way

The style pipeline runs on the same pull request, and the first thing the
fixture showed about it was that it said everything twice.

`aggregate_style` emits its own copy of the findings array, re-derived from
the analyze stage's output. The two copies disagreed on line numbers, and
the consumer's merge drops a finding only when it repeats at the same file
and line — so both survived. On this diff: **9 comments for about six
issues**, with "no type annotation" three times, each at 99% confidence.

In 3.2.0 the aggregate copies the analyze stage's findings verbatim, and the
analyze stage is told that two findings with one cause are one finding, with
the other places named in the description. Severity and confidence were
separated as well: confidence is how sure you are the pattern is there,
severity is what it costs the reader.

| Version | Comments in one run | What they said |
|---|---|---|
| 3.1.0 | 9 | "no type annotation" three times at 99%, plus a hardcoded credential as CRITICAL |
| 3.2.0 | 5 findings, 3 new comments | one comment naming all five functions, `low` |

The security finding did not disappear: the hardcoded credential is the
audit's business, and the audit reports it as `CWE-798` in the same pull
request. Two pipelines, one job each.

## Reproducing it

```bash
python3 tools/ground_truth.py     # regenerate the ground truth from the markers
python3 tools/measure.py 1        # measure the pull request
```

`measure.py` reads the comments the review posted and compares them with
`.github/ground-truth.json`. `--since <ISO timestamp>` measures one run; a
pull request accumulates the comments of every run, and the union of two
runs answers a different question than either of them does.
