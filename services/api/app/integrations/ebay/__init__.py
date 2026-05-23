"""eBay OAuth + Browse API integration.

Public surface:
  · oauth.get_application_token()     · cached client_credentials token
  · browse_api.search_item_summaries()  · Browse API search wrapper
  · smoke.run()                         · CLI smoke test (python -m)

Doctrine:
  · Cert ID (Client Secret) NEVER logged
  · Access tokens NEVER returned in API responses
  · Token cache in-memory only · refreshed 100s before expiry
  · Sandbox by default · production requires explicit env flip
"""
