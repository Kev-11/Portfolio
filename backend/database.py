import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "portfolio")

_client: Optional[AsyncIOMotorClient] = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def _get_db():
    return _get_client()[MONGODB_DB]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.astimezone(timezone.utc).isoformat()


def _serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if "image_urls" not in doc and doc.get("image_url"):
        doc["image_urls"] = [doc["image_url"]]
    if "is_featured" in doc:
        doc["is_featured"] = bool(doc["is_featured"])
    for key in ("created_at", "updated_at", "email_sent_at"):
        if key in doc:
            doc[key] = _to_iso(doc.get(key))
    return doc


async def _get_next_sequence(name: str) -> int:
    db = _get_db()
    result = await db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(result["seq"])


async def init_db():
    """Initialize MongoDB collections and indexes."""
    db = _get_db()
    try:
        await db.projects.create_index([("display_order", ASCENDING), ("created_at", DESCENDING)])
        await db.experience.create_index([("display_order", ASCENDING), ("created_at", DESCENDING)])
        await db.skills.create_index([("category", ASCENDING), ("name", ASCENDING)])
        await db.skills.create_index([("name", ASCENDING)], unique=True)
        await db.contact_submissions.create_index([("created_at", ASCENDING)])
        await db.contact_submissions.create_index([("ip_address", ASCENDING), ("created_at", ASCENDING)])
        await db.about.create_index([("updated_at", ASCENDING)])
        logger.info("MongoDB indexes ensured")
    except PyMongoError as e:
        logger.error(f"MongoDB init failed: {e}")
        raise


