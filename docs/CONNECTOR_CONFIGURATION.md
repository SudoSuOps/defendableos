# Connector Configuration · honest provider status

Every connector reports a single ProviderStatus enum based on real
config + kill switches. `READY` is reserved for connectors where:

1. Credentials are present in the environment.
2. Live calls are explicitly enabled (`*_LIVE_CALLS_ENABLED=true`).
3. The global gate is open (`LIVE_PROVIDER_CALLS_ENABLED=true`).
4. The connector's terms_review_status permits the use.

If ANY of those fail, the status is honest about which one:

```
NOT_CONFIGURED        no credentials
CONFIGURED_DISABLED   credentials present, kill switch off
READY                 all conditions met
ERROR                 credentials present but a precondition fails (e.g. eBay
                      production env without production_access_confirmed)
FUTURE_DISABLED       connector reserved for a future capability
```

The admin `/api/v1/admin/goods/connectors` endpoint reads from
`app/services/connector_registry.py` which derives the status from
config at call time. **The status is never cached.** It always
reflects the live config.

## The 7 connectors

### `BRAVE_LLM_CONTEXT`
Purpose: trend discovery context · never a comp.
```
BRAVE_API_KEY=                       (required for READY)
BRAVE_LIVE_CALLS_ENABLED=false       (kill switch)
LIVE_PROVIDER_CALLS_ENABLED=false    (global gate)
BRAVE_MAX_CALLS_PER_RUN=1
BRAVE_MAX_CONTEXT_TOKENS=6000
BRAVE_CONTEXT_THRESHOLD_MODE=strict
BRAVE_DISCOVERY_ENABLED=false        (admin flag)
```
Terms: `REVIEWED_INTERNAL_RESEARCH_ONLY`.

### `EBAY_BROWSE`
Purpose: public active listing observations · asking-market context only.
```
EBAY_APP_ID=                              (required)
EBAY_CERT_ID=                             (required)
EBAY_DEV_ID=
EBAY_ENVIRONMENT=production|sandbox
EBAY_MARKETPLACE_ID=EBAY_US
EBAY_BROWSE_LIVE_CALLS_ENABLED=false      (kill switch)
EBAY_MAX_CALLS_PER_RUN=1
EBAY_PRODUCTION_ACCESS_CONFIRMED=false    (founder attestation)
LIVE_PROVIDER_CALLS_ENABLED=false         (global gate)
```
Terms: `REVIEWED_INTERNAL_RESEARCH_ONLY`.

Note: `EBAY_ENVIRONMENT=production` AND
`EBAY_PRODUCTION_ACCESS_CONFIRMED=false` resolves to `ERROR`, not
silent sandbox fallback.

### `EBAY_INVENTORY`
Purpose: future outbound eBay listing publication.
Status: `FUTURE_DISABLED` always.
```
EBAY_OUTBOUND_LISTING_ENABLED=false   (stays false)
```

### `SHOPIFY_FUTURE`
Status: `FUTURE_DISABLED` always until a future feature lane.

### `CLIENT_UPLOAD`
Purpose: client-provided evidence intake.
Status: `READY` (the upload endpoint is the connector).
Terms: `REVIEWED_INTERNAL_RESEARCH_ONLY` for the intake itself ·
client evidence is `PRIVATE_BY_DEFAULT`.

### `FIRST_PARTY_TRANSACTION`
Purpose: founder-owned transaction evidence.
Status: `READY`.
Terms: `TERMS_REVIEW_PENDING` · manual approval required before
any transaction becomes Grade A/B comp evidence.

### `LICENSED_TRANSACTION_DATA_FUTURE`
Status: `FUTURE_DISABLED` until terms are reviewed and approved.

## How to enable Brave (founder, local only)

```bash
# 1. Set the key (already in ~/Desktop/defendableos/.env locally)
export BRAVE_API_KEY=...

# 2. Open the kill switches
export BRAVE_LIVE_CALLS_ENABLED=true
export LIVE_PROVIDER_CALLS_ENABLED=true
export BRAVE_DISCOVERY_ENABLED=true

# 3. Trigger ONE controlled discovery run via the admin endpoint
#    (DO NOT schedule recurring calls in this turn)
```

The admin endpoint:
1. Reads the kill switches.
2. Creates a DiscoveryRun row.
3. Calls Brave ONCE (capped by BRAVE_MAX_CALLS_PER_RUN).
4. Writes the raw response to `MARKET_OBSERVATIONS` bucket.
5. Hashes raw + normalized output.
6. Creates `TrendSignal` rows · ALL graded E · ALL marked NOT_A_COMP.
7. Writes an `AuditEvent`.

## How to enable eBay Browse (founder, local only)

```bash
export EBAY_APP_ID=...
export EBAY_CERT_ID=...
export EBAY_ENVIRONMENT=production
export EBAY_PRODUCTION_ACCESS_CONFIRMED=true   # attestation
export EBAY_BROWSE_LIVE_CALLS_ENABLED=true
export LIVE_PROVIDER_CALLS_ENABLED=true
```

The admin endpoint then:
1. Creates a DiscoveryRun with `run_type=ACTIVE_LISTING_SEARCH`.
2. Calls eBay Browse ONCE.
3. Writes the raw response to `MARKET_OBSERVATIONS`.
4. Normalizes each listing into a `MarketObservation` with:
   - `source_type = PUBLIC_ACTIVE_LISTING`
   - `transaction_confirmed = false`
   - `price_type = ASKING_PRICE`
   - `comp_quality_grade = C or D`
   - `limitations` includes the canonical 4 strings
5. Writes an AuditEvent.

The platform does NOT publish outbound eBay listings in this
turn. `EBAY_OUTBOUND_LISTING_ENABLED` stays false until a
separate inventory connector ships with founder approval.

## Security

- API keys are read from `os.environ` at process start · they
  never appear in `/healthz` JSON, never appear in audit-event
  payloads, never appear in admin UI.
- The connector-status response shows only the derived enum ·
  never the underlying key.
- Logs do not include request bodies for connector calls (rate
  limit messages and HTTP status only).
- See `[[feedback-keys-authoritative-on-zima]]` for the operator's
  key storage policy.
