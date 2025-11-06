# Security Guide

## Critical Security Requirements

### 1. SSH Host Key Verification

The system uses **strict SSH host key verification** to prevent man-in-the-middle attacks. Before running backups:

```bash
ssh-keyscan -H your_vps_host >> ~/.ssh/known_hosts
```

Or manually SSH into the server once to accept the host key:

```bash
ssh user@your_vps_host
```

This ensures the SSH connection verifies the server's identity.

### 2. Encryption Key Management

**IMPORTANT**: An encryption key is **required** for backups. The system will fail if no key is configured.

Generate a secure encryption key:

```bash
python cli.py genkey
```

Add the generated key to your environment:
- Create a `.env` file from `.env.example`
- Set `ENCRYPTION_KEY=<generated_key>`

**Security Notes:**
- Never commit the encryption key to version control
- Store the key securely (password manager, secrets manager, etc.)
- Without the key, encrypted backups **cannot be decrypted**
- Rotate keys periodically and re-encrypt existing backups

### 3. Path Validation

All backup paths are validated before execution to prevent command injection:
- Paths cannot contain `..` (directory traversal)
- Paths cannot start with `-` (option injection)
- All paths are properly shell-escaped using `shlex.quote()`

### 4. Google Drive Authentication

OAuth2 is used for Google Drive API:
- Download `credentials.json` from Google Cloud Console
- First run triggers OAuth flow and creates `token.json`
- Never commit `credentials.json` or `token.json` to version control

### 5. SSH Authentication Best Practices

**Recommended**: Use SSH keys instead of passwords

```bash
ssh-keygen -t ed25519 -C "backup-system"
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@vps_host
```

Set in `.env`:
```
VPS_KEY_PATH=/home/user/.ssh/id_ed25519
VPS_PASSWORD=
```

### 6. Environment Variable Security

Create `.env` file with restricted permissions:

```bash
cp .env.example .env
chmod 600 .env
```

Never expose environment variables in logs or error messages.

### 7. Production Deployment

For production use:
- Use a proper WSGI server (Gunicorn, uWSGI) instead of Flask development server
- Enable HTTPS/TLS for web interface
- Restrict network access to trusted IPs
- Implement rate limiting on backup endpoints
- Monitor and audit all backup operations
- Set up backup retention policies
- Test backup restoration regularly

## Security Checklist

Before running in production:

- [ ] SSH host keys configured in `~/.ssh/known_hosts`
- [ ] Encryption key generated and stored securely
- [ ] SSH key-based authentication configured
- [ ] Google Drive credentials secured
- [ ] `.env` file has restricted permissions (600)
- [ ] Firewall rules configured
- [ ] Backup restoration tested successfully
- [ ] Monitoring and alerting configured