async def verify_database_integrity() -> Dict[str, Any]:
    try:
        client = _get_client()
        await client.admin.command("ping")
        db = _get_db()
        await db.projects.find_one()
        return {"healthy": True, "status": "ok", "message": "Database is healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"healthy": False, "status": "error", "message": str(e)}


def close_all_connections():
    """Close MongoDB client connections."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def checkpoint_wal():
    """No-op for MongoDB compatibility."""
    return None


def cleanup_wal_files():
    """No-op for MongoDB compatibility."""
    return None


# ==================== PROJECTS CRUD ====================

async def create_project(title: str, description: str, technologies: List[str],
                         github_url: Optional[str] = None, external_url: Optional[str] = None,
                         image_url: Optional[str] = None, image_urls: Optional[List[str]] = None,
                         is_featured: bool = False, display_order: int = 0) -> int:
    db = _get_db()
    if image_url and not image_urls:
        image_urls = [image_url]
    project_id = await _get_next_sequence("projects")
    doc = {
        "id": project_id,
        "title": title,
        "description": description,
        "technologies": technologies,
        "github_url": github_url,
        "external_url": external_url,
        "image_url": image_url,
        "image_urls": image_urls or [],
        "is_featured": bool(is_featured),
        "display_order": int(display_order),
        "created_at": _now_utc()
    }
    await db.projects.insert_one(doc)
    return project_id


async def get_all_projects(featured_only: bool = False) -> List[Dict[str, Any]]:
    db = _get_db()
    query = {"is_featured": True} if featured_only else {}
    cursor = db.projects.find(query).sort([("display_order", ASCENDING), ("created_at", DESCENDING)])
    projects = [ _serialize_document(doc) async for doc in cursor ]
    return projects


async def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    db = _get_db()
    doc = await db.projects.find_one({"id": int(project_id)})
    return _serialize_document(doc) if doc else None


async def update_project(project_id: int, **kwargs) -> bool:
    db = _get_db()
    if "technologies" in kwargs and isinstance(kwargs["technologies"], list):
        kwargs["technologies"] = kwargs["technologies"]
    if "image_urls" in kwargs and isinstance(kwargs["image_urls"], list):
        kwargs["image_urls"] = kwargs["image_urls"]
    if not kwargs:
        return False
    result = await db.projects.update_one({"id": int(project_id)}, {"$set": kwargs})
    return result.modified_count > 0


async def delete_project(project_id: int) -> bool:
    db = _get_db()
    result = await db.projects.delete_one({"id": int(project_id)})
    return result.deleted_count > 0


# ==================== EXPERIENCE CRUD ====================

async def create_experience(company: str, role: str, date_range: str,
                            responsibilities: List[str], company_url: Optional[str] = None,
                            display_order: int = 0) -> int:
    db = _get_db()
    exp_id = await _get_next_sequence("experience")
    doc = {
        "id": exp_id,
        "company": company,
        "company_url": company_url,
        "role": role,
        "date_range": date_range,
        "responsibilities": responsibilities,
        "display_order": int(display_order),
        "created_at": _now_utc()
    }
    await db.experience.insert_one(doc)
    return exp_id


async def get_all_experience() -> List[Dict[str, Any]]:
    db = _get_db()
    cursor = db.experience.find({}).sort([("display_order", ASCENDING), ("created_at", DESCENDING)])
    experiences = [_serialize_document(doc) async for doc in cursor]
    return experiences


async def get_experience_by_id(experience_id: int) -> Optional[Dict[str, Any]]:
    db = _get_db()
    doc = await db.experience.find_one({"id": int(experience_id)})
    return _serialize_document(doc) if doc else None


async def update_experience(experience_id: int, **kwargs) -> bool:
    db = _get_db()
    if not kwargs:
        return False
    result = await db.experience.update_one({"id": int(experience_id)}, {"$set": kwargs})
    return result.modified_count > 0


async def delete_experience(experience_id: int) -> bool:
    db = _get_db()
    result = await db.experience.delete_one({"id": int(experience_id)})
    return result.deleted_count > 0


# ==================== SKILLS CRUD ====================

async def create_skill(name: str, category: Optional[str] = None) -> int:
    db = _get_db()
    skill_id = await _get_next_sequence("skills")
    doc = {
        "id": skill_id,
        "name": name,
        "category": category,
        "created_at": _now_utc()
    }
    try:
        await db.skills.insert_one(doc)
        return skill_id
    except Exception:
        return -1


async def get_all_skills() -> List[Dict[str, Any]]:
    db = _get_db()
    cursor = db.skills.find({}).sort([("category", ASCENDING), ("name", ASCENDING)])
    skills = [_serialize_document(doc) async for doc in cursor]
    return skills


async def get_skill_by_id(skill_id: int) -> Optional[Dict[str, Any]]:
    db = _get_db()
    doc = await db.skills.find_one({"id": int(skill_id)})
    return _serialize_document(doc) if doc else None


async def update_skill(skill_id: int, **kwargs) -> bool:
    db = _get_db()
    if not kwargs:
        return False
    result = await db.skills.update_one({"id": int(skill_id)}, {"$set": kwargs})
    return result.modified_count > 0


async def delete_skill(skill_id: int) -> bool:
    db = _get_db()
    result = await db.skills.delete_one({"id": int(skill_id)})
    return result.deleted_count > 0


# ==================== ABOUT CRUD ====================

async def create_or_update_about(bio: str, current_company: Optional[str] = None,
                                 current_role: Optional[str] = None) -> int:
    db = _get_db()
    existing = await db.about.find_one({})
    if existing:
        await db.about.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "bio": bio,
                "current_company": current_company,
                "current_role": current_role,
                "updated_at": _now_utc()
            }}
        )
        return int(existing.get("id", 1))
    about_id = await _get_next_sequence("about")
    doc = {
        "id": about_id,
        "bio": bio,
        "current_company": current_company,
        "current_role": current_role,
        "updated_at": _now_utc()
    }
    await db.about.insert_one(doc)
    return about_id


async def get_about() -> Optional[Dict[str, Any]]:
    db = _get_db()
    doc = await db.about.find_one({})
    return _serialize_document(doc) if doc else None


# ==================== CONTACT SUBMISSIONS CRUD ====================

async def create_contact_submission(name: str, email: str, message: str,
                                    subject: Optional[str] = None,
                                    ip_address: Optional[str] = None) -> int:
    db = _get_db()
    submission_id = await _get_next_sequence("contact_submissions")
    doc = {
        "id": submission_id,
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "ip_address": ip_address,
        "email_sent": False,
        "email_sent_at": None,
        "created_at": _now_utc()
    }
    await db.contact_submissions.insert_one(doc)
    return submission_id


async def mark_email_sent(submission_id: int) -> bool:
    db = _get_db()
    result = await db.contact_submissions.update_one(
        {"id": int(submission_id)},
        {"$set": {"email_sent": True, "email_sent_at": _now_utc()}}
    )
    return result.modified_count > 0


async def get_all_contact_submissions() -> List[Dict[str, Any]]:
    db = _get_db()
    cursor = db.contact_submissions.find({}).sort([("created_at", DESCENDING)])
    submissions = [_serialize_document(doc) async for doc in cursor]
    return submissions


async def delete_contact_submission(submission_id: int) -> bool:
    db = _get_db()
    result = await db.contact_submissions.delete_one({"id": int(submission_id)})
    return result.deleted_count > 0


async def get_recent_submissions_by_ip(ip_address: str, hours: int = 1) -> int:
    db = _get_db()
    cutoff = _now_utc()
    cutoff = cutoff.replace(tzinfo=timezone.utc)
    cutoff = cutoff - timedelta(hours=hours)
    count = await db.contact_submissions.count_documents({
        "ip_address": ip_address,
        "created_at": {"$gt": cutoff}
    })
    return int(count)


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
