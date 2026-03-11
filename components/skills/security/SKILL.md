---
name: security
description: OWASP Top 10 vulnerability checking, secret detection, auth review, security headers, and threat modeling with severity-graded output.
# No binary requirements - knowledge skill (scanning tools optional)
# Context cost: ~137 lines (~2.5K tokens)
---

# Security Analysis Skill

## Trigger
Activated when asked about security, vulnerabilities, or audits.

## Capabilities
- OWASP Top 10 vulnerability checking
- Dependency vulnerability scanning
- Secret detection
- Authentication/authorization review
- Security configuration analysis
- Threat modeling assistance

## OWASP Top 10 Checklist

### A01:2021 - Broken Access Control
- [ ] Verify authorization on all protected resources
- [ ] Deny by default principle
- [ ] Rate limiting implemented
- [ ] CORS properly configured
- [ ] Directory listing disabled

### A02:2021 - Cryptographic Failures
- [ ] Data classified by sensitivity
- [ ] Encryption at rest for sensitive data
- [ ] TLS 1.2+ for data in transit
- [ ] Strong algorithms (AES-256, RSA-2048+)
- [ ] Proper key management

### A03:2021 - Injection
- [ ] Parameterized queries for SQL
- [ ] Input validation and sanitization
- [ ] ORM/query builders used correctly
- [ ] Command injection prevention
- [ ] LDAP injection prevention

### A04:2021 - Insecure Design
- [ ] Threat modeling performed
- [ ] Security requirements defined
- [ ] Secure design patterns used
- [ ] Defense in depth applied

### A05:2021 - Security Misconfiguration
- [ ] Hardened server configuration
- [ ] Unnecessary features disabled
- [ ] Default credentials changed
- [ ] Error handling doesn't leak info
- [ ] Security headers configured

### A06:2021 - Vulnerable Components
- [ ] Component inventory maintained
- [ ] Dependencies regularly updated
- [ ] CVE monitoring active
- [ ] Unused dependencies removed

### A07:2021 - Authentication Failures
- [ ] Strong password policy
- [ ] MFA support
- [ ] Secure session management
- [ ] Brute force protection
- [ ] Secure password storage (bcrypt/argon2)

### A08:2021 - Software and Data Integrity
- [ ] CI/CD pipeline secured
- [ ] Dependency verification
- [ ] Code signing where applicable
- [ ] Integrity checks on data

### A09:2021 - Security Logging Failures
- [ ] Login/access attempts logged
- [ ] High-value transactions logged
- [ ] Logs protected from tampering
- [ ] Alerting configured

### A10:2021 - Server-Side Request Forgery
- [ ] URL validation on server
- [ ] Network segmentation
- [ ] Deny by default firewall rules
- [ ] Response validation

## Severity Levels

| Level | Icon | Description | Response Time |
|-------|------|-------------|---------------|
| CRITICAL | :red_circle: | Active exploit possible | Immediate |
| HIGH | :orange_circle: | Significant risk | 24 hours |
| MEDIUM | :yellow_circle: | Moderate risk | 1 week |
| LOW | :green_circle: | Minor risk | Next release |

## Secret Detection Patterns

Look for:
- API keys: `[A-Za-z0-9_]{20,}`
- AWS keys: `AKIA[0-9A-Z]{16}`
- Private keys: `-----BEGIN.*PRIVATE KEY-----`
- Passwords in code: `password\s*=\s*['"][^'"]+['"]`
- Connection strings: `mongodb://`, `postgres://`, `mysql://`

## Security Headers Checklist

```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=()
```

## Output Format

### Security Report Structure

1. **Executive Summary**
   - Overall risk level
   - Critical findings count
   - Immediate actions required

2. **Findings**
   For each issue:
   - Severity level
   - Location (file:line)
   - Description
   - Impact
   - Remediation steps
   - References (CWE, CVE)

3. **Recommendations**
   - Prioritized action items
   - Quick wins
   - Long-term improvements

4. **Compliance Notes**
   - Relevant standards (PCI-DSS, HIPAA, GDPR)
   - Compliance gaps identified
