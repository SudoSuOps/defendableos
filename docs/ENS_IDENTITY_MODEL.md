# ENS Identity Model · `defendable.eth`

## Why ENS?

ENS is the public identity and proof rail for DefendableOS. It is **not** a private database. The pattern is:

> An ENS subname is the stable public handle a deed (or organization, asset, edge box) can be referenced by. Public text records carry only hashes and a public verification URL. Confidential evidence stays server-side.

## Naming hierarchy

```
                  defendable.eth                           ← parent (owned by Swarm and Bee LLC)
                       │
       ┌───────────────┼───────────────────┐
       │               │                   │
  swarmbee.…      acmecorp.…           …                    ← {organization_slug}.defendable.eth
       │
       ├──────────────────────────┬──────────────────────────┐
       │                          │                          │
 box-01.swarmbee.…   ddeed-compute-000001.swarmbee.…   asset-dov-compute-000001.swarmbee.…
       (EDGE_NODE)         (DEED)                       (ASSET, optional)
```

| Identity type | Naming pattern | Example |
|---|---|---|
| Organization | `{org_slug}.defendable.eth` | `swarmbee.defendable.eth` |
| Edge node | `{node_slug}.{org_slug}.defendable.eth` | `box-01.swarmbee.defendable.eth` |
| Defendable Deed | `ddeed-{asset_slug}.{org_slug}.defendable.eth` | `ddeed-dov-compute-000001.swarmbee.defendable.eth` |
| Asset (optional) | `asset-{asset_slug}.{org_slug}.defendable.eth` | `asset-dov-compute-000001.swarmbee.defendable.eth` |

## Naming safety

`services/ens.py:normalise_label` enforces:
- Lowercase ASCII, dashes only
- No leading/trailing/double dashes
- Blocked labels: `admin · api · app · auth · login · support · verify · root · registry · resolver · system · www`
- ENS label syntax (`/[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?/`)
- Collision detection against `ens_identities.ens_name`

## Public records

Proposed text records for a **deed identity**:

```json
{
  "com.defendable.type": "DEFENDABLE_DEED",
  "com.defendable.version": "0.1",
  "com.defendable.status": "PUBLIC_VERIFICATION_AVAILABLE",
  "com.defendable.verify_url": "https://platform.defendableos.com/verify/<slug>",
  "com.defendable.record_hash": "<record_hash>",
  "com.defendable.manifest_hash": "<manifest_sha256>",
  "com.defendable.validator_receipt_hash": "<receipt_sha256>"
}
```

What text records **never** contain: serial numbers, purchase costs, private filenames, uploaded raw text, AIOV narrative, personally identifying information.

## Adapter strategy

`services/ens.py` exposes a tiny interface (`ENSAdapter`) with three implementations:

| Adapter | `mode` | Purpose | MVP status |
|---|---|---|---|
| `MockENSAdapter` | `MOCK` | Reserves names in the DB only. No chain access. Default. | ✓ implemented |
| `OffchainCCIPAdapter` | `OFFCHAIN_CCIP` | Future: gasless wildcard resolution via CCIP-Read gateway. | reservation only |
| `OnchainWrappedSubnameAdapter` | `ONCHAIN_WRAPPED` | Future: NameWrapper subname mint. | admin-only stub |

## Live-write safety controls

1. `ENS_MODE=mock` by default — selected automatically when no other mode is configured.
2. `ENS_LIVE_WRITES_ENABLED=false` by default — even when an onchain adapter is selected, it refuses to sign.
3. `ENS_SIGNER_PRIVATE_KEY` is **never** required in mock mode and **never** returned by an API.
4. `OnchainWrappedSubnameAdapter.issue` checks both `ens_live_writes_enabled` and the presence of a signer key before raising `NotImplementedError` (it is intentionally not wired to a real signer yet).
5. UI does not surface a signer key field anywhere.

## Choosing offchain vs onchain later

- **Offchain CCIP-Read** is the right path when:
  - Reservations scale into thousands per organization
  - Identities need to resolve in regular wallets but don't need transferability
  - Cost-per-issuance must be near-zero
- **Onchain wrapped subnames** are the right path when:
  - The identity itself needs to be transferable or owned by another wallet
  - The deed identity needs to survive without DefendableOS infrastructure
  - Cross-Swarm portability becomes a customer ask

Triggers to revisit: Whitelabel customer requests, >10 paying customers, cross-Swarm portability play, defendable.eth deed cross-references.
