#!/usr/bin/env python3

import click
from backup_engine import BackupEngine
from database import Database
from encryption import Encryptor
from tabulate import tabulate
from datetime import datetime

backup_engine = BackupEngine()
db = Database()

@click.group()
def cli():
    """Ubuntu AutoBackup CLI Tool"""
    pass

@cli.command()
@click.option('--paths', '-p', help='Comma-separated paths to backup')
def backup(paths):
    """Perform a manual backup"""
    click.echo("Starting backup process...")
    
    paths_list = paths.split(',') if paths else None
    
    result = backup_engine.perform_backup(paths_list)
    
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
    """Generate a new encryption key"""
    key = Encryptor.generate_key()
    click.echo("\nGenerated Encryption Key:")
    click.echo(key)
    click.echo("\nAdd this to your .env file as ENCRYPTION_KEY")

if __name__ == '__main__':
    cli()
