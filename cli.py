#!/usr/bin/env python3

import click
import os
from backup_engine import BackupEngine
from database import Database
from encryption import Encryptor
from ssh_host_manager import SSHHostManager
from tabulate import tabulate
from datetime import datetime

backup_engine = BackupEngine()
db = Database()
ssh_host_manager = SSHHostManager()

@click.group()
def cli():
    """OS Backup CLI Tool"""
    pass

@cli.command()
@click.option('--host-id', '-h', type=int, help='SSH host ID to backup')
@click.option('--paths', '-p', help='Comma-separated paths to backup')
def backup(host_id, paths):
    """Perform a manual backup"""
    if host_id:
        click.echo(f"Starting backup for Host ID {host_id}...")
    else:
        click.echo("Starting backup process...")

    paths_list = paths.split(',') if paths else None

    result = backup_engine.perform_backup(host_id=host_id, paths=paths_list)

    if result['success']:
        click.echo(f"\n✓ Backup completed successfully!")
        click.echo(f"  Backup ID: {result['backup_id']}")
        click.echo(f"  File: {result['file_name']}")
        click.echo(f"  Size: {result['file_size']:,} bytes")
        click.echo(f"  Duration: {result['duration']:.2f} seconds")
    else:
        click.echo(f"\n✗ Backup failed!")
        click.echo(f"  Error: {result['error']}")

@cli.command()
@click.option('--limit', '-l', default=10, help='Number of backups to show')
def history(limit):
    """Show backup history"""
    backups = backup_engine.get_backup_history(limit)

    if not backups:
        click.echo("No backups found.")
        return

    table_data = []
    for backup in backups:
        table_data.append([
            backup['id'],
            backup['timestamp'][:19],
            backup['status'],
            backup['file_name'] or 'N/A',
            f"{backup['file_size']:,}" if backup['file_size'] else 'N/A',
            f"{backup['duration_seconds']:.2f}s" if backup['duration_seconds'] else 'N/A'
        ])

    headers = ['ID', 'Timestamp', 'Status', 'File Name', 'Size', 'Duration']
    click.echo("\nBackup History:")
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

@cli.command()
@click.argument('backup_id', type=int)
def logs(backup_id):
    """Show logs for a specific backup"""
    backup_logs = backup_engine.get_backup_logs(backup_id)

    if not backup_logs:
        click.echo(f"No logs found for backup ID {backup_id}")
        return

    click.echo(f"\nLogs for Backup ID {backup_id}:")
    click.echo("-" * 80)

    for log in backup_logs:
        timestamp = log['timestamp'][:19]
        level = log['level'].ljust(7)
        message = log['message']
        click.echo(f"{timestamp} [{level}] {message}")

@cli.command()
def status():
    """Show current backup status"""
    latest = db.get_latest_backup()

    if not latest:
        click.echo("No backups found.")
        return

    click.echo("\nLatest Backup:")
    click.echo(f"  ID: {latest['id']}")
    click.echo(f"  Timestamp: {latest['timestamp']}")
    click.echo(f"  Status: {latest['status']}")

    if latest['status'] == 'SUCCESS':
        click.echo(f"  File: {latest['file_name']}")
        click.echo(f"  Size: {latest['file_size']:,} bytes")
        click.echo(f"  Duration: {latest['duration_seconds']:.2f} seconds")
    elif latest['status'] == 'FAILED':
        click.echo(f"  Error: {latest['error_message']}")

@cli.command()
def genkey():
    """Generate a new encryption key."""
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    print(f"\nGenerated encryption key:")
    print(key.decode())
    print(f"\nAdd this to your .env file as:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print()

@cli.command()
def reset_drive():
    """Reset Google Drive authentication (delete token.json)."""
    import os
    from config import Config

    token_file = Config.GOOGLE_DRIVE_TOKEN_FILE

    if os.path.exists(token_file):
        os.remove(token_file)
        click.echo(f"✓ Token file deleted: {token_file}")
        click.echo("Next backup will require re-authentication with Google Drive.")
    else:
        click.echo(f"Token file not found: {token_file}")
        click.echo("No action needed.")

@cli.command()
@click.argument('encrypted_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def restore(encrypted_file, output_file):
    """Restore (decrypt) a backup file

    Example: python cli.py restore backup_20241106.encrypted backup_restored.tar.gz
    """
    try:
        encryptor = Encryptor()

        click.echo(f"Decrypting {encrypted_file}...")
        encryptor.decrypt_file(encrypted_file, output_file)

        file_size = os.path.getsize(output_file)
        click.echo(f"\n✓ Backup restored successfully!")
        click.echo(f"  Output file: {output_file}")
        click.echo(f"  Size: {file_size:,} bytes")
        click.echo(f"\nTo extract: tar -xzf {output_file}")

    except Exception as e:
        click.echo(f"\n✗ Restore failed!")
        click.echo(f"  Error: {str(e)}")
        if os.path.exists(output_file):
            os.remove(output_file)

@cli.command()
def hosts():
    """List all SSH hosts"""
    all_hosts = ssh_host_manager.get_all_hosts()

    if not all_hosts:
        click.echo("No SSH hosts configured.")
        click.echo("\nUse the web interface to add SSH hosts or configure them in .env file.")
        return

    table_data = []
    for host in all_hosts:
        status = 'Connected' if host.get('connection_status', '').startswith('SUCCESS') else \
                'Failed' if host.get('connection_status', '').startswith('FAILED') else \
                'Not tested'

        auth_type = 'Password' if host['auth_type'] == 'password' else 'SSH Key'

        table_data.append([
            host['id'],
            host['name'],
            host['host'],
            host['port'],
            host['username'],
            auth_type,
            status
        ])

    headers = ['ID', 'Name', 'Host', 'Port', 'Username', 'Auth', 'Status']
    click.echo("\nConfigured SSH Hosts:")
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
    click.echo(f"\nTo backup a specific host, use: python cli.py backup --host-id <ID>")

if __name__ == '__main__':
    cli()