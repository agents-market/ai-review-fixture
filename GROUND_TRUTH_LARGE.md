# Ground truth

24 deliberate vulnerabilities. The line numbers come from the
markers in the code (`tools/ground_truth.py`), so they cannot drift; the
markers themselves are taken out of the diff before the review runs, so
the review does not read the answers.

| # | CWE | File | Line | What it is |
|---|---|---|---|---|
| 1 | `CWE-89` | `src-large/api/orders.ts` | 13 | The user id goes into the SQL as text |
| 2 | `CWE-1321` | `src-large/api/orders.ts` | 20 | The request body is merged into the order |
| 3 | `CWE-1333` | `src-large/api/orders.ts` | 29 | The email pattern has nested quantifiers |
| 4 | `CWE-434` | `src-large/api/uploads.ts` | 14 | Any kind of file is accepted |
| 5 | `CWE-22` | `src-large/api/uploads.ts` | 20 | The name of the document decides which file is read |
| 6 | `CWE-79` | `src-large/api/uploads.ts` | 26 | The document name is written into the page |
| 7 | `CWE-89` | `src-large/api/users.ts` | 12 | The profile id goes into the SQL as text |
| 8 | `CWE-79` | `src-large/api/users.ts` | 19 | The biography goes into the page as markup |
| 9 | `CWE-362` | `src-large/api/users.ts` | 27 | The check and the write are two separate operations |
| 10 | `CWE-918` | `src-large/api/webhooks.ts` | 14 | The webhook target is whatever the caller sent |
| 11 | `CWE-347` | `src-large/api/webhooks.ts` | 21 | The signature is accepted whatever it says |
| 12 | `CWE-798` | `src-large/auth/password.ts` | 8 | The signing key is written into the source |
| 13 | `CWE-327` | `src-large/auth/password.ts` | 12 | The payload is sealed with a cipher that is no longer safe |
| 14 | `CWE-338` | `src-large/auth/session.ts` | 9 | The session id comes from Math.random |
| 15 | `CWE-614` | `src-large/auth/session.ts` | 12 | The cookie is set without the Secure flag |
| 16 | `CWE-384` | `src-large/auth/session.ts` | 19 | The client sends the session id and it is taken as it is |
| 17 | `CWE-78` | `src-large/jobs/email.ts` | 9 | The recipient goes into the shell command |
| 18 | `CWE-209` | `src-large/jobs/email.ts` | 14 | The failure text carries the secret to the customer |
| 19 | `CWE-611` | `src-large/jobs/importer.py` | 10 | The parser resolves entities that point outside |
| 20 | `CWE-502` | `src-large/jobs/importer.py` | 16 | The settings blob is unpickled |
| 21 | `CWE-311` | `src-large/lib/crypto.ts` | 9 | The profile goes to disk as plain text |
| 22 | `CWE-601` | `src-large/web/admin.ts` | 12 | The redirect target comes from the query string |
| 23 | `CWE-639` | `src-large/web/admin.ts` | 17 | The user id in the path is the only key that is checked |
| 24 | `CWE-352` | `src-large/web/admin.ts` | 23 | The role change asks for no token |

Regenerate with `python3 tools/ground_truth.py`, check with
`python3 tools/ground_truth.py --verify`.
