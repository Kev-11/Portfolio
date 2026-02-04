from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime


# ==================== PROJECT MODELS ====================

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    technologies: List[str] = Field(..., min_items=1)
    github_url: Optional[str] = None
    external_url: Optional[str] = None
    image_url: Optional[str] = None  # Kept for backward compatibility
    image_urls: Optional[List[str]] = None  # Multiple images support
    is_featured: bool = False
    display_order: int = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    technologies: Optional[List[str]] = None
    github_url: Optional[str] = None
    external_url: Optional[str] = None
    image_url: Optional[str] = None  # Kept for backward compatibility
    image_urls: Optional[List[str]] = None  # Multiple images support
    is_featured: Optional[bool] = None
    display_order: Optional[int] = None


class Project(ProjectBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True


# ==================== EXPERIENCE MODELS ====================

class ExperienceBase(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    company_url: Optional[str] = None
    role: str = Field(..., min_length=1, max_length=200)
    date_range: str = Field(..., min_length=1, max_length=100)
    responsibilities: List[str] = Field(..., min_items=1)
    display_order: int = 0


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    company_url: Optional[str] = None
    role: Optional[str] = Field(None, min_length=1, max_length=200)
    date_range: Optional[str] = Field(None, min_length=1, max_length=100)
    responsibilities: Optional[List[str]] = None
    display_order: Optional[int] = None


class Experience(ExperienceBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True


# ==================== SKILL MODELS ====================

class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)


class Skill(SkillBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True


# ==================== ABOUT MODELS ====================

class AboutBase(BaseModel):
    bio: str = Field(..., min_length=1, max_length=5000)
    current_company: Optional[str] = Field(None, max_length=200)
    current_role: Optional[str] = Field(None, max_length=200)


class AboutCreate(AboutBase):
    pass


class AboutUpdate(AboutBase):
    pass


class About(AboutBase):
    id: int
    updated_at: str

    class Config:
        from_attributes = True


# ==================== CONTACT MODELS ====================

class ContactRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: Optional[str] = Field(None, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)
    honeypot: Optional[str] = Field(None, max_length=0)  # Should be empty

    @validator('honeypot')
    def check_honeypot(cls, v):
        if v:  # If honeypot is filled, it's likely a bot
            raise ValueError('Invalid submission')
        return v


class ContactSubmission(BaseModel):
    id: int
    name: str
    email: str
    subject: Optional[str]
    message: str
    ip_address: Optional[str]
    email_sent: bool
    email_sent_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


# ==================== RESPONSE MODELS ====================

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    success: bool = False
