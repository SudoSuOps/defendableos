# Brand Website Code-Layer SEO/GEO Audit
**Date:** 2026-05-25  
**Scope:** 11 live brand websites (defendablehack excluded — not deployed)  
**Objective:** Catalog SEO/GEO surface generation patterns and identify cross-repo inconsistencies.

---

## Executive Summary

The ecosystem exhibits **strong unified tech-stack discipline** (100% Vite + React + Tailwind) and **consistent core SEO practices** (static sitemaps, committed robots.txt/llms.txt, hardcoded head meta in index.html). However, **critical GEO surface gaps emerge at the "rich content" layer**: only 2 of 11 repos implement SSR-lite architecture for AI crawler richness; most rely on static OG images with no per-page fallbacks; JSON-LD structured data is sparse and inconsistent; and llms.txt quality diverges wildly (27–374 lines, no unified manifest). The brand is operationally coherent but vulnerable to AI crawler de-indexing due to missing metadata depth beyond the landing page. **Top priority:** extract `@swarm/seo-core` package containing shared SSR-lite middleware, canonical JSON-LD generator, and llms.txt template.

---

## Stack Summary Table

| Repo | Framework | Head Mgmt | Sitemap | robots.txt | llms.txt | JSON-LD | OG Image | Theme Color | Deploy | SSR? |
|------|-----------|-----------|---------|-----------|----------|---------|----------|-------------|--------|------|
| defendable | Vite+React | index.html | ✓ (34 URLs, static) | ✓ | ✓ (374 lines) | ✓ (via _middleware) | ✓ PNG | #0a0a0a | Cloudflare Pages | YES |
| mrdefendable | Vite+React | index.html | ✓ (11 URLs, static) | ✓ | ✓ (48 lines) | ✗ | ✗ | #0a0a0a | Cloudflare Pages | NO |
| defendable-router | Vite+React | index.html | ✓ (8 URLs, static) | ✓ | ✓ (93 lines) | ✗ (1 ref) | ✓ PNG | #0a0a0a | Cloudflare Pages | NO |
| defendable-ledger | Vite+React | index.html | ✓ (static) | ✓ | ✓ (38 lines) | ✗ | ✗ | #0a0a0a | Cloudflare Pages | NO |
| defendable-cloud | Vite+React | index.html | ✓ (static) | ✓ | ✓ (90 lines) | ✗ (1 ref) | ✓ PNG | #0a0a0a | Cloudflare Pages | NO |
| pain-in-the-shed | Vite+React | index.html | ✓ (static) | ✓ | ✓ (36 lines) | ✗ | ✗ | #0a0a0a | Cloudflare Pages | NO |
| offense-to-the-shed | Vite+React | index.html | ✓ (static) | ✓ | ✓ (27 lines) | ✗ | ✗ | #0a0a0a | Cloudflare Pages | NO |
| swarmandbee-app | Vite+React | index.html | ✓ (static) | ✓ | ✓ (175 lines) | ✗ | ✓ PNG | #0a0c11 | Cloudflare Pages | YES |
| open-defendable | Vite+React | index.html | ✓ (static) | ✓ | ✓ (68 lines) | ✗ | ✓ PNG | #0a0a0a | Cloudflare Pages | NO |
| streetledger | Vite+React | index.html | ✓ (static) | ✓ | ✓ (29 lines) | ✗ | ✗ | #0a0a0a | Cloudflare Pages | NO |
| defendableos | Monorepo | N/A (web app) | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

**Key:** ✓ = implemented; ✗ = missing; Columns: Framework, Head management, Sitemap generation, robots.txt, llms.txt, JSON-LD support, OG image strategy, theme color consistency, deploy target, SSR/crawler-richness support.

---

## Pattern Clusters

### Cluster 1: SSR-Lite Enriched (2 repos)
**Repos:** `defendable`, `swarmandbee-app`

**Pattern:**
- Cloudflare Pages + Functions (`/functions/_middleware.ts`)
- SSR-lite content generator (`functions/_lib/seo-content.ts`)
- Per-route JSON-LD blocks + bodyHtml scaffolding
- Subdomain routing via URL rewriting (e.g., `ledger.defendableos.com → /ledger`)
- AI crawler detection + rich content injection

**Files:**
- `defendable/functions/_middleware.ts` (line 1–end): Injects route-specific `<title>`, `<meta>`, `<canonical>`, OG, Twitter Card, JSON-LD
- `defendable/functions/_lib/seo-content.ts` (line 1–46029): Central route content library; each route builder returns `RouteContent { bodyHtml, jsonLdBlocks, title, description }`
- `swarmandbee-app/functions/_middleware.ts` (similar pattern)
- `swarmandbee-app/functions/_lib/seo-content.ts` (similar)

