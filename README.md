# Portfolio Website

A modern, production-ready portfolio website built with HTML, CSS, JavaScript (frontend), FastAPI (backend), and SQLite (database). Features a complete admin panel for managing content, contact form with email notifications, and automated database backups.

## 🎨 Features

- **Modern Dark Theme**: Exact color scheme from v4.brittanychiang.com
- **Responsive Design**: Mobile-first, works on all devices
- **Dynamic Content**: All content managed via admin panel
- **Contact Form**: With email notifications via SMTP
- **Admin Panel**: Full CRUD operations for all content
- **File Upload**: Image upload for projects
- **Database Backup**: Automated backup and download
- **Smooth Animations**: Scroll-triggered fade-in effects
- **Production Ready**: Easy deployment to Vercel + Render

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   cd Portfolio
   ```

2. **Create and activate virtual environment**
   
   **Windows:**
   ```bash
   setup_venv.bat
   ```
   
   **Mac/Linux:**
   ```bash
   chmod +x setup_venv.sh
   ./setup_venv.sh
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   - SMTP credentials (Gmail app password)
   - Admin username and password
   - CORS origins

4. **Start the backend server**
   ```bash
   # Activate venv first (if not already activated)
   # Windows: venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open the frontend**
   
   Open `frontend/index.html` in your browser or use a local server:
   ```bash
   # Using Python
   cd frontend
   python -m http.server 3000
   ```
   
   Then visit: `http://localhost:3000`

6. **Access admin panel**
   
   Visit: `http://localhost:3000/admin.html`
   
   Login with credentials from your `.env` file

## 📁 Project Structure

```
Portfolio/
├── frontend/               # Frontend files
│   ├── index.html         # Main portfolio page
│   ├── admin.html         # Admin panel
│   ├── css/
│   │   ├── variables.css  # Color scheme & design tokens
│   │   ├── styles.css     # Main portfolio styles
│   │   └── admin.css      # Admin panel styles
│   ├── js/
│   │   ├── main.js        # Main portfolio logic
│   │   └── admin.js       # Admin panel logic
│   └── assets/
│       ├── images/        # Uploaded images
│       └── resume.pdf     # Your resume (add your own)
├── backend/               # FastAPI backend
│   ├── main.py           # FastAPI app & endpoints
│   ├── database.py       # SQLite operations
│   ├── models.py         # Pydantic models
│   ├── auth.py           # Authentication
│   ├── email_service.py  # SMTP email sending
│   ├── backup.py         # Database backup
│   └── logs/             # Application logs
├── backups/              # Database backups
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
├── setup_venv.bat       # Windows setup script
├── setup_venv.sh        # Mac/Linux setup script
├── vercel.json          # Vercel deployment config
├── render.yaml          # Render deployment config
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

Required variables in `.env`:

```bash
# Database
DATABASE_PATH=./backend/portfolio.db

# SMTP (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate at https://myaccount.google.com/apppasswords
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TO_EMAIL=your-email@gmail.com

# Admin Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5500

# Rate Limiting
RATE_LIMIT_REQUESTS=3
RATE_LIMIT_PERIOD=3600

# Environment
ENVIRONMENT=development
```

### Gmail App Password Setup

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "Portfolio Contact Form"
4. Copy the generated password to `SMTP_PASSWORD` in `.env`

## 📝 Content Management

### Via Admin Panel

1. **Projects**: Add featured and regular projects with images, technologies, and links
2. **Experience**: Add work history with company, role, dates, and responsibilities
3. **Skills**: Add technical skills organized by category
4. **About**: Update bio, current company, and role
5. **Contacts**: View all contact form submissions

### Direct Database Access

You can also manage data directly via SQLite:

```bash
sqlite3 backend/portfolio.db

# View tables
.tables

# Query data
SELECT * FROM projects;

# Exit
.quit
```

## 🌐 Deployment

### Option 1: Vercel (Frontend) + Render (Backend)

#### Deploy Backend to Render

1. Create account at [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: portfolio-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (from `.env`)
6. Add persistent disk:
   - **Name**: portfolio-data
   - **Mount Path**: /data
   - **Size**: 1GB
7. Deploy!
8. Copy your Render URL (e.g., `https://portfolio-api.onrender.com`)

#### Deploy Frontend to Vercel

1. Create account at [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: ./
5. Deploy!
6. After deployment, update frontend JavaScript:
   - Edit `frontend/js/main.js` and `frontend/js/admin.js`
   - Replace `YOUR_BACKEND_URL` with your Render URL
   - Commit and push changes

7. **Update CORS**: Add your Vercel URL to Render environment variables:
   ```
   CORS_ORIGINS=https://your-portfolio.vercel.app
   ```

### Option 2: Both on Render

Render supports static sites too:

1. Deploy backend (as above)
2. Create new "Static Site" for frontend
3. Configure build settings
4. Update JavaScript with backend URL

## 🎨 Customization

### Update Colors

Edit `frontend/css/variables.css`:

```css
:root {
  --navy: #0a192f;           /* Main background */
  --green: #64ffda;          /* Accent color */
  --lightest-slate: #ccd6f6; /* Headings */
  /* ... more variables ... */
}
```

### Add Your Photo

1. **Via Admin Panel**: Upload image in Projects/Experience
2. **Manual**: 
   - Place image in `frontend/assets/images/profile.jpg`
   - Uncomment CSS in `frontend/css/styles.css` (search for "To replace the placeholder")

### Update Resume

Replace `frontend/assets/resume.pdf` with your own PDF resume.

### Customize Content

All text content in `index.html` can be edited directly or managed via admin panel after deployment.

## 🔒 Security

- **HTTPS Only**: Always use HTTPS in production
- **Strong Passwords**: Use strong admin password
- **Environment Variables**: Never commit `.env` to git
- **Rate Limiting**: Contact form limited to 3 submissions/hour per IP
- **Honeypot**: Spam protection on contact form
- **Basic Auth**: Admin panel protected with HTTP Basic Auth

## 📊 Monitoring

### Logs

Backend logs are stored in `backend/logs/app.log`:

```bash
tail -f backend/logs/app.log
```

### Database Backups

Backups are automatically created when you click "Download Backup" in admin panel.

Manual backup:
```bash
cp backend/portfolio.db backups/backup-$(date +%Y%m%d).db
```

## 🐛 Troubleshooting

### Backend won't start

- Check Python version: `python --version` (need 3.10+)
- Activate venv: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
- Check logs: `backend/logs/app.log`

### Contact form not sending emails

- Verify SMTP credentials in `.env`
- Check Gmail app password is correct
- Review logs for error messages
- Test with: `python -c "from backend.email_service import send_test_email; import asyncio; asyncio.run(send_test_email())"`

### Admin panel login fails

- Verify `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`
- Check browser console for errors
- Ensure backend is running

### Images not uploading

- Check file size (<5MB)
- Verify file type (jpg, png, webp, gif)
- Ensure `frontend/assets/images/` directory exists
- Check backend logs

## 📚 Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python, FastAPI, Uvicorn
- **Database**: SQLite
- **Email**: aiosmtplib (SMTP)
- **Deployment**: Vercel (frontend), Render (backend)

## 📄 License

This project is open source and available for personal use.

## 🤝 Contributing

Feel free to fork this project and customize it for your own portfolio!

## 📧 Support

For issues or questions, please open an issue on GitHub or use the contact form on the deployed site.

---

**Built with ❤️ using modern web technologies**
