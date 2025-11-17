# Login and Authentication Issues - Quick Answer

## Summary
Users experiencing authentication failures with SSO integration. Error code 401 returned after recent security update.

## Problem
Single Sign-On (SSO) authentication is failing with HTTP 401 Unauthorized errors. Issue began following a recent security patch deployment. Affects users across multiple identity providers including Okta, Azure AD, and Google Workspace.

## Root Causes
- OAuth token validation endpoint configuration mismatch
- TLS certificate pinning changed in security update
- Legacy OAuth2 scopes no longer accepted by providers

## Solution Steps

### Step 1: Verify Configuration
1. Check OAuth2 provider settings in admin dashboard
2. Confirm redirect URIs match provider configuration exactly
3. Verify client ID and secret are correctly set

### Step 2: Update Trust Certificates
1. Navigate to Security → Certificate Management
2. Re-import provider trust certificates
3. Clear certificate cache

### Step 3: Update OAuth Scopes
1. Go to Authentication → OAuth Configuration
2. Update scope list to include: `openid profile email`
3. Save changes and restart auth service

## Workaround
Users can temporarily use username/password authentication while SSO is being repaired. Requires manual password reset at `https://app.example.com/forgot-password`

## Prevention
- Enable certificate monitoring alerts
- Test SSO integration in staging before production deployments
- Document all OAuth provider configurations

## Related Articles
- [OAuth2 Configuration Guide](https://docs.example.com/oauth2)
- [SSO Troubleshooting](https://docs.example.com/sso-troubleshooting)
- [Security Update Changelog](https://docs.example.com/security-updates)

## Support
If issues persist after following these steps, contact support with:
- Error logs from `/var/log/auth.log`
- OAuth provider error details
- Last known working configuration

---
*Generated on 2025-11-17 | Category: Authentication | Priority: High*
