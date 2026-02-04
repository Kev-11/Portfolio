import os
import shutil
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "./backend/portfolio.db")
BACKUP_DIR = "./backups"


def create_backup() -> dict:
    """
    Create a timestamped backup of the database.
    
    Returns:
        Dictionary with backup information (filename, path, success status)
    """
    try:
        # Ensure backup directory exists
        Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
        
        # Check if database exists
        if not os.path.exists(DATABASE_PATH):
            logger.error(f"Database not found at {DATABASE_PATH}")
            return {
                "success": False,
                "error": "Database file not found",
                "filename": None,
                "path": None
            }
        
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"portfolio_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Copy database to backup location
        shutil.copy2(DATABASE_PATH, backup_path)
        
        # Get file size for reporting
        file_size = os.path.getsize(backup_path)
        file_size_kb = round(file_size / 1024, 2)
        
        logger.info(f"Database backup created: {backup_filename} ({file_size_kb} KB)")
        
        return {
            "success": True,
            "filename": backup_filename,
            "path": backup_path,
            "size_kb": file_size_kb,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to create database backup: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "filename": None,
            "path": None
        }


def list_backups() -> list:
    """
    List all available database backups.
    
    Returns:
        List of dictionaries with backup information
    """
    try:
        if not os.path.exists(BACKUP_DIR):
            return []
        
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith('.db'):
                filepath = os.path.join(BACKUP_DIR, filename)
                file_size = os.path.getsize(filepath)
                file_size_kb = round(file_size / 1024, 2)
                modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                backups.append({
                    "filename": filename,
                    "size_kb": file_size_kb,
                    "created_at": modified_time.strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
        
    except Exception as e:
        logger.error(f"Failed to list backups: {str(e)}")
        return []


def restore_backup(backup_filename: str) -> dict:
    """
    Restore database from a backup file.
    
    Args:
        backup_filename: Name of the backup file to restore
    
    Returns:
        Dictionary with restore status
    """
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Check if backup exists
        if not os.path.exists(backup_path):
            return {
                "success": False,
                "error": "Backup file not found"
            }
        
        # Create a backup of current database before restoring
        current_backup = create_backup()
        if not current_backup["success"]:
            logger.warning("Failed to create safety backup before restore")
        
        # Restore the backup
        shutil.copy2(backup_path, DATABASE_PATH)
        
        logger.info(f"Database restored from backup: {backup_filename}")
        
        return {
            "success": True,
            "message": f"Database restored from {backup_filename}",
            "safety_backup": current_backup.get("filename")
        }
        
    except Exception as e:
        logger.error(f"Failed to restore backup: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def delete_old_backups(keep_count: int = 10) -> dict:
    """
    Delete old backups, keeping only the most recent ones.
    
    Args:
        keep_count: Number of most recent backups to keep
    
    Returns:
        Dictionary with deletion results
    """
    try:
        backups = list_backups()
        
        if len(backups) <= keep_count:
            return {
                "success": True,
                "deleted_count": 0,
                "message": f"Only {len(backups)} backups exist, keeping all"
            }
        
        # Delete older backups
        to_delete = backups[keep_count:]
        deleted_count = 0
        
        for backup in to_delete:
            filepath = os.path.join(BACKUP_DIR, backup['filename'])
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete backup {backup['filename']}: {str(e)}")
        
        logger.info(f"Deleted {deleted_count} old backup(s), kept {keep_count} most recent")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "kept_count": keep_count
        }
        
    except Exception as e:
        logger.error(f"Failed to delete old backups: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
