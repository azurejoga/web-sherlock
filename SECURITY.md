# Security Policy

## Supported Versions

We actively maintain security for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Features Implemented

### Authentication & Authorization
- ✅ **Secure Password Hashing**: Using bcrypt with proper salt generation
- ✅ **JWT Security**: HS256 algorithm with strict validation, 1-hour expiration
- ✅ **Rate Limiting**: Login attempt limiting (5 attempts per 5 minutes)
- ✅ **Token Revocation**: Blacklist system for compromised tokens
- ✅ **Session Management**: Secure session handling with environment-based secrets

### Input Validation & Sanitization
- ✅ **File Upload Security**: JSON validation with size and format restrictions
- ✅ **Path Traversal Prevention**: Filename sanitization in export functions
- ✅ **XSS Prevention**: Input sanitization and output encoding
- ✅ **SQL Injection Prevention**: Parameterized queries (where applicable)

### Cryptographic Security
- ✅ **Secure Random Generation**: Using os.urandom() for nonces and tokens
- ✅ **AES-GCM Encryption**: Ready for sensitive data encryption if needed
- ✅ **PBKDF2 Key Derivation**: For password-based key generation

### Network Security
- ✅ **Security Headers**: Comprehensive HTTP security headers
- ✅ **Content Security Policy**: XSS and injection attack prevention
- ✅ **HTTPS Enforcement**: Strict Transport Security headers
- ✅ **Frame Protection**: Clickjacking prevention

### Logging & Monitoring
- ✅ **Secure Logging**: Log injection prevention and sanitization
- ✅ **Error Handling**: Secure error messages without information disclosure
- ✅ **Audit Trail**: Authentication and critical action logging

### File System Security
- ✅ **ZIP Bomb Protection**: Controlled file creation in ZIP exports
- ✅ **Temporary File Cleanup**: Automatic cleanup of uploaded files
- ✅ **Directory Traversal Prevention**: Sanitized file paths

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 1. **Do Not** Create a Public Issue
Please do not report security vulnerabilities through public GitHub issues.

### 2. Send a Private Report
Email security concerns to: **azurejoga@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (if available)

### 3. Response Timeline
- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Critical issues within 30 days

### 4. Disclosure Policy
We follow a coordinated disclosure policy:
1. We'll acknowledge receipt of your report
2. We'll investigate and develop a fix
3. We'll test the fix thoroughly
4. We'll deploy the fix to production
5. We'll publicly acknowledge your contribution (if desired)

## Security Best Practices for Users

### For Developers
1. Keep dependencies updated
2. Use environment variables for secrets
3. Enable HTTPS in production
4. Regularly review access logs
5. Implement proper backup procedures

### For Deployment
1. Use strong, unique passwords
2. Enable two-factor authentication where possible
3. Regularly update the application
4. Monitor for suspicious activity
5. Use secure hosting environments

## CVEs Addressed

The following known vulnerabilities have been mitigated:

| CVE ID | Description | Status |
|--------|-------------|--------|
| CVE-2020-36242 | Weak bcrypt implementation | ✅ Fixed |
| CVE-2013-7370 | Static IV in AES encryption | ✅ Fixed |
| CVE-2019-17571 | Logging injection vulnerabilities | ✅ Fixed |
| GHSA-ffqj-6fqr-9h24 | Insecure JWT decoding | ✅ Fixed |
| GHSA-c7hr-j4mj-j2w6 | JWT "none" algorithm acceptance | ✅ Fixed |
| GHSA-gw9q-c7gh-j9vm | ZIP path traversal vulnerability | ✅ Fixed |
| GHSA-gwrp-pvrq-jmwv | Unvalidated relative paths in ZIP | ✅ Fixed |

## Security Contact

For security-related questions or concerns:
- Email: azurejoga@gmail.com]
- GitHub: [@azurejoga](https://github.com/azurejoga)

---

*Last updated: June 26, 2025*
*Security policy version: 1.0*