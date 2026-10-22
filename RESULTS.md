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

A later CI run added the open redirect to the union (four of its findings were
new comments; the rest repeated lines the earlier runs had already covered).
One CI run failed outright — `Retry exhausted after 4 attempts`, the provider,
not the pipeline — and the summary comment said so in one line: "Pipeline did
not complete". That is the honest path, and it is the one the summary comment
now takes when there is no result at all.

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

## The second pass (3.3.0)

The pipeline now reviews twice. The second pass reads the first pass's findings
and is asked for the gaps only — the weaknesses the first pass did not report.

**In CI, on the published 3.3.0, on this pull request: all eleven — three runs
in a row.** Twelve, twelve and fourteen findings; eleven of them are the
planted weaknesses every time, and the rest are observations about missing
controls (`CWE-639`, "no auth / no CSRF", "TOCTOU on the archive"). The report
names every planted weakness:

| Severity | Findings | What they are |
|---|---|---|
| critical | 3 | pickle deserialization, the committed password, `os.system` |
| high | 6 | SQL injection, path traversal, SSRF, XSS, prototype pollution, `Math.random` tokens |
| medium | 2 of 3 | open redirect, the ReDoS regex |

(The prototype pollution is reported under `CWE-915`, the neighbouring class the
catalogue does have — see the catalogue note below. The weakness and the line
are right; the id is the neighbour's.)

The same diff, the same ground truth, measured locally, the default `medium`
floor:

| # | deep_review | gap_review | Planted found | Extra findings |
|---|-------------|------------|----------------|-----------------|
| 1 | 8 | 0 | 8 / 11 | 0 |
| 2 | 8 | 3 | **11 / 11** | 0 |
| 3 | 11 | 5 | **11 / 11** | 5 |
| 4 | 8 | 3 | **11 / 11** | 0 |
| 5 | 8 | 4 | 8 / 11 | 4 |
| 6 | 5 | 8 | 8 / 11 | 5 |

Five more runs died on the provider (`MiniMax API 529 overloaded_error`) before
they produced anything — including the first CI attempt at 3.3.0, which then
recovered on the retry. The provider was the flakier half of this measurement.

**The union is never worse than one pass.** The second pass only adds findings;
it cannot lose one. In three of six local runs it reached all eleven, and in the
best run the union was exactly the eleven planted weaknesses — no duplicate,
nothing invented. In the other three it added findings the reader does not need
without closing a gap.

**Where the extra findings come from.** The second pass sometimes reports a
weakness the first pass had already reported under a different CWE id or on a
nearby line, and sometimes reports the *absence* of a control (no authentication
on a route, no CSRF token). Two rules in its prompt address both: a weakness is
the same weakness when it is the same code, and a finding needs the line where
something wrong happens. The rules reduce the noise; they do not remove it.

**Cost.** One more model call: about $0.035 per review instead of $0.018.

Four prompt variants were measured over four runs each. They differ by one to
three runs at 11 of 11 — inside the noise of a sample that size. The one that
shipped is the variant whose second pass fires most reliably.

## The noise, counted the way the reader sees it (2026-10-22)

The "Extra findings" column above counts *raw* findings: two passes reporting
the same weakness twice, or under a neighbouring CWE id, count as two. The
reader never sees that — the Action merges every stage's findings by
`file::line::cwe` and posts one comment per survivor. Two things had also
drifted in the instrument: the probe sent `language: typescript` while the CI
sends `language: generic` (this diff is TypeScript and Python at once), and
the earlier local runs were made while the report itself was still inside the
reviewed diff. Both are fixed; the probe now sends what the CI sends.

Six runs of the published spec, the same diff, the `medium` floor, counting
what the reader gets:

| # | deep_review | gap_review | Reader-visible comments | Planted found | Extra comments |
|---|-------------|------------|-------------------------|---------------|----------------|
| 1 | 8 | 0 | 8 | 8 / 11 | 0 |
| 2 | 8 | 3 | 11 | **11 / 11** | 0 |
| 3 | 8 | 3 | 11 | **11 / 11** | 0 |
| 4 | 11 | 0 | 11 | **11 / 11** | 0 |
| 5 | 8 | 6 | 12 | 10 / 11 | 1 (`CWE-770`) |
| 6 | 8 | 0 | 8 | 8 / 11 | 0 |

**One extra comment in six runs.** Most of the "extra findings" in the table
above were the same weakness counted twice.

Three ways to make the second pass quieter were measured. Five to seven runs
each, the same diff and the same floor; the first group was measured before
the instrument fix (`language: typescript`) and the second after it
(`language: generic`), so the rows are comparable only inside a group.

| Variant | What changed | Planted (sum of runs) | Extra comments |
|---------|--------------|-----------------------|----------------|
| *`language: typescript`, 5–7 runs* | | | |
| published | — | 51 / 55 | 0 |
| v2 | the two rules rewritten | 53 / 55 | 3 |
| v3 | a third rule: judge your own fix | 40 / 55 | 4 |
| v4 | a separate `observations` list | 65 / 77 | 0 |
| *`language: generic`, 6 runs each* | | | |
| published | — | 59 / 66 | 1 |
| v4 | the same split | 62 / 66 | 4 |

**None of them is better.** The differences sit inside the noise of a
five-run sample: this fixture answers "11 of 11 or not" with a spread of
three. Two things are worth keeping from the experiment:

- The schema split works as designed — the missing-control remarks ("the
  /comments route has no authentication check", "no rate limit on
  /password-reset") land in `observations` and never become comments. But the
  model does not do it every time: two of v4's four extra comments were
  exactly that class, in `findings`.
- The noise that is left has two kinds, and only one of them can be fixed
  without the model's cooperation. The second pass sometimes reports a
  weakness the first pass already reported under a neighbouring CWE id
  (`CWE-330` for `CWE-338`, `CWE-259` for `CWE-798`). That is one weakness on
  one line, and a consumer that merged by `file::line` instead of
  `file::line::cwe` would show one comment. The catalogue carries both ids on
  purpose, so this is not a defect in the pipeline — it is a decision the
  consumer can make.

Nothing was published from this experiment: the shipped spec keeps the
current second-pass prompt.

## The severity floor, measured on the current pipeline (3.3.0)

Three runs over the same diff, one per floor, same ground truth:

| Floor | deep_review | gap_review | Dropped by the stage | Planted found | Missed |
|-------|-------------|------------|----------------------|----------------|--------|
| `high` | 8 | 3 | 2 | **11 / 11** | — |
| `critical` | 8 | 3 | 0 | **11 / 11** | — |
| `low` | 8 | 0 | 8 | **8 / 11** | open redirect, prototype pollution, weak crypto |

**The floor is a hint to the model, not a filter.** The stage prompt says
"drop findings below the severity floor rather than shrinking the JSON", and
the model puts what it dropped into a separate `rejected` array. Nothing
filters afterwards, so what survives is the model's judgement of its own
ratings — and its judgements move between runs.

Three consequences, all measured above:

- **The sets are not nested.** A higher floor is not a subset of a lower one.
  The severity is the model's own rating, and it moves from run to run.
- **Raising the floor does not reliably shrink the output.** At `high` and at
  `critical` the audit still reported all eleven planted weaknesses; the floor
  dropped nothing real.
- **Lowering the floor can lose real weaknesses.** At `low` the audit dropped
  the open redirect, the prototype pollution and the weak crypto, and the
  second pass then found nothing to replace them. The same happened on the
  single-pass pipeline: at `low` it dropped the hardcoded password and the SQL
  injection while adding findings nothing planted.

So `medium` — the default — stays the default: it is the only floor that lost
nothing in any run, on either version of the pipeline.

## What would move the numbers

- **Review per file instead of per diff.** The model spends its findings on a
  diff of any size; two files reviewed separately would each get their own
  budget. This is a change to the pipeline, not to the workflow.
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

## Two rules of the instrument

**Everything written about the measurement lives on `main`, not on the pull
request's branch.** The workflow computes the diff as `main...branch`, so a
report about the runs would be part of what gets reviewed — one run at 3.3.0
"found" five of eleven because it was reading the report instead of the code.

**A re-run updates the comments it already posted instead of creating new
ones.** Measuring one run therefore means filtering on the last touch of a
comment, not on the date it was created (`tools/measure.py --since`).

## Reproducing it

```bash
python3 tools/ground_truth.py     # regenerate the ground truth from the markers
python3 tools/measure.py 1        # measure the pull request
node tools/probe.mjs              # run the pipeline locally, no pull request
```

`probe.mjs` runs the audit on this repository's own diff and prints the same
count without waiting for CI. It needs the pipeline runtime built somewhere and
`MINIMAX_API_KEY` in the environment; `PIPELINE_RUNTIME` points it at the
runtime.

`measure.py` reads the comments the review posted and compares them with
`.github/ground-truth.json`. `--since <ISO timestamp>` measures one run; a
pull request accumulates the comments of every run, and the union of two
runs answers a different question than either of them does.
