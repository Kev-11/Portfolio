import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
import threading
import time

DATABASE_PATH = os.getenv("DATABASE_PATH", "./backend/portfolio.db")
logger = logging.getLogger(__name__)

# Connection management
_pool_lock = threading.Lock()
_last_checkpoint = time.time()
_checkpoint_interval = 300  # 5 minutes


def get_db_connection():
    """Get a database connection with automatic reconnection."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(
                DATABASE_PATH, 
                timeout=30.0,  # Increased timeout for reliability
                check_same_thread=False,
                isolation_level='DEFERRED'  # Use normal transactions for persistence
            )
            conn.row_factory = sqlite3.Row
            
            # Configure for 24/7 availability and data persistence
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=30000000000")  # 30GB memory mapping
            conn.execute("PRAGMA page_size=4096")
            conn.execute("PRAGMA cache_size=10000")  # 40MB cache
            conn.execute("PRAGMA wal_autocheckpoint=1000")  # Checkpoint every 1000 pages
            
            # Test connection
            conn.execute("SELECT 1").fetchone()
            
            # Periodic WAL checkpoint to prevent file bloat
            global _last_checkpoint
            if time.time() - _last_checkpoint > _checkpoint_interval:
                try:
                    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                    _last_checkpoint = time.time()
                except:
                    pass  # Don't fail on checkpoint error
            
            return conn
            
        except sqlite3.Error as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise


def close_all_connections():
    """Close all database connections. Call this after database restore."""
    # Force SQLite to close all connections by checkpointing WAL
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=5.0)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
        logger.info("All database connections closed")
    except Exception as e:
        logger.warning(f"Error closing connections: {e}")


def cleanup_wal_files():
    """Remove WAL and SHM files. Call this during database restore."""
    wal_file = f"{DATABASE_PATH}-wal"
    shm_file = f"{DATABASE_PATH}-shm"
    
    for file_path in [wal_file, shm_file]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed {os.path.basename(file_path)}")
            except Exception as e:
                logger.warning(f"Failed to remove {file_path}: {e}")


def checkpoint_wal():
    """Force a WAL checkpoint to ensure all data is written to main database file."""
    conn = get_db_connection()
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        logger.info("WAL checkpoint completed")
    except Exception as e:
        logger.warning(f"WAL checkpoint failed: {e}")
    finally:
        conn.close()


def verify_database_integrity():
    """Verify database integrity and return health status."""
    try:
        conn = get_db_connection()
        try:
            # Quick integrity check
            result = conn.execute("PRAGMA quick_check").fetchone()
            if result and result[0] == "ok":
                # Test actual data access
                conn.execute("SELECT COUNT(*) FROM projects").fetchone()
                return {"healthy": True, "status": "ok", "message": "Database is healthy"}
            else:
                return {"healthy": False, "status": "error", "message": "Integrity check failed"}
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"healthy": False, "status": "error", "message": str(e)}


def init_db():
    """Initialize the database with all required tables."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                technologies TEXT NOT NULL,
                github_url TEXT,
                external_url TEXT,
                image_url TEXT,
                image_urls TEXT,
                is_featured BOOLEAN DEFAULT 0,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate existing image_url to image_urls array
        try:
            cursor.execute("SELECT name FROM pragma_table_info('projects') WHERE name='image_urls'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE projects ADD COLUMN image_urls TEXT")
                # Migrate existing single images to array format
                cursor.execute("""
                    UPDATE projects 
                    SET image_urls = json_array(image_url) 
                    WHERE image_url IS NOT NULL AND image_url != ''
                """)
        except:
            pass

        # Experience table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experience (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                company_url TEXT,
                role TEXT NOT NULL,
                date_range TEXT NOT NULL,
                responsibilities TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # About table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS about (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bio TEXT NOT NULL,
                current_company TEXT,
                current_role TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Contact submissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT,
                message TEXT NOT NULL,
                ip_address TEXT,
                email_sent BOOLEAN DEFAULT 0,
                email_sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Verify integrity
        conn.execute("PRAGMA integrity_check")
        print(f"Database initialized at {DATABASE_PATH}")
        logger.info(f"Database tables created successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()


# ==================== PROJECTS CRUD ====================

def create_project(title: str, description: str, technologies: List[str], 
                   github_url: Optional[str] = None, external_url: Optional[str] = None,
                   image_url: Optional[str] = None, image_urls: Optional[List[str]] = None,
                   is_featured: bool = False, display_order: int = 0) -> int:
    """Create a new project."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Handle backward compatibility: if image_url provided but not image_urls
        if image_url and not image_urls:
            image_urls = [image_url]
        
        cursor.execute("""
            INSERT INTO projects (title, description, technologies, github_url, 
                                external_url, image_url, image_urls, is_featured, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, json.dumps(technologies), github_url, 
              external_url, image_url, json.dumps(image_urls) if image_urls else None, 
              is_featured, display_order))
        
        project_id = cursor.lastrowid
        conn.commit()
        # Force checkpoint to ensure data is saved
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        print(f"Project '{title}' (ID: {project_id}) successfully saved to database at {DATABASE_PATH}")
        return project_id
    except Exception as e:
        print(f"Error saving project: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_projects(featured_only: bool = False) -> List[Dict[str, Any]]:
    """Get all projects, optionally filtered by featured status."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if featured_only:
            cursor.execute("""
                SELECT * FROM projects WHERE is_featured = 1 ORDER BY display_order, created_at DESC
            """)
        else:
            cursor.execute("SELECT * FROM projects ORDER BY display_order, created_at DESC")
        
        projects = []
        for row in cursor.fetchall():
            project = dict(row)
            project['technologies'] = json.loads(project['technologies'])
            project['is_featured'] = bool(project['is_featured'])
            
            # Parse image_urls array, fallback to single image_url for backward compatibility
            if project.get('image_urls'):
                project['image_urls'] = json.loads(project['image_urls'])
            elif project.get('image_url'):
                project['image_urls'] = [project['image_url']]
            else:
                project['image_urls'] = []
                
            projects.append(project)
        
        return projects
    finally:
        conn.close()


def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """Get a project by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        if row:
            project = dict(row)
            project['technologies'] = json.loads(project['technologies'])
            project['is_featured'] = bool(project['is_featured'])
            
            # Parse image_urls array
            if project.get('image_urls'):
                project['image_urls'] = json.loads(project['image_urls'])
            elif project.get('image_url'):
                project['image_urls'] = [project['image_url']]
            else:
                project['image_urls'] = []
                
            return project
        return None
    finally:
        conn.close()


def update_project(project_id: int, **kwargs) -> bool:
    """Update a project."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Convert technologies list to JSON if present
        if 'technologies' in kwargs and isinstance(kwargs['technologies'], list):
            kwargs['technologies'] = json.dumps(kwargs['technologies'])
        
        # Convert image_urls list to JSON if present
        if 'image_urls' in kwargs and isinstance(kwargs['image_urls'], list):
            kwargs['image_urls'] = json.dumps(kwargs['image_urls'])
        
        # Build update query dynamically
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [project_id]
        
        cursor.execute(f"UPDATE projects SET {fields} WHERE id = ?", values)
        updated = cursor.rowcount > 0
        conn.commit()
        # Force checkpoint to ensure data is saved
        if updated:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return updated
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_project(project_id: int) -> bool:
    """Delete a project."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        # Force checkpoint to ensure data is saved
        if deleted:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return deleted
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==================== EXPERIENCE CRUD ====================

def create_experience(company: str, role: str, date_range: str, 
                     responsibilities: List[str], company_url: Optional[str] = None,
                     display_order: int = 0) -> int:
    """Create a new experience entry."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO experience (company, company_url, role, date_range, 
                                  responsibilities, display_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company, company_url, role, date_range, json.dumps(responsibilities), display_order))
        
        experience_id = cursor.lastrowid
        conn.commit()
        # Force checkpoint to ensure data is saved
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return experience_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_experience() -> List[Dict[str, Any]]:
    """Get all experience entries."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experience ORDER BY display_order, created_at DESC")
        
        experiences = []
        for row in cursor.fetchall():
            exp = dict(row)
            exp['responsibilities'] = json.loads(exp['responsibilities'])
            experiences.append(exp)
        
        return experiences
    finally:
        conn.close()


