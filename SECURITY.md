# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### DO NOT

- ❌ Open a public GitHub issue
- ❌ Discuss the vulnerability publicly before it's fixed
- ❌ Exploit the vulnerability maliciously

### DO

1. **Email** the maintainer directly at: [rasinbinabdulla@gmail.com](mailto:rasinbinabdulla@gmail.com)
2. **Include** in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

3. **Wait** for acknowledgment (within 48 hours)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Fix Timeline**: Depends on severity
  - Critical: Target within 7 days
  - High: Target within 14 days  
  - Medium: Target within 30 days
  - Low: Will be scheduled

### Disclosure Policy

We follow **Coordinated Disclosure**:
1. You report the vulnerability privately
2. We confirm and develop a fix
3. We release a patched version
4. We publicly disclose the vulnerability (with credit to you, if desired)
5. You may publish your findings after public disclosure

### Security Features

OpsDeck includes:

- ✅ **Signed URL Tokens**: Prevents IDOR and tampering
- ✅ **CSRF Protection**: Signed cookies for state changes
- ✅ **CSP with Nonces**: Prevents XSS attacks
- ✅ **Password Hashing**: SHA-256 with salt
- ✅ **Audit Logging**: Full trail of all changes
- ✅ **RBAC**: Role-based permissions
- ✅ **Input Validation**: Pydantic v2 schemas
- ✅ **SQL Injection Prevention**: ORM-only, no raw SQL

### Security Best Practices

When deploying:

```python
# ✅ DO THIS
admin = ShadcnAdmin(
    app,
    engine=engine,
    secret_key=os.getenv("ADMIN_SECRET"),  # From environment
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
)

# ❌ DON'T DO THIS
admin = ShadcnAdmin(
    app,
    engine=engine,
    secret_key="my-weak-secret"  # Hardcoded, weak
)
```

**Additional Recommendations:**
- Use HTTPS in production
- Keep dependencies updated
- Enable audit logging
- Review RBAC permissions regularly
- Use strong secret keys (32+ characters)
- Set secure session cookie flags

### Hall of Fame

Security researchers who responsibly disclose vulnerabilities will be:
- Credited in security advisories (if desired)
- Listed in CHANGELOG
- Thanked publicly (if desired)

Thank you for helping keep OpsDeck secure! 🛡️
