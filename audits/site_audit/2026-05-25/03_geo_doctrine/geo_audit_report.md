# Generative Engine Optimization (GEO) Audit Report

**DefendableOS Ecosystem · 9 Brands · 2026-05-25**

## Executive Summary

The Defendable ecosystem demonstrates **above-average GEO maturity** for early 2026 standards, with strong positioning in the flagship domains (DefendableOS, Swarm & Bee, OpenDefendable) but **significant cross-brand consistency gaps** in smaller surfaces.

Three flagship domains (defendableos.com, swarmandbee.ai, opendefendable.com) publish comprehensive llms.txt files with explicit positioning, last-updated dates, and operator entity attestation — meeting the emerging convention for AI-crawler citability. However, six subsidiary domains (mrdefendable.com, defendableledger.com, painintheshed.com, offensetotheshed.com, defendablerouter.com, defendablecloud.com) publish minimal or no-entity llms.txt files that would fail a strict GEO audit.

**AI-bot policy is inconsistent across the stack**: three major domains explicitly allow 9-15 AI crawlers (defendableos, swarmandbee, full coverage); two products allow only 4 (defendablerouter, defendablecloud); and four cultural/media sites offer only implicit Allow:/. This mixed stance reduces the probability that LLMs cite all Defendable surfaces equally in context windows.

**Critical issue**: smaller sites reference phantom domains (chat.mrdefendable.com, defendabledocs.com, defendable-hq, ledger.mrdefendable.com) not present in the main brand stack, creating citation drift and LLM confusion about the true architecture.

---

## Per-Brand Summary Table

| Brand | llms.txt Size | Positioning | Operator Attested | AI-Bot Stance | Sitemaps | Citation Readiness |
|---|---|---|---|---|---|---|
| **defendableos.com** | 18.6 KB (374 L) | Clear "3rd-party defense layer" · tagline · deed pipeline | YES (D-U-N-S 138652395) | EXPLICIT: 12 bots + all major crawlers | 34 URLs w/ lastmod · llms.txt indexed | **STRONG** |
| **swarmandbee.ai** | 12.6 KB (175 L) | Clear "organic dataset bakery" · CCIR · founder voiced | YES (Donovan Mackey · D-U-N-S) | EXPLICIT: 15 bots (most comprehensive) | 35 URLs w/ lastmod · llms.txt indexed | **STRONG** |
| **opendefendable.com** | 2.6 KB (68 L) | Clear "open standards body" · 6 permanent principles | YES (D-U-N-S 138652395) | IMPLICIT Allow:/ only | 2 URLs w/ lastmod · llms.txt indexed | **GOOD** |
| **defendablerouter.com** | 4.8 KB (93 L) | Clear "drop-in middleware" · 3 modes · pricing | YES (D-U-N-S 138652395) | EXPLICIT: 4 bots (GPT/Claude/Perplexity/Google) | 8 URLs w/ lastmod · llms.txt NOT indexed | **FAIR** |
| **defendablecloud.com** | 4.7 KB (90 L) | Clear "operator-owned private inference" · 3-lane model | YES (D-U-N-S 138652395) | EXPLICIT: 4 bots (same 4 as router) | 7 URLs w/ lastmod · llms.txt NOT indexed | **FAIR** |
| **mrdefendable.com** | 1.9 KB (48 L) | WEAK: 4-domain stack claim · no operator entity | NO | IMPLICIT Allow:/ only | 11 URLs · NO lastmod · llms.txt not indexed | **POOR** |
| **defendableledger.com** | 1.6 KB (38 L) | MINIMAL: ledger + 5 tiers · no operator attestation | NO | IMPLICIT Allow:/ only | 3 URLs · NO lastmod · llms.txt not indexed | **POOR** |
| **painintheshed.com** | 1.5 KB (36 L) | Clear "cost-of-intelligence podcast" · 8 lanes | NO | IMPLICIT Allow:/ only | 6 URLs · NO lastmod · llms.txt not indexed | **FAIR** |
| **offensetotheshed.com** | 0.96 KB (27 L) | MINIMAL: 5 pillars only · no entity | NO | IMPLICIT Allow:/ only | 10 URLs · NO lastmod · llms.txt not indexed | **WEAK** |

---

## Cross-Brand Drift Findings

### Finding 1 · Sibling domain lists are fragmented