def get_experience_by_id(experience_id: int) -> Optional[Dict[str, Any]]:
    """Get an experience entry by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experience WHERE id = ?", (experience_id,))
        row = cursor.fetchone()
        
        if row:
            exp = dict(row)
            exp['responsibilities'] = json.loads(exp['responsibilities'])
            return exp
        return None
    finally:
        conn.close()


def update_experience(experience_id: int, **kwargs) -> bool:
    """Update an experience entry."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Convert responsibilities list to JSON if present
        if 'responsibilities' in kwargs and isinstance(kwargs['responsibilities'], list):
            kwargs['responsibilities'] = json.dumps(kwargs['responsibilities'])
        
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [experience_id]
        
        cursor.execute(f"UPDATE experience SET {fields} WHERE id = ?", values)
        updated = cursor.rowcount > 0
        conn.commit()
        # Force checkpoint to ensure data is saved
        if updated:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return updated
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_experience(experience_id: int) -> bool:
    """Delete an experience entry."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM experience WHERE id = ?", (experience_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        # Force checkpoint to ensure data is saved
        if deleted:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return deleted
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==================== SKILLS CRUD ====================

def create_skill(name: str, category: Optional[str] = None) -> int:
    """Create a new skill."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO skills (name, category) VALUES (?, ?)", (name, category))
        skill_id = cursor.lastrowid
        conn.commit()
        # Force checkpoint to ensure data is saved
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return skill_id
    except sqlite3.IntegrityError:
        return -1  # Skill already exists
    finally:
        conn.close()


