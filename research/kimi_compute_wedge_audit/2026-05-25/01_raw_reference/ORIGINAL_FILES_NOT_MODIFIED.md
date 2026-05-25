# Original Files Not Modified

> Per audit doctrine, the original Kimi compute-wedge package is never modified.
> Hashes recorded here are the canonical source-of-truth references for the audit.

## Original package locations · sha256 anchored

| file | path | size | sha256 |
| --- | --- | ---: | --- |
| Compute Wedge mission zip | `/home/swarm/Kimi_Agent_DefendableOS Compute Wedge Mission.zip` | 916,056 | `da0ae8df4ca820f838ba54bff3b202460db948d0809ae767c918025c9536512f` |
| Final report (markdown · standalone) | `/home/swarm/defendableos.agent.final.md` | 260,560 | `8977e76f170cd2eb6508e9d6b177d5ed28f205fe1b7a2826dfd796ac9bb7d5c1` |
| Final report (docx · standalone) | `/home/swarm/DefendableOS_Compute_Wedge_Report.docx` | 1,115,976 | `44785fa829011420945218e8219e63937933a74116663fd97d54804f93903f8f` |

## Working unpack location (read-only reference)

The zip was unpacked earlier in this session into `/tmp/kimi-compute-wedge/` containing 32 member files. This audit does **not** modify any of those files — they are referenced via absolute path and re-hashed if used.

## Access policy

- The Kimi package shall be **read** via `python3 zipfile` or `cat` only.
- No extraction shall write to source directories.
- The `02_claim_audit/` and `03_market_audit/` workspaces hold **derived** structured records (JSONL / CSV) that quote sources; they do not relocate or rewrite source files.
- The cross-references in this audit point at **absolute source paths** so a future auditor can re-verify any claim against the original file.

## Confirmation

- ✅ Zip not modified
- ✅ Standalone markdown not modified
- ✅ Standalone docx not modified
- ✅ Prior intake workspace `research/kimi_intake/2026-05-25/` not modified
- ✅ Prior product workspace `products/defendable_compute_proof_receipt/v0.1/` not modified
- ✅ Prior SAM workspace `federal/sam_registration/2026-05-25/` not modified (memo may be appended in Phase 13)

`No proof, no honey. Originals preserved.`
