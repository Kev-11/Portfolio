"""
Database Seeding Script
Run this to populate your database with sample portfolio data.

Usage:
    python seed_database.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend import database

def seed_database():
    """Seed the database with sample data."""
    print("🌱 Seeding database...")
    
    # Initialize database first
    database.init_db()
    print("✅ Database initialized")
    
    # Sample Projects
    print("\n📁 Adding sample projects...")
    
    projects_data = [
        {
            "title": "Portfolio Website",
            "description": "A modern, responsive portfolio website with an admin panel for content management. Built with FastAPI backend and vanilla JavaScript frontend.",
            "technologies": ["Python", "FastAPI", "JavaScript", "SQLite", "HTML/CSS"],
            "github_url": "https://github.com/yourusername/portfolio",
            "external_url": None,
            "image_urls": [],
            "is_featured": True,
            "display_order": 1
        },
        {
            "title": "E-Commerce Platform",
            "description": "Full-stack e-commerce solution with payment integration, inventory management, and order tracking.",
            "technologies": ["React", "Node.js", "MongoDB", "Stripe", "Redux"],
            "github_url": "https://github.com/yourusername/ecommerce",
            "external_url": "https://demo-shop.example.com",
            "image_urls": [],
            "is_featured": True,
            "display_order": 2
        },
        {
            "title": "Task Management App",
            "description": "Collaborative task management application with real-time updates, team collaboration, and progress tracking.",
            "technologies": ["Vue.js", "Firebase", "Tailwind CSS", "TypeScript"],
            "github_url": "https://github.com/yourusername/taskapp",
            "external_url": None,
            "image_urls": [],
            "is_featured": False,
            "display_order": 3
        },
        {
            "title": "Weather Dashboard",
            "description": "Real-time weather dashboard with forecasts, historical data visualization, and location-based alerts.",
            "technologies": ["React", "Chart.js", "OpenWeather API", "Material-UI"],
            "github_url": "https://github.com/yourusername/weather",
            "external_url": "https://weather-dash.example.com",
            "image_urls": [],
            "is_featured": False,
            "display_order": 4
        },
        {
            "title": "Blog CMS",
            "description": "Content management system for bloggers with markdown support, SEO optimization, and analytics.",
            "technologies": ["Django", "PostgreSQL", "Redis", "Docker"],
            "github_url": "https://github.com/yourusername/blog-cms",
            "external_url": None,
            "image_urls": [],
            "is_featured": True,
            "display_order": 5
        },
        {
            "title": "Fitness Tracker",
            "description": "Mobile-first fitness tracking app with workout logging, progress charts, and goal setting.",
            "technologies": ["React Native", "Express", "MongoDB", "JWT"],
            "github_url": "https://github.com/yourusername/fitness",
            "external_url": None,
            "image_urls": [],
            "is_featured": False,
            "display_order": 6
        }
    ]
    
    for project in projects_data:
        try:
            project_id = database.create_project(**project)
            print(f"  ✓ Created project: {project['title']} (ID: {project_id})")
        except Exception as e:
            print(f"  ✗ Error creating project {project['title']}: {e}")
    
    # Sample Experience
    print("\n💼 Adding sample experience...")
    
    experience_data = [
        {
            "company": "Tech Solutions Inc.",
            "company_url": "https://techsolutions.example.com",
            "role": "Senior Full Stack Developer",
            "date_range": "Jan 2023 - Present",
            "responsibilities": [
                "Led development of microservices architecture serving 1M+ users",
                "Mentored team of 5 junior developers",
                "Implemented CI/CD pipelines reducing deployment time by 60%",
                "Architected scalable solutions using AWS and Docker"
            ],
            "display_order": 1
        },
        {
            "company": "StartUp Ventures",
            "company_url": "https://startup.example.com",
            "role": "Full Stack Developer",
            "date_range": "Mar 2021 - Dec 2022",
            "responsibilities": [
                "Built RESTful APIs using Node.js and Express",
                "Developed responsive React applications",
                "Integrated third-party payment systems",
                "Optimized database queries improving performance by 40%"
            ],
            "display_order": 2
        },
        {
            "company": "Digital Agency Co.",
            "company_url": "https://digitalagency.example.com",
            "role": "Frontend Developer",
            "date_range": "Jun 2019 - Feb 2021",
            "responsibilities": [
                "Created pixel-perfect responsive websites for 20+ clients",
                "Collaborated with designers using Figma and Adobe XD",
                "Implemented SEO best practices",
                "Maintained and updated legacy codebases"
            ],
            "display_order": 3
        }
    ]
    
    for exp in experience_data:
        try:
            exp_id = database.create_experience(**exp)
            print(f"  ✓ Created experience: {exp['role']} at {exp['company']} (ID: {exp_id})")
        except Exception as e:
            print(f"  ✗ Error creating experience: {e}")
    
    # Sample Skills
    print("\n🛠️  Adding sample skills...")
    
    skills_data = [
        # Frontend
        {"name": "JavaScript", "category": "Frontend"},
        {"name": "React", "category": "Frontend"},
        {"name": "Vue.js", "category": "Frontend"},
        {"name": "TypeScript", "category": "Frontend"},
        {"name": "HTML/CSS", "category": "Frontend"},
        {"name": "Tailwind CSS", "category": "Frontend"},
        
        # Backend
        {"name": "Python", "category": "Backend"},
        {"name": "Node.js", "category": "Backend"},
        {"name": "FastAPI", "category": "Backend"},
        {"name": "Django", "category": "Backend"},
        {"name": "Express", "category": "Backend"},
        {"name": "RESTful APIs", "category": "Backend"},
        
        # Database
        {"name": "PostgreSQL", "category": "Database"},
        {"name": "MongoDB", "category": "Database"},
        {"name": "SQLite", "category": "Database"},
        {"name": "Redis", "category": "Database"},
        
        # DevOps
        {"name": "Docker", "category": "DevOps"},
        {"name": "AWS", "category": "DevOps"},
        {"name": "CI/CD", "category": "DevOps"},
        {"name": "Git", "category": "DevOps"},
        
        # Tools
        {"name": "VS Code", "category": "Tools"},
        {"name": "Postman", "category": "Tools"},
        {"name": "Figma", "category": "Tools"},
    ]
    
    for skill in skills_data:
        try:
            skill_id = database.create_skill(**skill)
            print(f"  ✓ Created skill: {skill['name']} ({skill['category']})")
        except Exception as e:
            # Skill might already exist (UNIQUE constraint)
            if "UNIQUE constraint" in str(e):
                print(f"  → Skill already exists: {skill['name']}")
            else:
                print(f"  ✗ Error creating skill {skill['name']}: {e}")
    
    # Sample About
    print("\n👤 Adding about information...")
    
    about_data = {
        "bio": "Passionate full-stack developer with 5+ years of experience building scalable web applications. Specialized in modern JavaScript frameworks and Python backend development. Love creating beautiful, user-friendly interfaces and solving complex problems.",
        "current_company": "Tech Solutions Inc.",
        "current_role": "Senior Full Stack Developer"
    }
    
    try:
        about_id = database.create_or_update_about(**about_data)
        print(f"  ✓ Created about section (ID: {about_id})")
    except Exception as e:
        print(f"  ✗ Error creating about: {e}")
    
    print("\n✨ Database seeding completed!")
    print("\n📊 Summary:")
    print(f"  • Projects: {len(projects_data)}")
    print(f"  • Experience: {len(experience_data)}")
    print(f"  • Skills: {len(skills_data)}")
    print(f"  • About: 1 entry")
    print("\n🎉 Your portfolio database is ready to use!")
    print("\nNext steps:")
    print("  1. Customize the data through the admin panel")
    print("  2. Upload project images")
    print("  3. Update the information to match your actual portfolio")


if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        sys.exit(1)
