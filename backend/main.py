import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables FIRST before importing other modules
load_dotenv()

from backend import database, models, auth, email_service, backup

# Configure logging
log_dir = Path("backend/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
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

# Mount static files for uploaded images
static_dir = Path("frontend/assets/images")
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(static_dir)), name="uploads")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        database.init_db()
        # Verify database integrity on startup
        health = database.verify_database_integrity()
        if health["healthy"]:
            logger.info("Application started successfully - database is healthy")
        else:
            logger.warning(f"Application started but database health check failed: {health['message']}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


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
        db_health = database.verify_database_integrity()
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
        projects = database.get_all_projects(featured_only=featured if featured else False)
        return projects
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")


@app.get("/api/experience", response_model=List[models.Experience])
async def get_experience():
    """Get all work experience entries."""
    try:
        experiences = database.get_all_experience()
        return experiences
    except Exception as e:
        logger.error(f"Error fetching experience: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch experience")


@app.get("/api/skills", response_model=List[models.Skill])
async def get_skills():
    """Get all skills."""
    try:
        skills = database.get_all_skills()
        return skills
    except Exception as e:
        logger.error(f"Error fetching skills: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch skills")


@app.get("/api/about")
async def get_about():
    """Get about section information."""
    try:
        about = database.get_about()
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
        recent_count = database.get_recent_submissions_by_ip(client_ip, hours=1)
        if recent_count >= 100:
            raise HTTPException(
                status_code=429,
                detail="Too many contact submissions. Please try again later."
            )
        
        # Save to database first
        submission_id = database.create_contact_submission(
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
        project_id = database.create_project(
            title=project.title,
            description=project.description,
            technologies=project.technologies,
            github_url=project.github_url,
            external_url=project.external_url,
            image_url=project.image_url,
            is_featured=project.is_featured,
            display_order=project.display_order
        )
        created_project = database.get_project_by_id(project_id)
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
        
        success = database.update_project(project_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        updated_project = database.get_project_by_id(project_id)
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
        success = database.delete_project(project_id)
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
        exp_id = database.create_experience(
            company=experience.company,
            company_url=experience.company_url,
            role=experience.role,
            date_range=experience.date_range,
            responsibilities=experience.responsibilities,
            display_order=experience.display_order
        )
        created_exp = database.get_experience_by_id(exp_id)
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
        
        success = database.update_experience(experience_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Experience not found")
        
        updated_exp = database.get_experience_by_id(experience_id)
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
        success = database.delete_experience(experience_id)
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
        skill_id = database.create_skill(name=skill.name, category=skill.category)
        if skill_id == -1:
            raise HTTPException(status_code=400, detail="Skill already exists")
        
        created_skill = database.get_skill_by_id(skill_id)
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
        
        success = database.update_skill(skill_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        updated_skill = database.get_skill_by_id(skill_id)
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
        success = database.delete_skill(skill_id)
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
        about_id = database.create_or_update_about(
            bio=about.bio,
            current_company=about.current_company,
            current_role=about.current_role
        )
        updated_about = database.get_about()
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
        submissions = database.get_all_contact_submissions()
        return submissions
    except Exception as e:
        logger.error(f"Error fetching contact submissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch contact submissions")


@app.delete("/api/admin/contacts/{submission_id}")
async def delete_contact_submission(submission_id: int, admin: str = Depends(auth.verify_admin)):
    """Delete a contact form submission (admin only)."""
    try:
        deleted = database.delete_contact_submission(submission_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Contact submission not found")
        return {"message": "Contact submission deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete contact submission")


# ==================== ADMIN ENDPOINTS - FILE UPLOAD ====================

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@app.post("/api/admin/upload", response_model=dict)
async def upload_image(file: UploadFile = File(...), admin: str = Depends(auth.verify_admin)):
    """Upload an image file (admin only)."""
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        contents = await file.read()
        
        # Validate file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Generate safe filename
        import uuid
        safe_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = static_dir / safe_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return URL to access the file
        file_url = f"/uploads/{safe_filename}"
        
        logger.info(f"Admin {admin} uploaded file: {safe_filename}")
        
        return {
            "success": True,
            "filename": safe_filename,
            "url": file_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@app.get("/api/admin/images", response_model=list)
async def list_images(admin: str = Depends(auth.verify_admin)):
    """List all available images in the static directory (admin only)."""
    try:
        image_files = []
        for file_path in static_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                image_files.append({
                    "filename": file_path.name,
                    "url": f"/uploads/{file_path.name}",
                    "size": file_path.stat().st_size
                })
        
        # Sort by filename
        image_files.sort(key=lambda x: x['filename'])
        
        logger.info(f"Admin {admin} listed {len(image_files)} images")
        return image_files
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list images")


@app.delete("/api/admin/images/{filename}")
async def delete_image(filename: str, admin: str = Depends(auth.verify_admin)):
    """Delete an image file (admin only)."""
    try:
        # Security check: ensure filename doesn't contain path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = static_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete the file
        file_path.unlink()
        
        logger.info(f"Admin {admin} deleted image: {filename}")
        return {"message": "Image deleted successfully", "filename": filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete image")


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
        result = backup.create_backup()
        
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
    """Restore database from uploaded backup file (admin only)."""
    try:
        # Validate file extension
        if not file.filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Only .db files are allowed")
        
        # Read uploaded file
        content = await file.read()
        
        # Create backup of current database first
        current_backup = backup.create_backup()
        logger.info(f"Created safety backup before restore: {current_backup['filename']}")
        
        # Close all active database connections
        database.close_all_connections()
        
        # Remove WAL and SHM files to prevent stale data
        database.cleanup_wal_files()
        
        # Get database path from environment
        db_path = os.getenv('DATABASE_PATH', './backend/portfolio.db')
        
        # Write new database
        with open(db_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Admin {admin} restored database from {file.filename}")
        
        return {
            "success": True,
            "message": "Database restored successfully",
            "backup_created": current_backup['filename']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring database: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to restore database")


@app.get("/api/admin/backups")
async def list_backups(admin: str = Depends(auth.verify_admin)):
    """List all available backups (admin only)."""
    try:
        backups_list = backup.list_backups()
        return {"success": True, "backups": backups_list}
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list backups")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
