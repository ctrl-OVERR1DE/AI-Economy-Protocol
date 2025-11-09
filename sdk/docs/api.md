# AEP SDK API Reference

## Config
- `AEPConfig.from_env()` → `AEPConfig`
- Fields: `api_base`, `gateway_url`, `token_mint`, `timeout`
- Optional fields: `api_key`, `user_agent`, `max_retries`, `backoff_factor`
- Env vars: `AEP_API_BASE`, `AEP_GATEWAY_URL`, `AEP_TOKEN_MINT`, `AEP_API_KEY`, `AEP_MAX_RETRIES`, `AEP_BACKOFF`, `AEP_USER_AGENT`

## MarketplaceClient
- `MarketplaceClient(config=None, base_url=None, timeout=None)`
- `health()` → dict
- `stats()` → dict
- `get(path, **kwargs)` → dict
- `post(path, json=None, **kwargs)` → dict
- Typed helpers:
  - `health_typed()` → `HealthModel`
  - `stats_typed()` → `MarketplaceStatsModel`
  - `get_provider_typed(agent_address)` → `ProviderModel`
  - `create_request_typed(client_address, service_type, provider_address=None)` → `ServiceRequestModel`
- Providers:
  - `register_provider(payload)` → dict
  - `unregister_provider(agent_address)` → dict
  - `update_provider_status(agent_address, status)` → dict
  - `get_all_providers()` → dict
  - `get_online_providers()` → dict
  - `get_provider(agent_address)` → dict
  - `get_provider_stats(agent_address)` → dict
  - `get_provider_reviews(agent_address)` → dict
  - `get_provider_requests(agent_address, limit=10)` → dict
  - `get_provider_balance(agent_address, mint, rpc_url=None)` → dict
- Service discovery:
  - `discover_services(service_type=None)` → dict
  - `get_providers_by_service(service_type)` → dict
  - `find_best_provider(service_type, max_price=None, min_rating=None)` → dict
- Requests / jobs / reviews:
  - `create_request(client_address, service_type, provider_address=None)` → dict
  - `update_request(request_id, status, escrow_pda=None, amount=None)` → dict
  - `record_job_completion(provider_address, success, amount)` → dict
  - `add_review(provider_address, client_address, service_type, rating, comment, transaction_signature)` → dict
  - `search_providers(service_type=None, min_rating=None, max_price=None, status='online')` → dict

## PaymentClient
- `PaymentClient(config=None, gateway_url=None, timeout=None)`
- `health()` → dict
- Typed helper: `health_typed()` → `HealthModel`
- `verify_proof(escrow_pda)` → dict
- `claim_payment(escrow_pda, provider_address, retry_402=False, max_retries=3, backoff=1.5)` → dict or raises `PaymentRequired`

## Async Clients

### AsyncMarketplaceClient
- `AsyncMarketplaceClient(config=None, base_url=None, timeout=None)`
- Basic: `get`, `post`, `put`
- Convenience: `health()`, `stats()`
- Typed: `health_typed()` → `HealthModel`, `stats_typed()` → `MarketplaceStatsModel`, `get_provider_typed()` → `ProviderModel`, `create_request_typed()` → `ServiceRequestModel`
- Providers: `register_provider`, `unregister_provider`, `update_provider_status`, `get_all_providers`, `get_online_providers`, `get_provider`, `get_provider_stats`, `get_provider_reviews`, `get_provider_requests`, `get_provider_balance`
- Discovery: `discover_services`, `get_providers_by_service`, `find_best_provider`
- Requests/Jobs/Reviews: `create_request`, `update_request`, `record_job_completion`, `add_review`, `search_providers`

### AsyncPaymentClient
- `AsyncPaymentClient(config=None, gateway_url=None, timeout=None)`
- Convenience: `health()`, `verify_proof(escrow_pda)`, `claim_payment(...)`
- Typed: `health_typed()` → `HealthModel`

## Errors
- `AEPError`
- `APIError`
- `GatewayError`
- `PaymentRequired` (HTTP 402)
