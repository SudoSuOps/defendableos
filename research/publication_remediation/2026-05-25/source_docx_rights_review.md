# Source DOCX Rights / License Review

Repo: `defendable-compute-wedge` · path (pre-removal): `deliverables/source_docx/`

## The three files identified

| filename | size (bytes) | sha256 (preserved) | distinct? |
| --- | ---: | --- | --- |
| `DefendableOS_Compute_Wedge_Report.docx` | 1,115,976 | `44785fa829011420945218e8219e63937933a74116663fd97d54804f93903f8f` | A |
| `defendableos.agent.final.footnote.docx` | 1,115,976 | `44785fa829011420945218e8219e63937933a74116663fd97d54804f93903f8f` | A (byte-identical to Report) |
| `defendableos.agent.final.base.docx` | 130,504 | `cb95f20e6db906ef6aea8c58ba244797f6e963d13d717bbf0c4590efe5de1d15` | B |

So three files, **two distinct artifacts** (Report == footnote; base differs).

## Origin & ownership

The filenames (`defendableos.agent.final.*`) and content indicate these are **model-generated
report drafts** produced by the Kimi research agent for the Compute Wedge mission — i.e., outputs
of a third-party model (Moonshot/Kimi) over a Swarm-commissioned prompt. The derived **Markdown**
analysis Swarm authored from them is Swarm's to publish; the **raw DOCX model outputs** are drafts
whose republication rights and provenance were **not audited** before publication (the same
source-promotion audit gap that affects the market claims).

## Conclusion

Ownership/republication permission for the raw DOCX is **not clearly established**. Per mission D2,
the conservative action is to remove them from the public tree while preserving the audit trail.

## Disposition (done)

1. **Removed** all three DOCX from the public Compute Wedge tree (`git rm`, in commit `78bd10b`).
2. **Hashes preserved** in `receipts/SHA256SUMS.txt` (unchanged) and in the local archive manifest.
3. **Local archival copies retained** outside any repository at
   `~/Desktop/_private_audit_archive/compute-wedge-source-docx-2026-05-25/` with its own
   `SHA256SUMS.txt`.
4. **README note added** to the Compute Wedge repo:
   *"Source documents retained privately for audit; public corpus contains derived research
   artifacts only."*
5. **License narrowed**: CC-BY-4.0 now applies only to Swarm-authored original/derived artifacts
   (Markdown analysis, extractions, audit notes) that Swarm has the right to publish — not to any
   third-party source material.

## If rights are later confirmed

If a source-promotion audit establishes Swarm's republication rights over the DOCX (e.g., the
Kimi/Moonshot terms grant output ownership to the operator), the files can be restored from the
local archive — the preserved hashes prove they are unchanged.