The ecosystem defines its brand architecture **three different ways**:

**DefendableOS llms.txt claims 6 surfaces:**
- defendableos.com (Institutional)
- defendtheclaw.com (Movement)
- defendablehack.com (Researcher)
- opendefendable.com (OSS standards)
- defendablerouter.com (AI gateway)
- defendablecloud.com (Hosted compute)

**OpenDefendable llms.txt claims 7 surfaces** (adds defendablecloud/router):
- defendableos.com + /opendefense subpage
- defendtheclaw.com
- defendablehack.com
- opendefendable.com
- defendablecloud.com ★ (added)
- defendablerouter.com ★ (added)

**MrDefendable llms.txt claims 4-domain "defense stack":**
- mrdefendable.com (FACE)
- defendableos.com (SYSTEM)
- offensetotheshed.com (CULTURE)
- painintheshed.com (MEDIA)

**PainInTheShed + OffenseToTheShed cross-reference 6-domain stack with phantom entries:**
- mrdefendable.com (FACE)
- defendableos.com (SYSTEM)
- ledger.mrdefendable.com (LEDGER) ← **NOT IN AUDIT CAPTURES**
- chat.mrdefendable.com (CHAT) ← **NOT IN AUDIT CAPTURES**
- offensetotheshed.com (CULTURE)
- painintheshed.com (MEDIA)
- defendabledocs.com (DOCS) ← **NOT IN AUDIT CAPTURES**

**Result:** LLMs asked "what's the full Defendable brand stack?" will receive conflicting answers. Citation consistency across models is reduced.

### Finding 2 · Operator entity attestation is inconsistent

**Well-attested (5/9 sites):**
- defendableos.com · swarmandbee.ai · opendefendable.com · defendablerouter.com · defendablecloud.com

**NOT attested (4/9 sites):**
- mrdefendable.com (references Donovan Mackey only in intro text; no D-U-N-S, no LLC)
- defendableledger.com (no entity reference in llms.txt)
- painintheshed.com (no entity reference; only cross-references to other sites)
- offensetotheshed.com (no entity reference; only cross-references)

### Finding 3 · AI-bot policy is stratified, not unified

| Tier 1 (Comprehensive) | Tier 2 (Minimal) | Tier 3 (Implicit) |
|---|---|---|
| defendableos: 12 bots explicitly allowed | defendablerouter: 4 bots | mrdefendable: default Allow:/ only |
| swarmandbee: 15 bots (most comprehensive) | defendablecloud: 4 bots | defendableledger: default Allow:/ only |
| | | painintheshed: default Allow:/ only |
| | | offensetotheshed: default Allow:/ only |
| | | opendefendable: default Allow:/ only |

**swarmandbee.ai allows the most crawlers (15):** GPTBot, ChatGPT-User, OAI-SearchBot, ClaudeBot, Claude-Web, anthropic-ai, PerplexityBot, Perplexity-User, Google-Extended, GoogleOther, Applebot, Applebot-Extended, Bingbot, Amazonbot, Bytespider, CCBot, cohere-ai, Mistral-AI, Meta-ExternalAgent, Meta-ExternalFetcher, YouBot, DuckAssistBot.

**defendablerouter + defendablecloud allow only 4:** GPTBot, ClaudeBot, PerplexityBot, Google-Extended.

### Finding 4 · Sitemap lastmod metadata is sparse

**With lastmod (supports LLM recency ranking):**
- defendableos, swarmandbee, defendablerouter, defendablecloud, opendefendable ✓

**Without lastmod:**
- mrdefendable, defendableledger, painintheshed, offensetotheshed ✗

### Finding 5 · llms.txt not indexed in most sitemaps

Only 3/9 sites reference their own llms.txt in sitemap.xml: defendableos, swarmandbee, opendefendable.

### Finding 6 · security.txt files missing (RFC 9116)

All captured "security.txt" files are actually HTML fallbacks, not RFC 9116 compliant. No security contact info published in the standard location.

---

## AI-Bot Policy Recommendation

Adopt **Option B (Transparent)** · copy swarmandbee's 15-bot allow list to all 9 domains, signaling "we welcome all major LLM crawlers."

This brings mrdefendable, defendableledger, painintheshed, offensetotheshed, defendablerouter, defendablecloud all to Tier 1.

---

## Top 10 GEO Improvements (Ranked by Impact)