def get_all_skills() -> List[Dict[str, Any]]:
    """Get all skills."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills ORDER BY category, name")
        skills = [dict(row) for row in cursor.fetchall()]
        return skills
    finally:
        conn.close()


def get_skill_by_id(skill_id: int) -> Optional[Dict[str, Any]]:
    """Get a skill by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_skill(skill_id: int, **kwargs) -> bool:
    """Update a skill."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [skill_id]
        
        cursor.execute(f"UPDATE skills SET {fields} WHERE id = ?", values)
        updated = cursor.rowcount > 0
        conn.commit()
        # Force checkpoint to ensure data is saved
        if updated:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return updated
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_skill(skill_id: int) -> bool:
    """Delete a skill."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        # Force checkpoint to ensure data is saved
        if deleted:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return deleted
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==================== ABOUT CRUD ====================

def create_or_update_about(bio: str, current_company: Optional[str] = None, 
                           current_role: Optional[str] = None) -> int:
    """Create or update the about section (only one entry exists)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if about entry exists
        cursor.execute("SELECT id FROM about LIMIT 1")
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute("""
                UPDATE about SET bio = ?, current_company = ?, current_role = ?, 
                               updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (bio, current_company, current_role, existing['id']))
            about_id = existing['id']
        else:
            # Create new
            cursor.execute("""
                INSERT INTO about (bio, current_company, current_role)
                VALUES (?, ?, ?)
            """, (bio, current_company, current_role))
            about_id = cursor.lastrowid
        
        conn.commit()
        # Force checkpoint to ensure data is saved
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return about_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_about() -> Optional[Dict[str, Any]]:
    """Get the about section."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM about LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ==================== CONTACT SUBMISSIONS CRUD ====================

def create_contact_submission(name: str, email: str, message: str,
                              subject: Optional[str] = None, 
                              ip_address: Optional[str] = None) -> int:
    """Create a new contact submission."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contact_submissions (name, email, subject, message, ip_address)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, subject, message, ip_address))
        
        submission_id = cursor.lastrowid
        conn.commit()
        # Force checkpoint to ensure data is saved
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return submission_id
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_email_sent(submission_id: int) -> bool:
    """Mark a contact submission as email sent."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contact_submissions 
            SET email_sent = 1, email_sent_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (submission_id,))
        
        updated = cursor.rowcount > 0
        conn.commit()
        # Force checkpoint to ensure data is saved
        if updated:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        print(f"Contact submission {submission_id} marked as email sent")
        return updated
    except Exception as e:
        print(f"Error marking email as sent: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_all_contact_submissions() -> List[Dict[str, Any]]:
    """Get all contact submissions."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contact_submissions ORDER BY created_at DESC")
        submissions = [dict(row) for row in cursor.fetchall()]
        return submissions
    finally:
        conn.close()


def delete_contact_submission(submission_id: int) -> bool:
    """Delete a contact submission by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contact_submissions WHERE id = ?", (submission_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        # Force checkpoint to ensure data is saved
        if deleted:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        return deleted
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_recent_submissions_by_ip(ip_address: str, hours: int = 1) -> int:
    """Get count of submissions from an IP in the last N hours."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM contact_submissions 
            WHERE ip_address = ? 
            AND created_at > datetime('now', '-' || ? || ' hours')
        """, (ip_address, hours))
        
        result = cursor.fetchone()
        return result['count'] if result else 0
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