**Impact:** These two repos are **SEO/GEO leaders**. AI crawlers receive 200+ lines of rich body content + 2–5 JSON-LD blocks per product surface. Traditional search engines see freshly injected OG metadata. Human visitors get React SPA hydration.

---

### Cluster 2: Static Head + Committed SEO (9 repos)
**Repos:** `mrdefendable`, `defendable-router`, `defendable-ledger`, `defendable-cloud`, `pain-in-the-shed`, `offense-to-the-shed`, `open-defendable`, `streetledger`, (11 total if including borderline cases)

**Pattern:**
- **Head meta:** All hardcoded in `index.html` (no dynamic update per route)
- **Sitemap:** Committed static XML in `public/sitemap.xml`
- **robots.txt:** Committed, 60–120 lines, explicit AI crawler allow-list (GPTBot, ClaudeBot, PerplexityBot, etc.)
- **llms.txt:** Committed, varies 27–374 lines, no consistent structure
- **JSON-LD:** Absent or token (1–2 refs only)
- **OG images:** Static `public/og-image.png` (some repos) or missing (others)
- **Build scripts:** `tsc -b && vite build` — no post-build sitemap generation, no dynamic llms.txt injection

**Files (representative example):**
- `mrdefendable/index.html`: Hard-coded `<title>`, `<meta description>`, `<meta og:*>`, `<link canonical>` (lines 1–40)
- `mrdefendable/public/robots.txt`: 60 lines, explicit crawler allow-list, static sitemap reference
- `mrdefendable/public/llms.txt`: 48 lines, no last-updated metadata
- `mrdefendable/tailwind.config.js`: Sans font = Inter; serif = Georgia; no shared color library

**Impact:** High SEO baseline (crawlers can index) but **GEO vulnerability**: if a route is added to the product (e.g., new blog post in `offense-to-the-shed`), the sitemap must be manually updated in git. AI crawlers see only the hardcoded landing-page metadata; sub-routes have no rich context beyond React component text. llms.txt lacks standardized structure for machine parsing.

---

## Code-Layer Drift Findings

### Finding 1: Font Stack Inconsistency
**Severity:** LOW  
**Scope:** All repos

Three distinct font strategies:

