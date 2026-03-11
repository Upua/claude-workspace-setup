---
name: documentation
description: Generate JSDoc/docstrings, API docs, READMEs, architecture docs, and user guides with templates for multiple formats.
# No binary requirements - knowledge skill
# Context cost: ~189 lines (~3K tokens)
---

# Documentation Skill

## Trigger
Activated when asked to document code, APIs, or generate documentation.

## Capabilities
- Generate JSDoc/docstrings for functions
- Create API documentation
- Write README files
- Generate architecture documentation
- Create user guides
- Document configuration options

## Documentation Standards

### JavaScript/TypeScript (JSDoc)
```javascript
/**
 * Calculates the total price including tax and discounts.
 *
 * @param {number} subtotal - The pre-tax subtotal amount
 * @param {number} taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @param {number} [discount=0] - Optional discount amount to subtract
 * @returns {number} The final total price
 * @throws {Error} If subtotal or taxRate is negative
 *
 * @example
 * // Calculate total with 8% tax and $10 discount
 * const total = calculateTotal(100, 0.08, 10);
 * // Returns: 98.00
 */
function calculateTotal(subtotal, taxRate, discount = 0) {
  // implementation
}
```

### Python (Docstrings)
```python
def calculate_total(subtotal: float, tax_rate: float, discount: float = 0) -> float:
    """
    Calculate the total price including tax and discounts.

    Args:
        subtotal: The pre-tax subtotal amount.
        tax_rate: Tax rate as decimal (e.g., 0.08 for 8%).
        discount: Optional discount amount to subtract. Defaults to 0.

    Returns:
        The final total price as a float.

    Raises:
        ValueError: If subtotal or tax_rate is negative.

    Example:
        >>> calculate_total(100, 0.08, 10)
        98.0
    """
    pass
```

## API Documentation Template

```markdown
# API Endpoint: [Name]

## Overview
Brief description of what this endpoint does.

## Request

### Method & URL
`POST /api/v1/resource`

### Headers
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |
| Content-Type | Yes | application/json |

### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Resource identifier |
| name | string | No | Display name |

### Request Body
```json
{
  "field1": "value1",
  "field2": 123
}
```

## Response

### Success (200 OK)
```json
{
  "id": "abc123",
  "status": "created",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### Errors
| Code | Description |
|------|-------------|
| 400 | Invalid request body |
| 401 | Unauthorized |
| 404 | Resource not found |
| 500 | Server error |

## Examples

### cURL
```bash
curl -X POST https://api.example.com/v1/resource \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"field1": "value1"}'
```
```

## README Template

```markdown
# Project Name

Brief description of what this project does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
npm install project-name
```

## Quick Start

```javascript
import { feature } from 'project-name';

const result = feature.doSomething();
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| option1 | string | 'default' | Description |

## API Reference

See [API Documentation](./docs/api.md)

## Contributing

See [Contributing Guide](./CONTRIBUTING.md)

## License

MIT
```

## Documentation Checklist

- [ ] All public functions/methods documented
- [ ] Parameters and return types specified
- [ ] Examples provided for complex APIs
- [ ] Error conditions documented
- [ ] Configuration options listed
- [ ] Quick start guide included
- [ ] Installation instructions current
- [ ] Links to related documentation

## Output Formats

Support generating documentation in:
- Markdown (.md)
- JSDoc comments
- Python docstrings
- OpenAPI/Swagger YAML
- TypeDoc format
