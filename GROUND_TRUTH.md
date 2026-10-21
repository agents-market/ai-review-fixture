# Ground truth

Ten deliberate vulnerabilities. The line numbers come from the markers in
the code (`tools/ground_truth.py`), so they cannot drift.

| # | CWE | File | Line | What it is |
|---|---|---|---|---|
| 1 | `CWE-79` | `src/api.ts` | 15 | Comment body written into innerHTML |
| 2 | `CWE-918` | `src/api.ts` | 21 | Preview fetches whatever URL the caller sends |
| 3 | `CWE-338` | `src/api.ts` | 29 | Password reset token from Math.random |
| 4 | `CWE-601` | `src/api.ts` | 36 | Redirect target taken from the query string |
| 5 | `CWE-1321` | `src/api.ts` | 42 | Request body merged into the settings object |
| 6 | `CWE-1333` | `src/api.ts` | 50 | Email pattern with nested quantifiers |
| 7 | `CWE-798` | `src/orders.py` | 14 | Database password written into the source |
| 8 | `CWE-89` | `src/orders.py` | 25 | Order id pasted into the SQL statement |
| 9 | `CWE-78` | `src/orders.py` | 32 | Archive name reaches the shell |
| 10 | `CWE-22` | `src/orders.py` | 39 | Upload name decides which file is read |
| 11 | `CWE-502` | `src/orders.py` | 47 | Session cookie deserialized with pickle |

Regenerate with `python3 tools/ground_truth.py`.