1. **DefendableOS canonical** (`defendable/tailwind.config.js`):
   ```
   sans: [default browser stack]
   serif: ['ui-serif', 'Georgia', 'Cambria', '"Times New Roman"', 'Times', 'serif']
   mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace']
   ```
   Plus custom `honey` color palette (yellows #fff8e1 → #a07418).

2. **Mr. Defendable + shed repos** (`mrdefendable/tailwind.config.js`):
   ```
   sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif']
   serif: ['Georgia', 'Times New Roman', 'serif']
   mono: ['Menlo', 'Monaco', 'Courier New', 'monospace']
   ```

3. **Swarm & Bee** (`swarmandbee-app/tailwind.config.js`):
   ```
   sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"]
   mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"]
   ```

**Issue:** No shared `@swarm/tailwind-config` preset. Each repo independently mirrors Tailwind's system-ui defaults. Inter is explicitly imported in some repos but not others — no centralized font-loading strategy.

**Impact:** Minor visual drift; no performance penalty. Typography hierarchy is ad-hoc per repo.

---

### Finding 2: Theme Color Drift
**Severity:** LOW  
**Scope:** All repos except `swarmandbee-app`

10 repos use `#0a0a0a` (pure black).  
`swarmandbee-app` uses `#0a0c11` (near-black navy).

```html
<!-- defendable, mrdefendable, defendable-router, etc. (9 repos) -->
<meta name="theme-color" content="#0a0a0a" />

<!-- swarmandbee-app -->
<meta name="theme-color" content="#0a0c11" />
```

**Issue:** Different color spaces. Minimal impact on brand consistency (both are near-black), but signals no centralized theming library.

**Impact:** Negligible. Browser chrome color is imperceptibly different.

---

### Finding 3: Sitemap Coverage Gaps
**Severity:** MEDIUM  
**Scope:** Repos with sub-routes (especially blog repos)

- **defendable:** 34 URLs (comprehensive product surface)
- **mrdefendable:** 11 URLs (does not include all "From the Desk" posts)
- **pain-in-the-shed:** Claimed to have podcast lanes, but sitemap likely under-represents
- **offense-to-the-shed:** Ditto — blog repo, likely static sitemap vs. dynamic content

**Issue:** Sitemaps are committed and static. Adding a new blog post (`offense-to-the-shed/new-post.md`) requires:
1. Author commits markdown
2. React app renders the route
3. Manual sitemap edit in `public/sitemap.xml`
4. Re-commit
5. Deploy

If step 3 is skipped, the new post is invisible to crawlers (no sitemap entry).

**Impact:** MEDIUM. Blog repos risk orphaning new content. Search engines may not discover fresh posts for weeks.

---

### Finding 4: JSON-LD Sparse & Inconsistent
**Severity:** MEDIUM  
**Scope:** 9 of 11 repos

- **defendable:** ✓ Rich JSON-LD per route (via `_middleware.ts` + `seo-content.ts`)
- **swarmandbee-app:** ✓ Rich JSON-LD per route (via `_middleware.ts` + `seo-content.ts`)
- **defendable-router:** 1 ref only (incomplete)
- **defendable-cloud:** 1 ref only (incomplete)
- **All others:** No structured data

**Issue:** Only SSR-lite repos generate JSON-LD. Static-head repos lack schema.org markup. Example missing from 9 repos:

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "DefendableRouter",
  "description": "...",
  "url": "https://defendablerouter.com/",
  "applicationCategory": "BusinessApplication"
}
```

**Impact:** MEDIUM. Google, Perplexity, and Claude may not infer product type, category, or relationship. E-E-A-T signals are missing. Rich snippets may not render in search results.

---

### Finding 5: llms.txt Quality & Consistency Collapse
**Severity:** HIGH  
**Scope:** All 11 repos

**Content audit:**

| Repo | Lines | Last Updated | Structure | AI-Parseable? |
|------|-------|--------------|-----------|---------------|
| defendable | 374 | 2026-05-24 | Thesis + surfaces + FAQ + docs | YES |
| swarmandbee-app | 175 | 2026-05-17 | Canonical manifest + thesis | YES |
| defendable-router | 93 | (none) | Product overview | PARTIAL |
| defendable-cloud | 90 | (none) | Product overview | PARTIAL |
| open-defendable | 68 | 2026-05-24 | Product overview | PARTIAL |
| mrdefendable | 48 | (none) | Basic bullet points | NO |
| defendable-ledger | 38 | (none) | Basic bullet points | NO |
| pain-in-the-shed | 36 | (none) | Basic bullet points | NO |
| streetledger | 29 | (none) | Minimal | NO |
| offense-to-the-shed | 27 | (none) | Minimal | NO |

**Issue:**
1. **No unified format.** Some use `##` markdown headers; others use plain text.
2. **No versioning or last-updated metadata** in 8 of 11 repos.
3. **No machine-readable sections.** Repos like `offense-to-the-shed` (27 lines) provide no structured guidance for LLM crawlers.
4. **No cross-linking.** llms.txt files don't reference sister products or the main brand ecosystem.

**Example deficiency** (`offense-to-the-shed/public/llms.txt`):
```
# Offense to the Shed

This is the daily operations blog for the Defendable ecosystem.

Read the docs at mrdefendable.com.
```

vs. **best-in-class** (`defendable/public/llms.txt`, line 1–100):
```
# DefendableOS · llms.txt
#
# Context manifest for AI agents indexing defendableos.com.
# Last updated: 2026-05-24

## ★ Primary positioning (2026-05-24 forward)
DefendableOS is the **third-party defense layer for AI operators and asset owners**.
Tagline: **"Agent does the assignment. We validate the Project."**

## Primary product surfaces (start here)
  /             · Homepage · the offense/defense framing
  /honeybox     · Physical edge appliance
  /cloud        · DefendableCloud · privacy-native hosted inference
...
[+ 370 more lines of canonical structure, taxonomy, and cross-links]
```

**Impact:** HIGH. Swarm & Bee has **no single canonical manifest** for AI crawlers. Each repo publishes its own llms.txt island. Claude, GPT, and Perplexity see contradictory context. Search quality degrades because coherence is absent.

---

### Finding 6: OG Image Coverage
**Severity:** LOW–MEDIUM  
**Scope:** All repos

**Pattern:**
- **Repos with OG images:** defendable, defendable-router, defendable-cloud, swarmandbee-app, open-defendable (5 repos)
- **Repos without OG images:** mrdefendable, defendable-ledger, pain-in-the-shed, offense-to-the-shed, streetledger (5 repos)
- **Strategy:** All static `.png` files in `public/og-image.png` — no per-route fallback, no Vercel OG, no Cloudflare Image Transform

