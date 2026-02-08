# SECRETS ROTATION POLICY

## API Key Rotation Schedule

### Gemini API Key
- **Rotation Frequency**: Every 90 days
- **Process**:
  1. Generate new key in Google AI Studio
  2. Update in production environment (Railway/secrets manager)
  3. Monitor for errors (24 hours)
  4. Revoke old key

### Platform API Keys (Reddit, Twitter)
- **Rotation Frequency**: Every 180 days
- **Process**: Same as Gemini

### Internal API Keys (Client keys)
- **Rotation Frequency**: On compromise or every 365 days
- **Process**:
  1. Generate new key
  2. Provide to user
  3. Set 30-day grace period (both keys valid)
  4. Revoke old key after grace period

## Compromise Response
If any key is compromised:
1. Revoke immediately
2. Generate new key
3. Update all systems
4. Audit access logs
5. Notify stakeholders
