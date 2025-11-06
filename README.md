# Ubuntu AutoBackup

A comprehensive backup solution for Ubuntu VPS servers with both CLI and web interfaces.

## Features

- 🔒 **Secure SSH Connection** - Connect to remote VPS via SSH (password or key-based)
- 📦 **Compression** - Create tar.gz archives of specified directories
- 🔐 **Encryption** - AES-256 encryption for backup files
- ☁️ **Cloud Storage** - Automatic upload to Google Drive
- 📊 **Web Dashboard** - Portuguese interface for monitoring and management
- 💻 **CLI Tool** - English command-line interface for manual operations
- 📝 **Logging** - Comprehensive logs for all operations
- 📈 **History Tracking** - SQLite database for backup history

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

Required configuration:
- VPS connection details (SSH)
- Backup paths to archive
- Encryption key (generate with: `python cli.py genkey`)
- Google Drive API credentials

### 3. Google Drive Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download credentials as `credentials.json`
6. Place `credentials.json` in the project root

### 4. Web Interface

Start the Flask server:

```bash
python app.py
```

Access the dashboard at: `http://localhost:5000`

### 5. CLI Tool

Available commands:

```bash
# Perform manual backup
python cli.py backup

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

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VPS_HOST` | VPS IP or hostname | `192.168.1.100` |
| `VPS_PORT` | SSH port | `22` |
| `VPS_USERNAME` | SSH username | `root` |
| `VPS_PASSWORD` | SSH password (if not using key) | `your_password` |
| `VPS_KEY_PATH` | Path to SSH private key | `/path/to/key.pem` |
| `BACKUP_PATHS` | Comma-separated paths to backup | `/home,/etc,/var/www` |
| `ENCRYPTION_KEY` | Base64 encryption key | Generate with `cli.py genkey` |
| `GOOGLE_DRIVE_FOLDER_ID` | Target folder ID in Google Drive | `1a2b3c4d5e6f7g8h9i` |

## Web Interface (Portuguese)

The web dashboard provides:
- ✅ Current backup status
- 📋 Complete backup history
- 📄 Detailed logs for each backup
- ⬇️ Download links to Google Drive files
- ▶️ "Force Backup Now" button

## CLI Interface (English)

Command-line tool for:
- Manual backup execution
- Viewing backup history
- Checking logs
- Monitoring status
- Generating encryption keys

## Security Notes

- Never commit `.env` file or `credentials.json`
- Store encryption keys securely
- Use SSH keys instead of passwords when possible
- Backup files are encrypted before upload
- Google Drive uses OAuth2 authentication

## Troubleshooting

### SSH Connection Issues
- Verify VPS hostname and credentials
- Check firewall rules
- Ensure SSH service is running

### Google Drive Upload Issues
- Verify credentials.json is valid
- Check OAuth2 token (delete token.json to re-authenticate)
- Ensure Google Drive API is enabled

### Permission Errors
- Verify SSH user has read access to backup paths
- Check write permissions for temp directory

## License

MIT License
