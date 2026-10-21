# ai-review-fixture

A repository with **known** vulnerabilities, used to measure what the review
actually finds.

Everything else we have measured so far answers "did the review break?". This
repository answers the question that matters: **does it find what it must
find?**

## How it works

`main` holds the clean tree. The branch `feature/insecure-orders-api` adds an
orders service that contains eleven deliberate vulnerabilities — five in Python,
six in TypeScript. Each one is listed in [`GROUND_TRUTH.md`](GROUND_TRUTH.md)
with its CWE and the line it sits on, and the same list is machine-readable in
[`.github/ground-truth.json`](.github/ground-truth.json).

The pull request is the test. The review runs on the diff, and the findings are
compared with the ground truth:

- **found** — the review named the same weakness class on the same file
- **missed** — the vulnerability is in the diff and no finding covers it
- **invented** — a finding that no planted vulnerability accounts for

One of the eleven is outside the published catalogue: prototype pollution
(`CWE-1321`) is not in the 268 entries the model may choose from, so the
review may report the issue and still have no id to give it. That is the
closed set working as designed, and it is in the ground truth so the result
is read honestly.

The workflow is the one a consumer would write: ten lines, a reusable workflow
call, one secret.

## What a miss means

A miss is not automatically a defect in the review — a planted weakness can be
too subtle to be worth a reviewer's time, and the pipeline has a severity
floor. But a miss that repeats across runs is a real limit, and the only way
to know which it is, is to keep the ground truth honest and run the same pull
request again.

Two limits are worth naming before the first result is read:

- The audit reports **at most 8 findings**. A diff with eleven planted weaknesses
  cannot show all of them, and the pipeline does not say that it stopped.
- The catalogue the model chooses from is a **dated subset** of MITRE's list
  (268 entries, snapshot 2026-10-21). A weakness class outside it has no id to
  cite, and the review says `null` rather than inventing one.

## Results

Six runs over the same diff are written up in [`RESULTS.md`](RESULTS.md). The
short version: every run found **eight of the eleven** planted weaknesses,
no run invented anything at the default severity floor, and *which* eight
changed every time — the union across runs covers all eleven.

## Running it

The review needs `MINIMAX_API_KEY` as a repository secret. The pipelines
themselves are free to download, so the identity the workflow mints needs no
funds.
