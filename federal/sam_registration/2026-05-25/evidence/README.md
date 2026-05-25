# Evidence Trail · Caballerz Network LLC SAM Registration · 2026-05-25

> Drop the source documents here. Hash them. Anchor the manifest on DefendableLedger.

## Files to preserve in this folder

Save each as the operator captures it. File names are conventional · adjust the actual filenames to match what was downloaded as long as the purpose is clear.

| target filename | purpose | source action |
| --- | --- | --- |
| `sam_submission_confirmation.pdf` | SAM.gov submission confirmation page (PDF or screenshot) | screenshot or save-as-PDF from SAM.gov after submitting |
| `sam_uei_assignment.pdf` | UEI assignment download | download from SAM.gov Entity dashboard |
| `confirmation_email_buildatswarmandbeeai.eml` | confirmation email full source | save the email from build@swarmandbee.ai as EML |
| `florida_sunbiz_llc_filing.pdf` | Florida Sunbiz LLC formation filing | download from sunbiz.org Caballerz Network LLC entity page |
| `florida_annual_report.pdf` | Florida annual report (most recent) | download from sunbiz.org |
| `mercury_or_choice_bank_verification.pdf` | bank verification letter (Mercury / Choice) | request from bank dashboard or save the confirmation email |
| `florida_swarm_and_bee_dba.pdf` | Florida DBA registration for "Swarm & Bee" | download from sunbiz.org fictitious-name registry |

## After all files are saved · hash + anchor

From this directory (`~/Desktop/defendableos/federal/sam_registration/2026-05-25/`):

```bash
cd ~/Desktop/defendableos/federal/sam_registration/2026-05-25
sha256sum evidence/* | tee SHA256SUMS.txt
```

This generates the canonical hash manifest. Every file in `evidence/` will have its sha256 recorded.

Then for the DefendableLedger anchor record (when ready to publish):

```bash
# generate manifest JSON
python3 - <<'PY'
import hashlib, json, pathlib
e = pathlib.Path("evidence")
manifest = {
  "record_type": "REG-SAM-CABALLERZ-2026-05-25",
  "legal_entity": "CABALLERZ NETWORK LLC",
  "registration_status": "submitted",
  "submitted_at": "2026-05-25",
  "evidence_files": [
    {"file": str(f.relative_to(e.parent)),
     "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
     "size_bytes": f.stat().st_size}
    for f in sorted(e.iterdir()) if f.is_file() and f.name != "README.md"
  ],
  "doctrine": "Tribunal begins before training; no proof, no honey."
}
pathlib.Path("registration_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
print("registration_manifest.json written")
PY
```

## Privacy treatment

- These documents contain real identifiers (UEI, address, bank details, etc.)
- **Do NOT push the `evidence/` folder to a public GitHub repo**
- The local-audit-snapshots pattern applies: receipts stay local; published surfaces reference only the hash manifest

When committing the SAM registration folder to git, **exclude `evidence/*` (everything except this README) via `.gitignore`**.

Suggested `.gitignore` addition (in defendableos repo root):

```gitignore
# Federal SAM registration evidence · LOCAL ONLY
federal/sam_registration/*/evidence/*
!federal/sam_registration/*/evidence/README.md
!federal/sam_registration/*/evidence/.gitkeep
```

## Status check (operator: tick when done)

- [ ] SAM submission confirmation PDF saved
- [ ] UEI confirmation PDF saved
- [ ] Confirmation email saved as EML
- [ ] Sunbiz LLC filing PDF saved
- [ ] Sunbiz annual report PDF saved
- [ ] Bank verification PDF saved
- [ ] Florida DBA registration PDF saved
- [ ] `sha256sum evidence/* > SHA256SUMS.txt` run
- [ ] `registration_manifest.json` generated
- [ ] Anchored on DefendableLedger
- [ ] Federal corpus v0.3 update commit prepared

---

`Books and records · evidence first · receipts compound. To the shed.` 🐝🇺🇸