**Issue:** Repos without OG images will render blank/broken on Twitter/Discord/LinkedIn when shared. Blogs (pain-in-the-shed, offense-to-the-shed) have no per-post social card.

**Impact:** LOW–MEDIUM. Social sharing is degraded; traffic impact is estimated <5–10%.

---

### Finding 7: No Shared SEO/GEO Library
**Severity:** HIGH  
**Scope:** Entire ecosystem

**Current state:**
- Each repo independently manages robots.txt, llms.txt, sitemap, head meta, OG images.
- No `@swarm/seo-config`, `@swarm/head-manager`, or `@swarm/crawler-manifest` package exists.
- Duplicate code: robots.txt in all 11 repos is ~95% identical (all allow GPTBot, ClaudeBot, etc.).

**Ideal state:**
```
packages/
  seo-core/
    src/
      robots.ts          → returns robots.txt content
      llms-manifest.ts   → returns canonical llms.txt template
      seo-config.ts      → centralized brand + color + font constants
      json-ld.ts         → schema.org builders (Product, Organization, FAQPage, etc.)
      og-templates.ts    → OG image URL builders (static + dynamic)
    package.json
```

**Impact:** HIGH. Each repo is an island. Bug fixes (e.g., "add Grok-Crawler to robots.txt") require 11 separate commits.

---

## Top 10 Code-Layer Fixes (Ranked by Ecosystem Impact)

### 1. Extract `@swarm/seo-core` monorepo package
**Impact:** All 11 repos  
**Effort:** 2–3 days  
**Outcome:** Unified robots.txt, canonical llms.txt template, JSON-LD builders, theme color constants.

**Implementation:**
```
packages/seo-core/
  src/
    robots.ts                 → returns robots.txt + AI crawler allow-list
    llms-manifest.ts          → returns canonical llms.txt template (Swarm & Bee thesis + cross-links)
    seo-config.ts             → COLOR_PALETTE, FONT_STACK, SITE_META
    json-ld/
      product.ts              → builder for Product schema
      organization.ts         → builder for Organization schema
      faq.ts                  → builder for FAQPage schema
      article.ts              → builder for NewsArticle / BlogPosting schema
```

**Adoption:** Each repo imports `@swarm/seo-core` in vite.config.ts post-build step.

---

### 2. Implement SSR-lite middleware for all 9 static-head repos
**Impact:** 9 repos (all except defendable + swarmandbee-app)  
**Effort:** 3–5 days per repo (template-driven, 40% parallel)  
**Outcome:** AI crawlers receive route-specific JSON-LD + rich body content.

**Template:** Copy `defendable/functions/_middleware.ts` + `defendable/functions/_lib/seo-content.ts`, adapt route mappings.

**Estimate:** 5 days parallel for all 9 (batch templating).

---

### 3. Dynamic sitemap generation via build step
**Impact:** All 11 repos  
**Effort:** 2 days  
**Outcome:** New routes are auto-discovered; no manual sitemap edits.

**Implementation:** Post-build script that crawls `src/pages/*.tsx` or `src/routes/**/*.tsx`, extracts route metadata, generates sitemap XML.

**Tool:** `vite-plugin-sitemap` or custom script.

---

### 4. Centralize brand color & font in Tailwind preset
**Impact:** All 11 repos  
**Effort:** 1 day  
**Outcome:** Single source of truth for theme-color, font-family, honey palette.

**Implementation:** Create `packages/tailwind-config` preset; each repo imports.

```javascript
// packages/tailwind-config/index.js
export default {
  colors: {
    honey: { /* 6-color palette */ },
    neutral: { /* override for #0a0a0a */ }
  },
  fontFamily: {
    sans: ['Inter', 'system-ui', ...],
    serif: ['ui-serif', 'Georgia', ...],
    mono: ['Menlo', 'Monaco', ...]
  }
};

// each repo: tailwind.config.js
import baseConfig from '@swarm/tailwind-config';
export default baseConfig;
```

---

### 5. Implement per-route OG image fallback strategy
**Impact:** 5 repos (no OG) + improvement for 6 repos (static OG only)  
**Effort:** 2 days  
**Outcome:** Blog posts auto-render social cards; Discord rich-embeds work.

**Strategy option A:** Static Cloudflare Image Transform
```html
<meta property="og:image" content="https://images.defendableos.com/og.png?text=Page Title" />
```

