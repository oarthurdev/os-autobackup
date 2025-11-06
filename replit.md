# Ubuntu AutoBackup

## Project Overview
A Python-based automated backup system for Ubuntu VPS servers with CLI and web dashboard interfaces. The system performs SSH-based backups, encrypts them with AES-256, and uploads them to Google Drive. Now features multi-host management through the web interface.

## Architecture
- **Backend**: Flask web server
- **Database**: SQLite for backup history, logs, and SSH host management
- **SSH**: Paramiko for remote VPS connections with encrypted credential storage
- **Encryption**: AES-256 using cryptography library for backup files
- **Credentials**: Fernet symmetric encryption for SSH credentials in database
- **Storage**: Google Drive API integration
- **CLI**: Click-based command-line tool

## Key Features
- **Multi-Host Management**: Add, edit, delete multiple SSH servers via web interface
- **Encrypted Credentials**: SSH credentials stored encrypted in database
- Manual backup execution via CLI or web interface
- SSH connection testing before backup
- Tar.gz compression of backup files
- AES-256 encryption of backups
- Google Drive upload with OAuth2
- Backup history tracking in SQLite
- Portuguese web interface
- English CLI interface
- Comprehensive logging system

## Project Structure
```
.
├── app.py                    # Flask web application
├── cli.py                    # Command-line interface
├── backup_engine.py          # Core backup logic
├── ssh_manager.py            # SSH connection manager
├── ssh_host_manager.py       # SSH host CRUD operations
├── credentials_manager.py    # Credential encryption/decryption
├── encryption.py             # AES encryption/decryption
├── drive_manager.py          # Google Drive API integration
├── database.py               # SQLite database operations
├── logger.py                 # Logging system
├── config.py                 # Configuration management
├── templates/                # HTML templates (Portuguese)
│   └── index.html
├── static/                   # CSS and JavaScript
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt          # Python dependencies
├── README.md                 # Full documentation
└── SECURITY.md               # Security guidelines
```

## Setup Requirements
1. Python 3.11
2. Google Drive API credentials (credentials.json)
3. SSH access to target VPS (password or key-based)
4. Encryption key for backups (generated via CLI)

## Environment Variables (Optional)
- `ENCRYPTION_KEY` - Base64 encryption key for backups
- `GOOGLE_DRIVE_FOLDER_ID` - Google Drive folder for uploads
- `GOOGLE_DRIVE_CREDENTIALS_FILE` - Path to credentials.json

**Note**: SSH server credentials are now managed through the web interface and stored encrypted in the database, not in environment variables.

## Recent Changes
- **Custom Toast Notification System** (2025-11-06)
  - Replaced native JavaScript `alert()` with modern toast notifications
  - Created custom notification component with 4 types: Success, Error, Warning, Info
  - Added CSS animations (slide-in/slide-out from top-right)
  - Fully responsive design with mobile adaptation
  - Dark/light theme support
  - Auto-dismiss with configurable duration
  - Non-blocking user experience
  - Added convenience functions: `showSuccess()`, `showError()`, `showWarning()`, `showInfo()`
  - Created documentation in TOAST_NOTIFICATIONS.md

- **Bug Fixes - Streaming Backup** (2025-11-06)
  - Fixed missing `download_and_encrypt_streaming()` method in SSHManager
  - Implemented streaming encryption methods in Encryptor class
  - Added progress tracking with callbacks
  - Fixed all LSP type errors (13 → 0)
  - Improved type annotations with Optional typing

- **SSH Host Management System** (2025-11-06)
  - Added ssh_hosts table to database with encrypted credentials
  - Created credentials_manager.py for Fernet encryption
  - Created ssh_host_manager.py for host CRUD operations
  - Updated backup_engine.py to support host_id parameter
  - Added web interface for managing SSH hosts
  - Updated CLI with `hosts` command to list configured servers
  - Removed dependency on VPS_* environment variables
  - SSH credentials now stored encrypted in database
  - Support for multiple SSH servers from single dashboard

- Initial project structure created (2025-11-06)
- Core backup engine implemented
- Flask web dashboard in Portuguese
- CLI tool in English
- Database models and logging system
- Security hardening (SSH host key verification, command injection prevention)

## Next Phase Features
- Automated daily scheduling (APScheduler/cron)
- Full system backup capabilities
- Real-time progress updates
- Backup retention policies
- Email notifications
- Backup rotation and cleanup

## User Preferences
- Web interface in Portuguese
- CLI in English
- Secure credential storage (encrypted in database)
- Multi-host management capability