### 1 · Add last-updated dates to all llms.txt files (CRITICAL)
- **Impact:** Enables LLMs to rank by recency; signals active maintenance
- **Effort:** 1-2 minutes per file
- **Current state:** Only 3/9 have dates
- **Action:** Add `# Last updated: YYYY-MM-DD` to 6 files

### 2 · Unify operator entity attestation in all llms.txt files (CRITICAL)
- **Impact:** Allows LLMs to confirm all sites are controlled by same org
- **Action:** Add to mrdefendable, defendableledger, painintheshed, offensetotheshed:
  ```
  ## Operator
  Swarm and Bee LLC · Florida · D-U-N-S 138652395 · DBA Swarm & Bee AI
  ```

### 3 · Consolidate brand stack definition (HIGH)
- **Impact:** Reduces citation drift across LLMs
- **Action:** Publish a canonical v0.1.0 stack definition in ALL 9 llms.txt files
- **Canonical proposal:**
  ```
  ## Brand stack (canonical v0.1.0)
  - defendableos.com         (Institutional product)
  - swarmandbee.ai           (Organic dataset bakery + firm)
  - opendefendable.com       (OSS standards body)
  - defendablerouter.com     (AI router product)
  - defendablecloud.com      (Hosted compute product)
  - mrdefendable.com         (Principal voice / operator persona)
  - offensetotheshed.com     (Culture + doctrine)
  - painintheshed.com        (Media / podcast)
  - defendtheclaw.com        (Movement / manifesto)
  - defendablehack.com       (Researcher / bounty)

  Legacy / not part of v0.1.0:
  - ledger.mrdefendable.com  (now defendableledger.com)
  - chat.mrdefendable.com    (deprecated)
  - defendabledocs.com       (consolidated into defendableos.com)
  ```

### 4 · Upgrade 4 product sites to Tier 1 AI-bot policy (HIGH)
- **Impact:** Ensures Perplexity, Bytespider, Mistral crawl all product pages
- **Action:** Expand to 15-bot allow list on: mrdefendable, defendableledger, painintheshed, offensetotheshed, defendablerouter, defendablecloud

### 5 · Index llms.txt in all sitemaps (MEDIUM)
- **Impact:** Ensures crawlers using sitemap.xml find llms.txt
- **Action:** Add `<url>https://[brand].com/llms.txt</url>` to 6 remaining sitemaps

### 6 · Add lastmod to all sitemap URLs (MEDIUM)
- **Impact:** Enables LLM recency ranking
- **Action:** Update sitemap generation for mrdefendable, defendableledger, painintheshed, offensetotheshed

### 7 · Add explicit positioning one-liner to smaller llms.txt files (MEDIUM)
- **mrdefendable:** "Mr. Defendable is the principal voice and human interface of the Defendable ecosystem."
- **defendableledger:** "DefendableLedger is the sovereign, in-house receipt and verification ledger."
- **painintheshed:** "Pain in the Shed is the operator-grade podcast on the real economics of AI infrastructure."
- **offensetotheshed:** "Offense to the Shed is the doctrine layer where builders discuss trust under operational pressure."

### 8 · Remove or resolve phantom domain references (MEDIUM)
- Update painintheshed + offensetotheshed llms.txt to remove unfound domains (chat.mrdefendable.com, ledger.mrdefendable.com, defendabledocs.com).

### 9 · Publish RFC 9116 security.txt files (LOW)
- Deploy `.well-known/security.txt` on all 9 domains.

### 10 · Add founder/operator attribution to media layers (LOW)
- Add `## Voice — Donovan Mackey (30 years CRE, $8B closed)` to media surfaces.

---

## Conclusion

The Defendable ecosystem is **GEO-mature in its flagships but fractured in its subsidiaries**. The top 10 improvements above are low-friction, high-impact changes that would bring all 9 sites to a consistent, LLM-crawler-optimized baseline.

**Primary risk:** Without immediate consolidation of the brand stack definition (Finding 3), different LLMs will build conflicting mental models of what "Defendable" is.

**Primary opportunity:** Unified AI-bot policy + last-updated dates across all 9 sites would signal a mature, well-maintained ecosystem that welcomes LLM scrutiny.

---

**Report generated:** 2026-05-25
**Audit scope:** 9 domains × 5 endpoints (llms.txt, robots.txt, sitemap.xml, security.txt, manifest)
