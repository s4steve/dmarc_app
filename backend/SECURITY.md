# Security

Current security posture of the DMARC Analytics backend. Regression tests for every
control below live in `tests/test_security_regressions.py` and run without Elasticsearch or Redis:

```bash
pip install -r requirements-dev.txt
pytest tests/test_security_regressions.py
pip-audit -r requirements.txt
```

## Required configuration

The API refuses to start without these (see `/.env.example`):

| Variable | Notes |
|---|---|
| `SECRET_KEY` | JWT signing key, at least 32 chars. `openssl rand -hex 32` |
| `ELASTICSEARCH_PASSWORD` | ES `elastic` user password |
| `REDIS_PASSWORD` | Required by `docker-compose.yml` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Optional. Creates the first `system_admin` when the users index is empty. Password 12-72 chars |
| `ENVIRONMENT` | Defaults to `production` (generic 5xx messages). `development` shows sanitized details |

There are no default credentials.

## Controls

**Authentication**: Users live in Elasticsearch with bcrypt hashes. On every request the user
record is re-read, so deactivation and role changes apply immediately. Unknown emails still cost
a bcrypt check, so response timing doesn't reveal which accounts exist.

**Tokens and sessions**: HS256 JWTs (PyJWT), 30-minute expiry, a unique `jti` per token.
Sessions and revocations are stored in Redis as SHA-256 token hashes, never raw tokens.
`/auth/logout` revokes the current token and `/auth/logout-all` revokes every session for the
user. Revocation checks **fail closed**: if Redis is unreachable, the token is rejected.
The frontend calls `/auth/logout` on sign-out.

**Authorization**: Three roles: `read_only`, `admin` (their own customer), and `system_admin`.
Only a `system_admin` can create or promote another `system_admin` or edit one. Third-party
service definitions are shared by all customers, so every mutating `/services` route requires
`system_admin`. Alerts can only be resolved by their own customer.

**Rate limiting** (slowapi, stored in Redis): `/auth/login` allows 5/min per IP; upload allows
5/min and summary 30/min per session.

**Uploads**:
- Requests over 11 MB are rejected before the body is read, based on Content-Length.
- Files over 10 MB are rejected.
- Gzip is decompressed with a 50 MB output cap, which blocks decompression bombs.
- Any document with a `<!DOCTYPE` is rejected, which blocks XXE and entity expansion. xmltodict
  also disables entities by default.

**Input**: Domain parameters go through `InputSanitizer.sanitize_domain`. All Elasticsearch
queries are structured DSL (`term`/`range`), so user input is never interpreted as query syntax.

**Errors**: Handlers don't catch exceptions to echo them back. Unhandled errors reach the global
handler, which logs the details and returns a generic 500. 4xx messages are fixed strings written
in the code.

**Headers**: `middleware/security_headers.py` sets CSP, X-Frame-Options, nosniff, Referrer-Policy,
Permissions-Policy and no-store caching. HSTS is on in production.

**Containers**: The API runs as a non-root user, with no `--reload` and no source mount (the dev
override `docker-compose.dev.yml` adds both back). Redis requires a password and isn't published.
Elasticsearch has security enabled and is bound to 127.0.0.1.

## Known limits

- The body-size guard trusts `Content-Length`, so chunked uploads skip it. Put a reverse proxy
  body limit (`client_max_body_size 11m`) in front of the API in production.
- Session IP tracking records the direct peer only. Behind a trusted proxy, run uvicorn with
  `--proxy-headers --forwarded-allow-ips=<proxy>`.
- Tokens are stored in `localStorage`, so an XSS on the frontend could read them. The CSP is the
  mitigation. Moving to httpOnly cookies would need CSRF protection.
- There is no cap on concurrent sessions per user.

## Incident notes

- The Elasticsearch password previously hardcoded in `docker-compose.yml` and `app/core/config.py` is in git history (from `c528c9d`)
  and **must be treated as compromised**. Rotate it on every environment that used it.
