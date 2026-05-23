"""Defendable Compute Bench · Phase A read-only capture.

Implements the umbrella defined in docs/DEFENDABLE_COMPUTE_BENCH.md.
Phase A scope:
  · capture identity + system + runtime (read-only, no installs)
  · write structured JSON receipt bundle
  · SHA-256 manifest over the bundle
  · public-safe redacted export via the same vault doctrine
Phase A explicitly does NOT:
  · run workload/stress tests
  · change GPU clocks, power limits, or runtime config
  · upload anything
  · touch occupied GPUs without explicit operator override
"""
