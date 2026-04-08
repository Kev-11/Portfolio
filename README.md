# Kevin Patel's Portfolio

An animated, content-managed portfolio that showcases projects, experience, and skills with a FastAPI backend powering dynamic data and an admin panel for updates.

## Live App
- Frontend: https://portfolio-kevpatz.vercel.app
- Backend health: https://portfolio-back-flax-beta.vercel.app/api/health
- Admin panel: https://portfolio-kevpatz.vercel.app/admin

## What It Does
- Presents a responsive, dark-themed portfolio with custom hexagonal branding, smooth scroll/hover animations, and mobile-friendly layouts.
- Fetches portfolio content from the FastAPI backend, with MongoDB storing projects, experience, skills, and about details.
- Includes a secured admin dashboard for CRUD on all sections, drag-and-drop image uploads (single or carousel), contact management, and one-click database backups.
- Provides a contact form with rate limiting and honeypot spam protection, plus configurable backend URL for flexible deployments.

## Key Details
- Frontend: HTML, CSS, and vanilla JavaScript served from Vercel.
- Backend: FastAPI with authentication, rate limiting, and image handling, deployed as Vercel serverless functions.
- Data: MongoDB for all portfolio content and backups.
- Support: Email at kevin.05.patel@gmail.com for inquiries or updates.
