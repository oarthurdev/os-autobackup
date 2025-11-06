# OS Backup

A comprehensive backup solution for Ubuntu VPS servers with both CLI and web interfaces.

## Features

- 🖥️ **Multi-Host Management** - Manage multiple SSH servers through web interface
- 🔒 **Secure SSH Connection** - Connect to remote VPS via SSH (password or key-based)
- 🔐 **Encrypted Credentials** - SSH credentials stored encrypted in database
- 📦 **Compression** - Create tar.gz archives of specified directories
- 🔐 **Encryption** - AES-256 encryption for backup files
- ☁️ **Cloud Storage** - Automatic upload to Google Drive
- 📊 **Web Dashboard** - Portuguese interface for monitoring and management
- 💻 **CLI Tool** - English command-line interface for manual operations
- 📝 **Logging** - Comprehensive logs for all operations
- 📈 **History Tracking** - SQLite database for backup history
- ⚡ **Performance Optimized** - Streaming encryption and fast compression for large files (>= 1GB)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Encryption Key

Generate a secure encryption key for backup files:

```bash
python cli.py genkey
```

Save this key securely - you'll need it to decrypt your backups.

### 3. Google Drive Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download credentials as `credentials.json`
6. Place `credentials.json` in the project root

### 4. Start the Web Interface

Start the Flask server:

```bash
python app.py
```

Access the dashboard at: `http://localhost:5000`

### 5. Add SSH Servers

Through the web interface:

1. Click "Adicionar Servidor" (Add Server)
2. Enter server details:
   - Name (e.g., "Production Server")
   - Host/IP address
   - SSH port (default: 22)
   - Username
   - Authentication type (Password or SSH Key)
   - Credentials (password or key path)
   - Backup paths (comma-separated)
3. Click "Salvar" (Save)
4. Test connection with the "Test" button

**Note**: SSH credentials are stored encrypted in the database for security.

### 6. CLI Tool

Available commands:

```bash
# List configured SSH hosts
python cli.py hosts

# Perform backup for a specific host
python cli.py backup --host-id 1

# Show backup history
python cli.py history --limit 20

# View logs for specific backup
python cli.py logs <backup_id>

# Check current status
python cli.py status

# Generate encryption key
python cli.py genkey
```

## Configuration

### SSH Server Management

SSH servers are now managed through the **web interface** instead of environment variables. This allows you to:

- Manage multiple servers from one dashboard
- Store credentials securely encrypted in the database
- Test connections before running backups
- Easily add, edit, or remove servers

### Optional Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ENCRYPTION_KEY` | Base64 encryption key for backups | Generate with `cli.py genkey` |
| `GOOGLE_DRIVE_FOLDER_ID` | Target folder ID in Google Drive | `1a2b3c4d5e6f7g8h9i` |
| `GOOGLE_DRIVE_CREDENTIALS_FILE` | Path to credentials.json | `credentials.json` |

## Web Interface (Portuguese)

The web dashboard provides:
- 🖥️ **SSH Server Management** - Add, edit, delete, and test SSH connections
- ✅ Current backup status
- 📋 Complete backup history
- 📄 Detailed logs for each backup
- ⬇️ Download links to Google Drive files
- ▶️ "Force Backup Now" button with server selection

## CLI Interface (English)

Command-line tool for:
- Listing configured SSH hosts
- Manual backup execution for specific hosts
- Viewing backup history
- Checking logs
- Monitoring status
- Generating encryption keys
- **Restoring (decrypting) backups**

### Restoring Backups

To restore an encrypted backup via CLI:

```bash
# Download the .encrypted file from Google Drive first, then:
python cli.py restore backup_20241106_120000.encrypted backup_restored.tar.gz

# Extract the restored backup:
tar -xzf backup_restored.tar.gz
```

Via Web Interface:
1. Go to "Histórico de Backups" (Backup History)
2. Click the **"Restaurar"** (Restore) button next to a successful backup
3. The decrypted `.tar.gz` file will be downloaded to your computer
4. Extract it using your preferred archive tool

## Security Notes

- **SSH credentials are encrypted** in the database using Fernet symmetric encryption
- Never commit `credentials.json` or `credentials.key`
- Store encryption keys securely (required to decrypt backups)
- Use SSH keys instead of passwords when possible
- Backup files are encrypted with AES-256 before upload
- Google Drive uses OAuth2 authentication
- SSH connections use strict host key verification (must add hosts to known_hosts)

## Troubleshooting

### SSH Connection Issues
- **Host key not found**: Run `ssh-keyscan -H <your_host> >> ~/.ssh/known_hosts`
- Test connection using the "Test" button in the web interface
- Verify SSH credentials are correct
- Check firewall rules
- Ensure SSH service is running on the remote server

### Google Drive Upload Issues
- Verify credentials.json is valid
- Check OAuth2 token (delete token.json to re-authenticate)
- Ensure Google Drive API is enabled

### Permission Errors
- Verify SSH user has read access to backup paths
- Check write permissions for temp directory

## License

MIT License
