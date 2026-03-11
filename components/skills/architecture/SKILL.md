---
name: architecture
description: API design (REST/GraphQL) and database architecture (schema, indexing, migrations). Use for endpoint design, OpenAPI specs, query optimization.
---

# Architecture

## API Design
- REST: resource-oriented URLs, proper HTTP methods (GET read, POST create, PUT replace, PATCH update, DELETE remove)
- Status codes: 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable, 429 Rate Limited, 500 Internal
- Pagination: cursor-based for large datasets, offset-based for small. Include `next`, `prev` links.
- Versioning: URL path (`/v1/`) preferred. Header versioning for internal APIs.
- Error format: `{"error": {"code": "VALIDATION_ERROR", "message": "human readable", "details": [...]}}`
- OpenAPI: define schemas with examples, use `$ref` for reuse, generate docs from spec

## Database Architecture
- Normalization: 3NF default. Denormalize only with measured performance need.
- Indexing: index foreign keys, frequent WHERE/ORDER BY columns. Composite indexes: most selective column first.
- Query optimization: EXPLAIN ANALYZE before optimizing. Watch for sequential scans, nested loops on large tables.
- Migrations: always reversible (up + down). Never drop columns in production without deprecation period.
- Connection pooling: use pgBouncer/equivalent. Set pool size = 2 * CPU cores + disk spindles.
