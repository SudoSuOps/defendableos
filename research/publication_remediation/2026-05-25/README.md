# Publication Remediation · 2026-05-25

> Public-correction pass over the repositories pushed 2026-05-25. **Not** new product
> development. Scope: research-status accuracy, federal-registration status, legal-entity /
> DBA identity, claim-boundary discipline, and source-document publication safety.

## Public repositories examined

| repo | remote | role | action |
| --- | --- | --- | --- |
| `defendable-compute-wedge` | github.com/SudoSuOps/defendable-compute-wedge | Compute Wedge research corpus | claims downgraded · DOCX removed · entity wording corrected · **pushed** |
| `defendableos` (`federal/sam_registration/2026-05-25/` + root `README.md`) | github.com/SudoSuOps/defendableos | federal registration publication | entity wording corrected · claim boundaries added · D-U-N-S removed · **pushed** |

## What was wrong, in one paragraph

The Compute Wedge package presented Kimi-derived external market claims (market sizes,
pricing premiums, funding/valuation, share, rental tightness, and a "no competitor combines
all five layers" claim) as cross-verified **HONEY** before the required independent
source-promotion audit was completed. The federal materials described the operation in terms
that over-reached the actual posture (submitted-not-active SAM registration), conflated the
two LLCs, asserted prime/DoD bid-eligibility not yet established, and published a D-U-N-S
identifier that was unnecessary in the federal context.

## What this pass did

1. **Compute Wedge claims** → relabeled the package *Research Corpus · Source-Promotion Audit
   Pending*; downgraded external market claims to RESEARCH-SUPPORTED / VERIFICATION PENDING /
   JELLY; reserved DIRECT_EVIDENCE for smash-rig operational proof; rewrote the competitor
   claim; **preserved** the product recommendation and **preserved** the underlying research.
2. **Federal identity** → CABALLERZ NETWORK LLC = legal federal-facing entity; Swarm & Bee =
   operating brand / DBA; SAM described as submitted/activation-pending; CAGE pending; no award
   claimed; eligibility statements bounded to post-activation + per-solicitation confirmation;
   D-U-N-S removed from the federal folder and the root README footer.
3. **Sensitive-data scan** → tree + full git history of both repos. **No** UEI, EIN, bank
   routing/account, SSN, or residential-address values found in any tracked file or any commit.
   The `evidence/` folder never held real documents (only `.gitkeep` + placeholder README).
4. **Source DOCX** → removed from the public Compute Wedge tree (republication rights
   unaudited); hashes preserved; local archival copies retained outside the repo.
5. **Running shells** → only this authorized session was found writing to the repos.

## Files in this receipt

| file | purpose |
| --- | --- |
| `README.md` | this index |
| `public_claims_patch_log.md` | Compute Wedge claim downgrades, line by line |
| `federal_identity_patch_log.md` | federal entity / claim-boundary corrections |
| `sensitive_file_scan_report.md` | tree + git-history sensitive-exposure scan result |
| `source_docx_rights_review.md` | DOCX origin, rights conclusion, disposition |
| `running_shells_review.md` | process inspection findings |
| `SHA256SUMS.txt` | sha256 of every file in this receipt |
| `remediation_manifest.json` | machine-readable summary + commit references |

## Result

- Compute Wedge corrective commit: `78bd10b` — **pushed** to `main`
- DefendableOS corrective commit: this commit (see `git log`) — **pushed** to `main`
- No sensitive banking / TIN / UEI / address values were printed in the remediation report or
  committed to either repo.

`Tribunal begins before training. No proof, no honey. Correct the record. To the shed.` 🐝