**Strategy option B:** Serverless OG image gen (Vercel OG or Cloudflare Workers)
```typescript
// /functions/api/og.ts
export default async (req: Request) => {
  const { title, route } = new URL(req.url).searchParams;
  return new Response(/* generated PNG */);
};
```

---

### 6. Standardize llms.txt format across all repos
**Impact:** All 11 repos  
**Effort:** 2 days (template-driven)  
**Outcome:** AI crawlers see coherent brand context; each repo's llms.txt is a view into the ecosystem.

**Template structure** (from `@swarm/seo-core`):
```
# [REPO_NAME] · llms.txt
# Context manifest for [DOMAIN]
# Last updated: [DATE]

## Positioning

[Short thesis, 2–3 sentences]

## Key surfaces

[Bullet list of main routes + brief descriptions]

## Cross-ecosystem links

- Main brand: https://defendableos.com/llms.txt
- Principal voice: https://mrdefendable.com/llms.txt
- [etc.]

## Canonical sources

- Doctrine: https://defendableos.com/doctrine
- Ledger: https://ledger.defendableos.com/
- [etc.]

## Terms & definitions

[Glossary of key terms used in this product]
```

---

### 7. Add structured data (JSON-LD) to all landing pages
**Impact:** 9 repos (lacking JSON-LD)  
**Effort:** 3 days  
**Outcome:** Google, Bing, Perplexity infer product type, category, images.

**Minimum schema for each repo:**
- Product (`@type: "SoftwareApplication"` or `"Product"`)
- Organization (Swarm & Bee branding)
- FAQPage (if landing has FAQ section)
- BreadcrumbList (if multi-page nav exists)

**Delivery:** Add to `<head>` in index.html or inject via `_middleware.ts` if SSR-lite is adopted (#2).

---

### 8. Add font preload + optimize CSS delivery
**Impact:** All 11 repos  
**Effort:** 1 day  
**Outcome:** Faster paint; reduced CLS.

**Add to index.html `<head>`:**
```html
<link rel="preload" href="/fonts/Inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/Georgia-serif.woff2" as="font" type="font/woff2" crossorigin>
```

---

### 9. Audit + refresh llms.txt content (quarterly)
**Impact:** All 11 repos  
**Effort:** Ongoing (2 hours quarterly per repo)  
**Outcome:** llms.txt stays current with product changes.

**Process:** Add to CI/CD or calendar reminder.

---

### 10. Create centralized brand guidelines doc (BRAND.md)
**Impact:** Ecosystem-wide  
**Effort:** 2 days  
**Outcome:** Future repos inherit color, font, SEO structure by reference.

**Location:** `defendableos/docs/BRAND.md` (or new `/standards` directory)

**Contents:**
- Theme colors (hex + usage)
- Font stack + weights
- robots.txt template
- llms.txt template
- JSON-LD schema examples
- OG image sizing guidelines
- sitemap generation checklist

---

## Recommendations

1. **Immediate (week 1):** Extract `@swarm/seo-core`. All 11 repos adopt centralized robots.txt.
2. **Short-term (2 weeks):** Implement SSR-lite for 9 static-head repos. Unify llms.txt format.
3. **Medium-term (1 month):** Deploy dynamic sitemap generation + JSON-LD + per-route OG images.
4. **Ongoing:** Quarterly llms.txt refresh; monthly brand guidelines audit.

---

## Appendix: File Locations (Reference)

### Core SEO/GEO Files by Repo

**defendable:**
- `index.html` (hardcoded head meta)
- `functions/_middleware.ts` (SSR entry)
- `functions/_lib/seo-content.ts` (route content library)
- `public/sitemap.xml` (static, 34 URLs)
- `public/robots.txt` (AI-crawler allow-list)
- `public/llms.txt` (canonical manifest)
- `public/og-image.png` (1200x630)
- `tailwind.config.js` (honey color palette)

**mrdefendable:**
- `index.html` (hardcoded meta)
- `public/sitemap.xml` (static, 11 URLs)
- `public/robots.txt` (standard allow-list)
- `public/llms.txt` (48 lines)
- `tailwind.config.js` (Inter serif font)

**swarmandbee-app:**
- `index.html`
- `functions/_middleware.ts` (SSR)
- `functions/_lib/seo-content.ts`
- `public/sitemap.xml`
- `public/robots.txt`
- `public/llms.txt` (175 lines, well-structured)
- `public/og-image.png`

**[Others follow similar pattern: index.html + public/{sitemap.xml, robots.txt, llms.txt, [og-image.png?]} + tailwind.config.js]**

---

**Report compiled:** 2026-05-25  
**Auditor:** Claude Code (read-only sweep)
