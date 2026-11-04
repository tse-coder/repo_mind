# ADR 0001: Redis for Session Storage

## Status

Accepted

## Context

The authentication API needs a shared session store that works across multiple
API workers. Candidates were Redis and Memcached.

## Decision

We chose Redis over Memcached for session storage.

Reasons:

- Redis supports TTL key expiry that matches JWT access-token lifetime.
- Redis persistence lets sessions survive a rolling deploy.
- We already operate Redis for rate limiting, so operational cost is lower.

Memcached was rejected because it is purely volatile and cannot store the
webhook delivery retry cursor alongside sessions.

## Consequences

Session keys live under `session:{user_id}` with a 15-minute TTL. The login
handler writes the session after `authenticate()` succeeds.
