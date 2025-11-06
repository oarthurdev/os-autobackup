# Ubuntu AutoBackup

## Project Overview
A Python-based automated backup system for Ubuntu VPS servers with CLI and web dashboard interfaces. The system performs SSH-based backups, encrypts them with AES-256, and uploads them to Google Drive.

## Architecture
- **Backend**: Flask web server
- **Database**: SQLite for backup history and logs
- **SSH**: Paramiko for remote VPS connections
- **Encryption**: AES-256 using cryptography library
- **Storage**: Google Drive API integration
- **CLI**: Click-based command-line tool

## Key Features
- Manual backup execution via CLI or web interface
- SSH connection to remote VPS
- Tar.gz compression of backup files
- AES-256 encryption
- Google Drive upload with OAuth2
- Backup history tracking in SQLite
- Portuguese web interface
- English CLI interface
- Comprehensive logging system

## Project Structure
```
.
├── app.py                  # Flask web application
├── cli.py                  # Command-line interface
├── backup_engine.py        # Core backup logic
├── ssh_manager.py          # SSH connection manager
├── encryption.py           # AES encryption/decryption
├── drive_manager.py        # Google Drive API integration
├── database.py             # SQLite database operations
├── logger.py               # Logging system
├── config.py               # Configuration management
├── templates/              # HTML templates (Portuguese)
│   └── index.html
├── static/                 # CSS and JavaScript
│   ├── css/style.css
│   └── js/app.js
└── requirements.txt        # Python dependencies
```

## Setup Requirements
1. Python 3.11
2. Google Drive API credentials (credentials.json)
3. SSH access to target VPS (password or key-based)
4. Environment variables (.env file)

## Environment Variables
- VPS connection details (host, port, username, password/key)
- Backup paths
- Encryption key
- Google Drive credentials
- Flask secret key

## Recent Changes
- Initial project structure created (2025-11-06)
- Core backup engine implemented
- Flask web dashboard in Portuguese
- CLI tool in English
- Database models and logging system

## Next Phase Features
- Automated daily scheduling (APScheduler/cron)
- Full system backup capabilities
- Real-time progress updates
- Backup retention policies
- Email notifications
