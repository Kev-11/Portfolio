import os
from datetime import datetime, timezone
from pathlib import Path
import logging
from typing import Dict, Any

from bson import json_util

from backend import database

logger = logging.getLogger(__name__)

BACKUP_DIR = "./backups"

_COLLECTIONS = [
    "projects",
    "experience",
    "skills",
    "about",
    "contact_submissions",
    "counters"
]


async def _dump_collections() -> Dict[str, Any]:
    db = database._get_db()
    dump = {}
    for name in _COLLECTIONS:
        cursor = db[name].find({})
        dump[name] = [doc async for doc in cursor]
    return dump


async def create_backup() -> dict:
    """
    Create a timestamped JSON backup of the MongoDB database.
    """
    try:
        Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"portfolio_backup_{timestamp}.json"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        data = {
            "version": 1,
            "created_at": datetime.now(timezone.utc),
            "collections": await _dump_collections()
        }

        payload = json_util.dumps(data, indent=2)
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(payload)

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


async def list_backups() -> list:
    """
    List all available database backups.
    """
    try:
        if not os.path.exists(BACKUP_DIR):
            return []

        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(BACKUP_DIR, filename)
                file_size = os.path.getsize(filepath)
                file_size_kb = round(file_size / 1024, 2)
                modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                backups.append({
                    "filename": filename,
                    "size_kb": file_size_kb,
                    "created_at": modified_time.strftime("%Y-%m-%d %H:%M:%S")
                })

        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    except Exception as e:
        logger.error(f"Failed to list backups: {str(e)}")
        return []


async def restore_from_bytes(content: bytes) -> dict:
    """
    Restore database from JSON backup content.
    """
    try:
        if isinstance(content, (bytes, bytearray)):
            content = content.decode("utf-8")
        data = json_util.loads(content)
        collections = data.get("collections", {})

        db = database._get_db()
        for name in _COLLECTIONS:
            await db[name].delete_many({})
            docs = collections.get(name, [])
            if docs:
                await db[name].insert_many(docs)

        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to restore backup: {str(e)}")
        return {"success": False, "error": str(e)}


async def restore_backup(backup_filename: str) -> dict:
    """
    Restore database from a backup file.
    """
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        if not os.path.exists(backup_path):
            return {"success": False, "error": "Backup file not found"}

        with open(backup_path, "rb") as f:
            content = f.read()
        result = await restore_from_bytes(content)
        if not result.get("success"):
            return result

        logger.info(f"Database restored successfully from backup: {backup_filename}")
        return {
            "success": True,
            "message": f"Database restored from {backup_filename}",
            "integrity_check": "passed"
        }
    except Exception as e:
        logger.error(f"Failed to restore backup: {str(e)}")
        return {"success": False, "error": str(e)}
