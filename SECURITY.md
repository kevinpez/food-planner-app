# Security Policy

## Overview

This document outlines the security measures implemented in the AI-Powered Food Planner application and provides guidelines for secure deployment and usage.

## Security Features Implemented

### 1. Authentication & Authorization
- **Password Security**: Werkzeug password hashing with salt
- **Session Management**: Flask-Login with secure session cookies
- **Access Control**: `@login_required` decorators on protected routes
- **User Data Isolation**: Users can only access their own data

### 2. Input Validation & Sanitization
- **XSS Prevention**: Input sanitization using bleach library
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **Data Validation**: Server-side validation for all user inputs

### 3. Security Headers
- **X-Content-Type-Options**: nosniff
- **X-Frame-Options**: DENY
- **X-XSS-Protection**: 1; mode=block
- **Strict-Transport-Security**: HTTPS enforcement
- **Referrer-Policy**: strict-origin-when-cross-origin

### 4. Session Security
- **Secure Cookies**: HTTPOnly, Secure, SameSite attributes
- **Session Timeout**: 24-hour session lifetime
- **CSRF Time Limit**: 1-hour token validity

### 5. Environment Security
- **Secret Management**: Environment variables for sensitive data
- **No Hardcoded Secrets**: All API keys and secrets externalized
- **Strong Secret Generation**: Auto-generated secrets if not provided

## Deployment Security Checklist

### Production Environment
- [ ] Set strong `SECRET_KEY` environment variable
- [ ] Configure `FLASK_ENV=production`
- [ ] Use HTTPS/TLS encryption
- [ ] Set secure database credentials
- [ ] Configure proper file permissions
- [ ] Enable firewall and security groups
- [ ] Regular security updates
- [ ] Monitor application logs

### Environment Variables Required
```env
SECRET_KEY=your-very-strong-secret-key-minimum-32-characters
DATABASE_URL=your-production-database-url
ANTHROPIC_API_KEY=your-anthropic-api-key
FLASK_ENV=production
```

## Security Best Practices

### For Users
1. Use strong, unique passwords
2. Log out when finished
3. Don't share account credentials
4. Report suspicious activity

### For Developers
1. Keep dependencies updated
2. Follow secure coding practices
3. Validate all user inputs
4. Use parameterized queries
5. Implement proper error handling
6. Regular security audits

## Known Limitations

1. **Rate Limiting**: Currently implemented but may need tuning for high-traffic scenarios
2. **File Upload**: Limited to 16MB, consider adding virus scanning for production
3. **API Security**: Consider implementing API keys for external integrations
4. **Database**: Uses SQLite for development; consider PostgreSQL for production

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **Do not** create a public GitHub issue
2. Email security concerns to the maintainers
3. Provide detailed information about the vulnerability
4. Allow time for investigation and fix before public disclosure

## Security Updates

- Dependencies are regularly updated
- Security patches are applied promptly
- Monitor security advisories for Flask and related libraries

## Compliance Notes

- No sensitive personal data is stored beyond basic user profiles
- Food intake data is considered personal health information
- Users can delete their accounts and data
- No data is shared with third parties without consent

## Security Testing

Regular security testing should include:
- Static code analysis
- Dependency vulnerability scanning
- Penetration testing
- SQL injection testing
- XSS vulnerability testing
- CSRF protection testing

## Additional Security Measures to Consider

For production deployments, consider implementing:
- Web Application Firewall (WAF)
- DDoS protection
- API rate limiting per user
- Two-factor authentication
- Regular security audits
- Intrusion detection systems
- Database encryption at rest
- API endpoint monitoring

---

This security policy is regularly reviewed and updated. Last updated: January 2025