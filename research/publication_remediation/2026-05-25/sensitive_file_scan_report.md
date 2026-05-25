# Sensitive File Scan Report · 2026-05-25

Scope: current tracked tree **and full git history** of both public repositories.
No sensitive values are reproduced in this report.

## Method

- `git log --all --diff-filter=A --name-only` to enumerate every file ever added (history scan)
- Pattern scans over tracked text for: EIN (`NN-NNNNNNN`), 9-digit numbers (DUNS/routing/account),
  12-char UEI format, and keywords (`routing`/`account`/`aba`/`iban`/`swift`/`ssn`/`ein`/`bank`)
- Street-address heuristic (number + St/Ave/Rd/Dr/Blvd/Ln/Ct/Way) over the federal folder
- Binary/document enumeration (`.pdf`/`.eml`/`.png`/`.jpg`/`.docx`/`.xlsx`/`.csv`/`.key`/`.pem`)

## Result — were sensitive artifacts EVER committed?

**No.** Neither repository's current tree nor any commit in history contains:

| artifact | tree | history | notes |
| --- | --- | --- | --- |
| Full UEI value | absent | absent | referenced as "assigned (see evidence/)"; value never committed |
| EIN | absent | absent | zero matches to EIN pattern |
| Residential address | absent | absent | no street-address match in federal folder |
| Bank verification letter | absent | absent | only a *filename* in a local-only checklist |
| Bank routing/account | absent | absent | no routing/account literals |
| SAM screenshots / confirmation PDFs | absent | absent | `evidence/` only ever held `.gitkeep` + README |
| Confirmation email (.eml) | absent | absent | filename only, in local-only checklist |
| DBA PDF w/ personal data | absent | absent | filename only, in local-only checklist |
| Secrets / API keys / tokens | absent | absent | `.env` is gitignored and untracked |

### The one real identifier found (now removed)

A **D-U-N-S business number** appeared in tracked text — `federal/.../entity_relationship.md`,
`federal/.../REGISTRATION_RECEIPT.md`, and the root `README.md` trademark footer. D-U-N-S is a
business identifier (not in the do-not-publish set of UEI/EIN/bank/address) and the same value is
**already self-published by the operator** on their live `security.txt` / `llms.txt`. It has been
removed from the federal folder and the root README footer per mission B3 (unnecessary reference).
The value is not reproduced here.

## evidence/ folder posture — confirmed safe

- Across all of history the folder contained only `.gitkeep` and a placeholder `README.md`.
- `.gitignore` already enforces `federal/sam_registration/*/evidence/*` (allowing only README/.gitkeep).
- The public evidence folder therefore contains **only redacted/public-safe references** — no source documents.

## .env

`.env` exists locally in the defendableos working directory but is **gitignored and untracked**
(confirmed: `git ls-files .env` returns nothing; `.gitignore` lines for `.env*`). Not in history.

## Conclusion

No history purge or credential rotation is required for sensitive-document exposure — none was
ever committed. The publication workflow does **not** need to be halted on exposure grounds. The
only edit warranted was removing the D-U-N-S text reference (done). Recommend the operator keep
the existing `.gitignore` evidence rule and continue the local-only receipts pattern.
