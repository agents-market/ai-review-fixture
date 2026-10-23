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
*(Closed on 2026-10-23 — the catalogue grew to 269 entries and now carries
`CWE-1321`. See "The comment rule, measured" below.)*

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
  budget. This is a change to the pipeline, not to the workflow — and on a
  two-file fixture it cannot be shown to help.
- **A bigger fixture.** Eleven weaknesses in two files cannot show what a
  review does on a real pull request: the comment count, the noise, and the
  cost per file all need more than two files to mean anything.

## The comment rule, measured (2026-10-23)

The tables above count findings. What a reader sees is comments, and comments
were piling up: the same weakness came back on a neighbouring line — the
model's line for a weakness moves by 5 to 14 lines — the key was
`file::line`, and every re-run added a copy. On 2026-10-22 the pull request
carried **52 comments for 11 planted weaknesses**.

The rule now keys a comment by the weakness, not by the line: the CWE id for
the audit, the category tag for the style review. A new run closes the
comment that carried the same weakness and posts the fresh one.

Measured on the published `code-review-security-audit@3.4.0`, the same diff,
starting from a pull request with no comments at all:

| Run | Audit | Style | What the reader sees |
|-----|-------|-------|----------------------|
| 1, from clean | 10 posted, 10 live | 7 posted, 7 live | 10 of 11 planted, 0 invented |
| 2 | 11 posted, 10 replaced, **11 live** | 4 posted, 4 replaced, **7 live** | **11 of 11, 0 invented** |

**The count does not grow.** The second run replaced ten of the eleven
comments and added none; the style review replaced four and added none. The
live set is bounded by the weaknesses themselves, not by the number of runs.

Three bugs were found on the way, each visible only in the measurement:

- **A comment of another class hid the finding on its line.** The live set was
  keyed by `file::line`, so any comment standing there suppressed every
  finding on that line — the SSRF finding (`CWE-918`) was swallowed by a
  `CWE-330` comment that stood on its line. A line now holds a list of
  comments, and only a comment of the same class hides a finding.
- **Two ids for one weakness never merged.** The model called the weak
  password `CWE-259` in one run and `CWE-798` in another; the key changed and
  the old comment stood forever. A small map of known pairs now gives both ids
  one class. The id the reader sees is still the model's own.
- **The catalogue could not name prototype pollution.** `CWE-1321` was in the
  catalogue's scope list and was thrown out by the blocklist — the word
  `attribute` was there for other entries and dropped every weakness whose
  name ends in that word. Rebuilt from MITRE: 269 entries, snapshot
  2026-10-23, one id more.

**The reader now sees eleven comments for eleven weaknesses, and every one of
them is a planted weakness.** Nothing invented, and the two comments that used
to drift — `CWE-259`/`CWE-798` and `CWE-915`/`CWE-1321` — are one comment
each.

One run in six produced no usable review: the model returned prose instead
of the schema, twice, and the job went red — while the pull request kept the
standing review from the previous run. A failed run leaves the last good
review in place and takes no finding back.

## The answers were in the diff (2026-10-23)

The ground truth was written as comments in the code — `# VULN CWE-89: order
id pasted into the SQL statement` — and the review reads the diff. Every
number above was measured with the CWE id and a description of the weakness
one line above the weakness.

The markers can now be taken out of the code while the line numbers stay true
(`tools/ground_truth.py --strip`), and the truth can be checked against the
code afterwards (`--verify`, against the line of code it names). Both
fixtures are measured without their answers.

**On the small fixture, one run finds ten of the eleven and invents nothing.**
The one it missed is the hard-coded password: the model did not name it in
that run, and the comment from the previous run stays standing — a review
does not take a finding back because one run missed it. The union over two
runs is eleven of eleven.

So eleven of eleven was never true. It was eleven of eleven with the answers
in the diff.

## The larger change: ten files, twenty-four weaknesses

Two files are enough to measure the comment rule and not enough to measure a
review that has to cover a whole change. The second pull request is ten
files and twenty-four planted weaknesses, spread unevenly — three in one
file, one in another.

The ground truth lives on `main` and the code carries blank lines where the
markers were, so the answers are not in the diff.

### One review of the whole change

Four runs of the published `code-review-security-audit@3.4.0` over the whole
diff, the `medium` floor, same code:

| Run | Named by their own id | Comments | Model calls | Time |
|-----|----------------------|----------|-------------|------|
| 1 | 14 / 24 | 16 | 2 | 45s |
| 2 | 13 / 24 | 16 | 2 | 42s |
| 3 | 10 / 24 | 17 | 2 | 60s |
| 4 | 15 / 24 | 16 | 2 | 50s |

**Median 13.5 of 24 — 56%.** The CI run on the pull request (the consumer's
path, one run) found 9 of 24 by id. The spread between runs is five
weaknesses wide, which is what a shared budget does: which files get looked
at depends on the run.

### The same review, file by file

Three runs of the same pipeline over the same code, one diff per file:

| Run | Named by their own id | Comments | Model calls | Time |
|-----|----------------------|----------|-------------|------|
| 1 | 18 / 24 | 41 | 20 | 241s |
| 2 | 20 / 24 | 43 | 20 | 261s |
| 3 | 20 / 24 | 49 | 20 | 279s |

**Median 20 of 24 — 83%, and a spread of two instead of five.**

### What it costs, and where it comes from

The budget is the mechanism. The pipeline asks for at most eight findings per
pass and runs two passes, so **one review of a change cannot report more
than sixteen findings whatever the change's size** — and the measured
sixteen is exactly that. Ten files of a real change share one budget of
sixteen; reviewed one at a time, each file has its own.

- **Model calls: ten times as many.** Twenty against two. At the pipeline's
  notional rate (~$0.035 a review) a ten-file change costs ~$0.35 instead of
  ~$0.035. In local mode nothing is charged; the tokens are real either way.
- **Time: five times as long.** 261s against 50s, one file after another. A
  matrix would run the files in parallel and bring the wall time back to one
  review, at the price of ten runners.
- **Comments: two and a half times as many.** 43 against 16.

**The extra comments are mostly real.** Of the 21 comments in the first
file-by-file run that did not answer a planted weakness: 18 name weaknesses
that really are in the code and are not in the planted list — the fixture has
no authentication on most of its routes, and the review says so — and 3 are
planted weaknesses under another id (`CWE-326` for `CWE-327`, `CWE-526` for
`CWE-209`, `CWE-269` for `CWE-352`). None is invented.

### What this does not say

- The planted list is a subset. The fixture's code holds more weaknesses
  than the 24 marked, so "invented" cannot be measured here — only the small
  fixture, whose truth is exhaustive, can say that, and it says: nothing
  invented.
- The id is the model's judgement. The same weakness is named `CWE-209` by
  one run and `CWE-200` by another; the reader sees a comment either way, but
  a class keyed by the id can put two comments on one weakness.
- Ten files and twenty-four weaknesses are still a fixture, not a benchmark.

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
