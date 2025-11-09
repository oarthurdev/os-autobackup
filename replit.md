# OS Backup

## Project Overview
A Python-based automated backup system for Ubuntu VPS servers with CLI and web dashboard interfaces. The system performs SSH-based backups, compresses them as ZIP files, and uploads them to Supabase Storage. Now features multi-host management through the web interface.

## Architecture
- **Backend**: Flask web server
- **Database**: SQLite for backup history, logs, SSH host management, and schedules
- **SSH**: Paramiko for remote VPS connections with encrypted credential storage
- **Credentials**: Fernet symmetric encryption for SSH credentials in database
- **Storage**: Supabase Storage for backup file storage
- **Compression**: ZIP format with optimized compression levels
- **Scheduler**: APScheduler for automated backup execution
- **CLI**: Click-based command-line tool

## Key Features
- **Automated Scheduling**: Configure automatic backups (daily, weekly, interval-based)
- **Multi-Host Management**: Add, edit, delete multiple SSH servers via web interface
- **Encrypted Credentials**: SSH credentials stored encrypted in database
- **Concurrency Control**: Thread-safe backup execution preventing overlapping runs
- Manual backup execution via CLI or web interface
- SSH connection testing before backup
- Backup restore/download from Supabase Storage
- ZIP compression of backup files with smart compression levels
- Supabase Storage integration for reliable cloud storage
- Backup history tracking in SQLite
- Portuguese web interface
- English CLI interface
- Comprehensive logging system

## Project Structure
```
.
├── app.py                      # Flask web application
├── cli.py                      # Command-line interface
├── backup_engine.py            # Core backup logic
├── ssh_manager.py              # SSH connection manager
├── ssh_host_manager.py         # SSH host CRUD operations
├── credentials_manager.py      # Credential encryption/decryption
├── supabase_storage_manager.py # Supabase Storage integration
├── scheduler.py                # Automated backup scheduler
├── database.py                 # SQLite database operations
├── logger.py                   # Logging system
├── config.py                   # Configuration management
├── templates/                  # HTML templates (Portuguese)
│   └── index.html
├── static/                     # CSS and JavaScript
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt            # Python dependencies
├── README.md                   # Full documentation
└── SECURITY.md                 # Security guidelines
```

## Setup Requirements
1. Python 3.11
2. Supabase project with Storage enabled
3. SSH access to target VPS (password or key-based)

## Environment Variables (Required)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `SUPABASE_BUCKET_NAME` - Storage bucket name (default: "backups")
- `ENCRYPTION_KEY` - Base64 encryption key for SSH credentials (optional, auto-generated)

**Note**: SSH server credentials are managed through the web interface and stored encrypted in the database.

## Recent Changes
- **Migration to Supabase Storage and ZIP Format** (2025-11-09)
  - **BREAKING CHANGE**: Migrated from Google Drive to Supabase Storage
  - Changed backup format from TAR.GZ to ZIP for better compatibility
  - Removed backup file encryption (backups are now stored as plain ZIP files)
  - Updated backup engine to use Supabase Storage API
  - Removed dependency on Google API libraries
  - Simplified backup/restore process (no decryption needed)
  - ZIP compression with smart level selection (faster for large files)
  - Maintained encryption for SSH credentials in database
  - Updated requirements.txt to include supabase library
  - Removed encryption.py and drive_manager.py modules
  - All existing functionality preserved with new storage backend
- **Automated Backup Scheduling System** (2025-11-07)
  - Implemented complete scheduling system using APScheduler
  - Support for multiple schedule types:
    * Daily: backup at specific time every day
    * Weekly: backup on specific day/time each week
    * Interval (hours): backup every N hours
    * Interval (days): backup every N days
  - New database table `schedules` with foreign key to SSH hosts
  - Thread-safe execution with global lock preventing concurrent backups
  - Centralized backup orchestration for manual and scheduled runs
  - Web interface for managing schedules (add, edit, delete, toggle active/inactive)
  - Persistent tracking of last_run and next_run timestamps
  - Real-time status updates showing when backups are scheduled/executed
  - Auto-loading of active schedules on server startup
  - Prevents overlapping backup executions
  - Full CRUD API for schedule management

- **Performance Optimizations for Large Files** (2025-11-07)
  - Implemented dynamic chunk sizing for files >1GB to accelerate transfers
  - Download chunks: 4MB for >1GB files, 8MB for >5GB files (was 1MB)
  - Encryption chunks: 1MB for >1GB files, 2MB for >5GB files (was 64KB)
  - Google Drive upload chunks: 5MB for >1GB, 10MB for >5GB (was 1MB)
  - Optimized tar compression with pigz -3 for >1GB files, pigz -1 for >5GB files
  - Added SFTP prefetching to reduce network latency on large transfers
  - Increased channel timeouts to 5 minutes for large file operations
  - Expected speed improvement: 2-4x faster for files >1GB

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
- Full system backup capabilities (entire server)
- Real-time progress updates with WebSocket
- Backup retention policies (auto-delete old backups)
- Email notifications on success/failure
- Backup rotation and cleanup automation
- Incremental backups
- Backup verification and integrity checks

## User Preferences
- Web interface in Portuguese
- CLI in English
- Secure credential storage (encrypted in database)
- Multi-host management capability
