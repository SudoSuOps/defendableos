# Raw Kimi drops · referenced not copied

> Per intake doctrine, large original files are referenced via absolute path + SHA256,
> never copied into the workspace. Extraction reads through `zipfile` and `git`
> directly on the originals.

## Canonical drop paths

| # | path | size | sha256 |
| ---: | --- | ---: | --- |
| 1 | `/home/swarm/Kimi_Agent_Defendable Swarm Research Repo.zip` | 2.7M | `6cad81cbdf0471d6a5dc46abfd7fd2648fe735d408229182c529157976c07bd5` |
| 2 | `/home/swarm/Kimi_Agent_Defendable Swarm Research Repo (1).zip` | 3.7M | `197dd1f34c957f41dbb247cdaeeb8df5433a3b39c70fbbd5f9c4ccea0b8db37b` |
| 3 | `/home/swarm/Kimi_Agent_Defendable Swarm Research Repo (2).zip` | 4.3M | `dfa8a03b64a3abb7b7263cc02f393dfc099fd58f24a3c049ccb3da67139134ca` |
| 4 | `/home/swarm/Kimi_Agent_Defendable Swarm Research Repo (3).zip` | 4.7M | `4b5fcbef6745ea4ab2a411d6ed1ba0bfa7e043df85676d83b0144fb8e65e4481` |
| 5 | `/home/swarm/Kimi_Agent_Defendable sam.zip` | 3.7M | `197dd1f34c957f41dbb247cdaeeb8df5433a3b39c70fbbd5f9c4ccea0b8db37b` |

**Note:** Drop #5 (`sam.zip`) is byte-identical to Drop #2 (`Repo (1).zip`) per sha256. Four unique drops, not five.

## Downstream repos containing the published portions of these drops

- swarm-research: https://github.com/SudoSuOps/defendableos-swarm-research
  - main · v0.1 corpus (13 deliverables)
  - remediation/corpus-v0.2-source-receipts · v0.2 audited corpus (commit 260e541)
- federal corpus: https://github.com/SudoSuOps/DEFENDABLEOS-FEDERAL-DEMAND-INTELLIGENCE-SWARM
  - main · v0.1 federal corpus
  - remediation/federal-corpus-v0.2-source-receipts · v0.2 audited + SMALL_CONTRACT_OPPORTUNITIES.md

## Access policy

- Drops MUST be read in place via Python `zipfile` or `git show`.
- Drops MUST NOT be re-unpacked to /tmp or any working directory.
- If a specific drop member needs to be copied locally, that copy belongs to `02_extractions/` with full provenance.
