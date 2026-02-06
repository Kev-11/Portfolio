import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables FIRST before importing other modules
load_dotenv()

from backend import database, models, auth, backup

# Configure logging
log_handlers = [logging.StreamHandler()]
try:
    log_dir = Path("backend/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_handlers.insert(
        0,
        RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
    )
except Exception:
    # Serverless environments (e.g., Vercel) can be read-only.
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Portfolio API",
    description="Backend API for portfolio website with admin panel",
    version="1.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
# Strip whitespace from each origin
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS]
logger.info(f"CORS Origins configured: {CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        await database.init_db()
        # Verify database integrity on startup
        health = await database.verify_database_integrity()
        if health["healthy"]:
            logger.info("Application started successfully - database is healthy")
            
            # Auto-seed if database is empty
            try:
                projects = await database.get_all_projects()
                if len(projects) == 0:
                    logger.info("Database is empty - running auto-seed...")
                    import subprocess
                    import sys
                    subprocess.run([sys.executable, "seed_database.py"], check=True)
                    logger.info("Database auto-seeded successfully")
            except Exception as e:
                logger.warning(f"Auto-seed check failed: {e}")
        else:
            logger.warning(f"Application started but database health check failed: {health['message']}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't crash the app on serverless; health endpoint will show degraded.
        return


# Periodic checkpoint task
@app.on_event("startup")
async def start_periodic_checkpoint():
    """Start background task for periodic WAL checkpoints."""
    import asyncio
    
    async def checkpoint_task():
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                database.checkpoint_wal()
            except Exception as e:
                logger.error(f"Periodic checkpoint failed: {e}")
    
    asyncio.create_task(checkpoint_task())


# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint for deployment monitoring with database verification."""
    try:
        db_health = await database.verify_database_integrity()
        return {
            "status": "healthy" if db_health["healthy"] else "degraded",
            "message": "API is running",
            "database": db_health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "database": {"healthy": False, "message": str(e)},
            "timestamp": datetime.now().isoformat()
        }


# ==================== PUBLIC ENDPOINTS ====================

@app.get("/api/projects", response_model=List[models.Project])
async def get_projects(featured: Optional[bool] = None):
    """Get all projects, optionally filtered by featured status."""
    try:
        projects = await database.get_all_projects(featured_only=featured if featured else False)
        return projects
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")


@app.get("/api/experience", response_model=List[models.Experience])
async def get_experience():
    """Get all work experience entries."""
    try:
        experiences = await database.get_all_experience()
        return experiences
    except Exception as e:
        logger.error(f"Error fetching experience: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch experience")


@app.get("/api/skills", response_model=List[models.Skill])
async def get_skills():
    """Get all skills."""
    try:
        skills = await database.get_all_skills()
        return skills
    except Exception as e:
        logger.error(f"Error fetching skills: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch skills")


@app.get("/api/about")
async def get_about():
    """Get about section information."""
    try:
        about = await database.get_about()
        if not about:
            return {}  # Return empty object if no about section exists
        return about
    except Exception as e:
        logger.error(f"Error fetching about: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch about information")


@app.post("/api/contact", response_model=models.MessageResponse)
@limiter.limit("100/hour")
async def submit_contact(request: Request, contact: models.ContactRequest):
    """Submit a contact form (rate limited to 100 per hour per IP)."""
    try:
        # Get client IP
        client_ip = get_remote_address(request)
        
        # Additional rate limit check at database level
        recent_count = await database.get_recent_submissions_by_ip(client_ip, hours=1)
        if recent_count >= 100:
            raise HTTPException(
                status_code=429,
                detail="Too many contact submissions. Please try again later."
            )
        
        # Save to database first
        submission_id = await database.create_contact_submission(
            name=contact.name,
            email=contact.email,
            subject=contact.subject,
            message=contact.message,
            ip_address=client_ip
        )
        
        logger.info(f"Contact submission {submission_id} saved to database from {contact.email}")
        
        # Email sending is now handled by EmailJS on the frontend
        # This backend endpoint is only for database logging
        
        return models.MessageResponse(
            message="Thank you for your message! I'll get back to you soon.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        # Still return success to user even if email fails
        # (submission is saved in database)
        return models.MessageResponse(
            message="Thank you for your message! I'll get back to you soon.",
            success=True
        )


# ==================== ADMIN ENDPOINTS - PROJECTS ====================

@app.post("/api/admin/projects", response_model=models.Project)
async def create_project(project: models.ProjectCreate, admin: str = Depends(auth.verify_admin)):
    """Create a new project (admin only)."""
    try:
        project_id = await database.create_project(
            title=project.title,
            description=project.description,
            technologies=project.technologies,
            github_url=project.github_url,
            external_url=project.external_url,
            image_url=project.image_url,
            is_featured=project.is_featured,
            display_order=project.display_order
        )
        created_project = await database.get_project_by_id(project_id)
        logger.info(f"Admin {admin} created project: {project.title}")
        return created_project
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@app.put("/api/admin/projects/{project_id}", response_model=models.Project)
async def update_project(project_id: int, project: models.ProjectUpdate, 
                        admin: str = Depends(auth.verify_admin)):
    """Update a project (admin only)."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in project.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        success = await database.update_project(project_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        updated_project = await database.get_project_by_id(project_id)
        logger.info(f"Admin {admin} updated project ID {project_id}")
        return updated_project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@app.delete("/api/admin/projects/{project_id}", response_model=models.MessageResponse)
async def delete_project(project_id: int, admin: str = Depends(auth.verify_admin)):
    """Delete a project (admin only)."""
    try:
        success = await database.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        logger.info(f"Admin {admin} deleted project ID {project_id}")
        return models.MessageResponse(message="Project deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete project")


# ==================== ADMIN ENDPOINTS - EXPERIENCE ====================

@app.post("/api/admin/experience", response_model=models.Experience)
async def create_experience(experience: models.ExperienceCreate, 
                           admin: str = Depends(auth.verify_admin)):
    """Create a new experience entry (admin only)."""
    try:
        exp_id = await database.create_experience(
            company=experience.company,
            company_url=experience.company_url,
            role=experience.role,
            date_range=experience.date_range,
            responsibilities=experience.responsibilities,
            display_order=experience.display_order
        )
        created_exp = await database.get_experience_by_id(exp_id)
        logger.info(f"Admin {admin} created experience: {experience.company}")
        return created_exp
    except Exception as e:
        logger.error(f"Error creating experience: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create experience")


@app.put("/api/admin/experience/{experience_id}", response_model=models.Experience)
async def update_experience(experience_id: int, experience: models.ExperienceUpdate,
                           admin: str = Depends(auth.verify_admin)):
    """Update an experience entry (admin only)."""
    try:
        update_data = {k: v for k, v in experience.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        success = await database.update_experience(experience_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Experience not found")
        
        updated_exp = await database.get_experience_by_id(experience_id)
        logger.info(f"Admin {admin} updated experience ID {experience_id}")
        return updated_exp
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating experience: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update experience")


@app.delete("/api/admin/experience/{experience_id}", response_model=models.MessageResponse)
async def delete_experience(experience_id: int, admin: str = Depends(auth.verify_admin)):
    """Delete an experience entry (admin only)."""
    try:
        success = await database.delete_experience(experience_id)
        if not success:
            raise HTTPException(status_code=404, detail="Experience not found")
        
        logger.info(f"Admin {admin} deleted experience ID {experience_id}")
        return models.MessageResponse(message="Experience deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting experience: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete experience")


# ==================== ADMIN ENDPOINTS - SKILLS ====================

@app.post("/api/admin/skills", response_model=models.Skill)
async def create_skill(skill: models.SkillCreate, admin: str = Depends(auth.verify_admin)):
    """Create a new skill (admin only)."""
    try:
        skill_id = await database.create_skill(name=skill.name, category=skill.category)
        if skill_id == -1:
            raise HTTPException(status_code=400, detail="Skill already exists")
        
        created_skill = await database.get_skill_by_id(skill_id)
        logger.info(f"Admin {admin} created skill: {skill.name}")
        return created_skill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating skill: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create skill")


@app.put("/api/admin/skills/{skill_id}", response_model=models.Skill)
async def update_skill(skill_id: int, skill: models.SkillUpdate,
                      admin: str = Depends(auth.verify_admin)):
    """Update a skill (admin only)."""
    try:
        update_data = {k: v for k, v in skill.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        success = await database.update_skill(skill_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        updated_skill = await database.get_skill_by_id(skill_id)
        logger.info(f"Admin {admin} updated skill ID {skill_id}")
        return updated_skill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating skill: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update skill")


@app.delete("/api/admin/skills/{skill_id}", response_model=models.MessageResponse)
async def delete_skill(skill_id: int, admin: str = Depends(auth.verify_admin)):
    """Delete a skill (admin only)."""
    try:
        success = await database.delete_skill(skill_id)
        if not success:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        logger.info(f"Admin {admin} deleted skill ID {skill_id}")
        return models.MessageResponse(message="Skill deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting skill: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete skill")


# ==================== ADMIN ENDPOINTS - ABOUT ====================

@app.post("/api/admin/about", response_model=models.About)
async def update_about(about: models.AboutUpdate, admin: str = Depends(auth.verify_admin)):
    """Create or update about section (admin only)."""
    try:
        about_id = await database.create_or_update_about(
            bio=about.bio,
            current_company=about.current_company,
            current_role=about.current_role
        )
        updated_about = await database.get_about()
        logger.info(f"Admin {admin} updated about section")
        return updated_about
    except Exception as e:
        logger.error(f"Error updating about: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update about section")


# ==================== ADMIN ENDPOINTS - CONTACT SUBMISSIONS ====================

@app.get("/api/admin/contacts", response_model=List[models.ContactSubmission])
async def get_contact_submissions(admin: str = Depends(auth.verify_admin)):
    """Get all contact form submissions (admin only)."""
    try:
        submissions = await database.get_all_contact_submissions()
        return submissions
    except Exception as e:
        logger.error(f"Error fetching contact submissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch contact submissions")


@app.delete("/api/admin/contacts/{submission_id}")
async def delete_contact_submission(submission_id: int, admin: str = Depends(auth.verify_admin)):
    """Delete a contact form submission (admin only)."""
    try:
        deleted = await database.delete_contact_submission(submission_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Contact submission not found")
        return {"message": "Contact submission deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete contact submission")


# ==================== ADMIN ENDPOINTS - AUTH ====================

@app.get("/api/admin/verify")
async def verify_admin_credentials(admin: str = Depends(auth.verify_admin)):
    """Verify admin credentials (admin only)."""
    return {"authenticated": True, "username": admin}


# ==================== ADMIN ENDPOINTS - BACKUP ====================

@app.get("/api/admin/backup")
async def create_database_backup(admin: str = Depends(auth.verify_admin)):
    """Create a database backup and return download link (admin only)."""
    try:
        result = await backup.create_backup()
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Backup failed'))
        
        logger.info(f"Admin {admin} created database backup: {result['filename']}")
        
        return {
            "success": True,
            "message": "Backup created successfully",
            "filename": result['filename'],
            "size_kb": result['size_kb'],
            "download_url": f"/api/admin/backup/download/{result['filename']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create backup")


@app.get("/api/admin/backup/download/{filename}")
async def download_backup(filename: str, admin: str = Depends(auth.verify_admin)):
    """Download a backup file (admin only)."""
    try:
        backup_path = Path("backups") / filename
        
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Security check: ensure filename doesn't contain path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        logger.info(f"Admin {admin} downloaded backup: {filename}")
        
        return FileResponse(
            path=backup_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download backup")


@app.post("/api/admin/restore")
async def restore_database(file: UploadFile = File(...), admin: str = Depends(auth.verify_admin)):
    """Restore database from uploaded backup file (admin only).
    Completely replaces existing data and ensures it's properly saved."""
    try:
        # Validate file extension
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only .json files are allowed")
        
        # Read uploaded file
        content = await file.read()
        
        # Validate file is not empty
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Create backup of current database first
        current_backup = await backup.create_backup()
        logger.info(f"Created safety backup before restore: {current_backup['filename']}")
        
        # Step 1: Force checkpoint and close all connections
        logger.info("Checkpointing and closing all database connections...")
        database.checkpoint_wal()
        database.close_all_connections()
        
        # Step 2: Remove WAL and SHM files to prevent stale data
        logger.info("Removing WAL and SHM files...")
        database.cleanup_wal_files()
        
        # Step 3: Restore from JSON payload
        restore_result = await backup.restore_from_bytes(content)
        if not restore_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to restore database: {restore_result.get('error', 'Unknown error')}"
            )
        
        # Step 4: Verify database integrity
        health = await database.verify_database_integrity()
        if not health["healthy"]:
            logger.error(f"Restored database failed integrity check: {health['message']}")
            raise HTTPException(
                status_code=500, 
                detail=f"Database integrity check failed: {health['message']}"
            )
        
        logger.info(f"Admin {admin} restored database from {file.filename}")
        
        return {
            "success": True,
            "message": "Database restored successfully",
            "backup_created": current_backup['filename'],
            "integrity_check": "passed",
            "bytes_written": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restore database: {str(e)}")


@app.post("/api/admin/seed")
async def seed_database(admin: str = Depends(auth.verify_admin)):
    """Manually seed the database with sample data (admin only)."""
    try:
        import subprocess
        import sys
        
        # Run seed script
        result = subprocess.run(
            [sys.executable, "seed_database.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Admin {admin} manually seeded the database")
            return {
                "success": True,
                "message": "Database seeded successfully",
                "output": result.stdout
            }
        else:
            logger.error(f"Seeding failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Seeding failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Seeding timeout - operation took too long")
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to seed database")


@app.get("/api/admin/backups")
async def list_backups(admin: str = Depends(auth.verify_admin)):
    """List all available backups (admin only)."""
    try:
        backups_list = await backup.list_backups()
        return {"success": True, "backups": backups_list}
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list backups")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
