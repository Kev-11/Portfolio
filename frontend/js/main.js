// Portfolio Main JavaScript
// API Base URL - Update this to your backend URL in production
const API_URL = window.API_URL;

// EmailJS Configuration
const EMAILJS_PUBLIC_KEY = 'ZQo7MVaEQ7zlSZs1v';
const EMAILJS_SERVICE_ID = 'service_63oorub';
const EMAILJS_TEMPLATE_ID = 'template_ozb9npl';

// State
let allProjects = [];
let showingAllProjects = false;
const INITIAL_PROJECT_COUNT = 6;

// ==================== DOM LOADED ====================
document.addEventListener('DOMContentLoaded', () => {
    // Fetch data from API
    fetchAllData();
    
    // Setup event listeners
    setupNavigation();
    setupContactForm();
    setupScrollAnimations();
    
    // Setup show more button
    const showMoreBtn = document.getElementById('show-more-btn');
    if (showMoreBtn) {
        showMoreBtn.addEventListener('click', toggleProjects);
    }
});

// ==================== FETCH DATA FROM API ====================
async function fetchAllData() {
    console.log('[MAIN] Starting to fetch all data...');
    console.log('[INFO] Backend may take 30-60 seconds to wake up if inactive...');
    
    try {
        // Fetch all data in parallel
        const [projects, experience, skills, about] = await Promise.all([
            fetchProjects(),
            fetchExperience(),
            fetchSkills(),
            fetchAbout()
        ]);

        console.log('[MAIN] Fetched data:', { projects, experience, skills, about });

        // Render data
        if (projects && projects.length > 0) {
            console.log('[MAIN] Rendering projects:', projects.length);
            renderProjects(projects);
        } else {
            console.log('[MAIN] No projects to render');
        }
        
        if (experience && experience.length > 0) {
            console.log('[MAIN] Rendering experience:', experience.length);
            renderExperience(experience);
        } else {
            console.log('[MAIN] No experience to render');
        }
        
        if (skills && skills.length > 0) {
            console.log('[MAIN] Rendering skills:', skills.length);
            renderSkills(skills);
        } else {
            console.log('[MAIN] No skills to render');
        }
        
        if (about) {
            console.log('[MAIN] Rendering about');
            renderAbout(about);
        } else {
            console.log('[MAIN] No about data to render');
        }
    } catch (error) {
        console.error('[MAIN] Error fetching data:', error);
    }
}

async function fetchProjects() {
    try {
        console.log(`[API] Fetching projects from ${API_URL}/api/projects`);
        const response = await fetch(`${API_URL}/api/projects`, { 
            signal: AbortSignal.timeout(60000) // 60 second timeout for cold start
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching projects:', error);
        return [];
    }
}

async function fetchExperience() {
    try {
        console.log(`[API] Fetching experience from ${API_URL}/api/experience`);
        const response = await fetch(`${API_URL}/api/experience`, {
            signal: AbortSignal.timeout(60000) // 60 second timeout for cold start
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching experience:', error);
        return [];
    }
}

async function fetchSkills() {
    try {
        console.log(`[API] Fetching skills from ${API_URL}/api/skills`);
        const response = await fetch(`${API_URL}/api/skills`, {
            signal: AbortSignal.timeout(60000) // 60 second timeout for cold start
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching skills:', error);
        return [];
    }
}

async function fetchAbout() {
    try {
        console.log(`[API] Fetching about from ${API_URL}/api/about`);
        const response = await fetch(`${API_URL}/api/about`, {
            signal: AbortSignal.timeout(60000) // 60 second timeout for cold start
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        const data = await response.json();
        return Object.keys(data).length > 0 ? data : null;
    } catch (error) {
        console.error('Error fetching about:', error);
        return null;
    }
}

// ==================== RENDER FUNCTIONS ====================

function renderProjects(projects) {
    allProjects = projects;
    
    // Separate featured and other projects
    const featured = projects.filter(p => p.is_featured);
    const other = projects.filter(p => !p.is_featured);
    
    // Render featured projects
    if (featured.length > 0) {
        renderFeaturedProjects(featured);
    }
    
    // Render other projects
    if (other.length > 0) {
        renderOtherProjects(other);
    }
}

function renderFeaturedProjects(projects) {
    const container = document.getElementById('featured-projects');
    if (!container) return;
    
    container.innerHTML = projects.map(project => `
        <div class="featured-project fade-in">
            <div class="project-content">
                <p class="project-overline">Featured Project</p>
                <h3 class="project-title">
                    ${project.external_url ? `<a href="${project.external_url}" target="_blank" rel="noopener noreferrer">${project.title}</a>` : project.title}
                </h3>
                <div class="project-description">
                    <p>${project.description}</p>
                </div>
                <ul class="project-tech-list">
                    ${project.technologies.map(tech => `<li>${tech}</li>`).join('')}
                </ul>
                <div class="project-links">
                    ${project.github_url ? `
                        <a href="${project.github_url}" aria-label="GitHub Link" target="_blank" rel="noopener noreferrer">
                            <svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20">
                                <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                            </svg>
                        </a>
                    ` : ''}
                    ${project.external_url ? `
                        <a href="${project.external_url}" aria-label="External Link" target="_blank" rel="noopener noreferrer">
                            <svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" y1="14" x2="21" y2="3"></line>
                            </svg>
                        </a>
                    ` : ''}
                </div>
            </div>
            <div class="project-image">
                <div class="project-image-wrapper">
                    ${renderProjectImages(project)}
                </div>
            </div>
        </div>
    `).join('');
    
    // Re-trigger scroll animations
    observeElements();
}

function renderOtherProjects(projects) {
    const container = document.getElementById('projects-grid');
    const showMoreBtn = document.getElementById('show-more-btn');
    
    if (!container) return;
    
    // Determine how many projects to show
    const projectsToShow = showingAllProjects ? projects : projects.slice(0, INITIAL_PROJECT_COUNT);
    
    container.innerHTML = projectsToShow.map(project => `
        <div class="project-card fade-in">
            <div class="project-card-top">
                <div class="folder-icon">📁</div>
                <div class="project-card-links">
                    ${project.github_url ? `
                        <a href="${project.github_url}" aria-label="GitHub Link" target="_blank" rel="noopener noreferrer">
                            <svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20">
                                <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                            </svg>
                        </a>
                    ` : ''}
                    ${project.external_url ? `
                        <a href="${project.external_url}" aria-label="External Link" target="_blank" rel="noopener noreferrer">
                            <svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" y1="14" x2="21" y2="3"></line>
                            </svg>
                        </a>
                    ` : ''}
                </div>
            </div>
            <h3 class="project-card-title">
                ${project.external_url ? `<a href="${project.external_url}" target="_blank" rel="noopener noreferrer">${project.title}</a>` : project.title}
            </h3>
            <div class="project-card-description">
                <p>${project.description}</p>
            </div>
            <ul class="project-card-tech">
                ${project.technologies.map(tech => `<li>${tech}</li>`).join('')}
            </ul>
        </div>
    `).join('');
    
    // Show/hide the "Show More" button
    if (projects.length > INITIAL_PROJECT_COUNT) {
        showMoreBtn.style.display = 'block';
        showMoreBtn.textContent = showingAllProjects ? 'Show Less' : 'Show More';
    } else {
        showMoreBtn.style.display = 'none';
    }
    
    // Re-trigger scroll animations
    observeElements();
}

function toggleProjects() {
    showingAllProjects = !showingAllProjects;
    const other = allProjects.filter(p => !p.is_featured);
    renderOtherProjects(other);
}

function renderExperience(experiences) {
    const tabsContainer = document.getElementById('job-tabs');
    const panelsContainer = document.getElementById('job-panels');
    
    if (!tabsContainer || !panelsContainer || experiences.length === 0) return;
    
    // Render tabs
    tabsContainer.innerHTML = experiences.map((exp, index) => `
        <button class="job-tab ${index === 0 ? 'active' : ''}" 
                role="tab" 
                data-index="${index}"
                aria-selected="${index === 0}"
                aria-controls="panel-${index}">
            ${exp.company}
        </button>
    `).join('');
    
    // Render panels
    panelsContainer.innerHTML = experiences.map((exp, index) => `
        <div class="job-panel ${index === 0 ? 'active' : ''}" 
             id="panel-${index}" 
             role="tabpanel">
            <h3 class="job-title">
                <span>${exp.role}</span>
                <span class="job-company"> @ 
                    ${exp.company_url ? 
                        `<a href="${exp.company_url}" target="_blank" rel="noopener noreferrer">${exp.company}</a>` : 
                        exp.company
                    }
                </span>
            </h3>
            <p class="job-date">${exp.date_range}</p>
            <ul class="job-description">
                ${exp.responsibilities.map(resp => `<li>${resp}</li>`).join('')}
            </ul>
        </div>
    `).join('');
    
    // Setup tab switching
    setupTabs();
}

function setupTabs() {
    const tabs = document.querySelectorAll('.job-tab');
    const panels = document.querySelectorAll('.job-panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const index = tab.dataset.index;
            
            // Remove active class from all tabs and panels
            tabs.forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            panels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding panel
            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
            document.getElementById(`panel-${index}`).classList.add('active');
        });
    });
}

function renderSkills(skills) {
    const container = document.getElementById('skills-list');
    if (!container || skills.length === 0) return;
    
    container.innerHTML = skills.map(skill => `<li>${skill.name}</li>`).join('');
}

function renderAbout(about) {
    const bioContainer = document.getElementById('about-bio');
    if (!bioContainer || !about) return;
    
    // Split bio into paragraphs (assuming bio is separated by \n\n or similar)
    const paragraphs = about.bio.split('\n\n').filter(p => p.trim());
    
    bioContainer.innerHTML = paragraphs.map(p => `<p>${p}</p>`).join('');
    
    // Update hero section if current company/role provided
    if (about.current_company || about.current_role) {
        const heroDescription = document.querySelector('.hero-description');
        if (heroDescription && about.current_company && about.current_role) {
            heroDescription.textContent = `I'm a ${about.current_role} at ${about.current_company}, specializing in building exceptional digital experiences.`;
        }
    }
}

// ==================== NAVIGATION ====================

function setupNavigation() {
    const nav = document.getElementById('navbar');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    
    // Smooth scroll with offset for fixed nav
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                const navHeight = nav.offsetHeight;
                const targetPosition = targetSection.offsetTop - navHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add scroll class to nav
    let lastScrollY = window.scrollY;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
        
        lastScrollY = window.scrollY;
    });
}

// ==================== CONTACT FORM ====================

// Initialize EmailJS
if (typeof emailjs !== 'undefined') {
    emailjs.init(EMAILJS_PUBLIC_KEY);
}

function setupContactForm() {
    const form = document.getElementById('contact-form');
    const submitBtn = form.querySelector('.form-submit');
    const messageDiv = document.getElementById('form-message');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get form data
        const formData = {
            name: document.getElementById('name').value.trim(),
            email: document.getElementById('email').value.trim(),
            subject: document.getElementById('subject').value.trim(),
            message: document.getElementById('message').value.trim(),
            honeypot: document.getElementById('website').value
        };
        
        // Client-side validation
        if (formData.name.length < 2) {
            showMessage('Please enter a valid name (at least 2 characters)', 'error');
            return;
        }
        
        if (formData.message.length < 10) {
            showMessage('Please enter a message (at least 10 characters)', 'error');
            return;
        }
        
        // Disable submit button and show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';
        messageDiv.style.display = 'none';
        
        try {
            // Save to database first (backend)
            try {
                await fetch(`${API_URL}/api/contact`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
            } catch (dbError) {
                console.warn('Failed to save to database:', dbError);
                // Continue with email sending even if database save fails
            }
            
            // Send email using EmailJS
            const templateParams = {
                from_name: formData.name,
                from_email: formData.email,
                subject: formData.subject || 'Portfolio Contact',
                message: formData.message,
                to_email: 'ultkev0@gmail.com' // Your email where you want to receive messages
            };
            
            await emailjs.send(
                EMAILJS_SERVICE_ID,
                EMAILJS_TEMPLATE_ID,
                templateParams
            );
            
            showMessage('Thank you for your message! I\'ll get back to you soon.', 'success');
            form.reset();
            
        } catch (error) {
            console.error('Error submitting form:', error);
            showMessage('Failed to send message. Please try again later.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send Message';
        }
    });
}

function showMessage(message, type) {
    const messageDiv = document.getElementById('form-message');
    messageDiv.textContent = message;
    messageDiv.className = `form-message ${type}`;
    messageDiv.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

// ==================== SCROLL ANIMATIONS ====================

function setupScrollAnimations() {
    observeElements();
}

function observeElements() {
    const fadeElements = document.querySelectorAll('.fade-in');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    fadeElements.forEach(element => {
        observer.observe(element);
    });
}

// ==================== PROJECT IMAGE RENDERING ====================

function renderProjectImages(project) {
    // Get image URLs - support both single image_url and multiple image_urls
    let imageUrls = [];
    
    if (project.image_urls && Array.isArray(project.image_urls) && project.image_urls.length > 0) {
        imageUrls = project.image_urls;
    } else if (project.image_url) {
        imageUrls = [project.image_url];
    }
    
    // If no images, return placeholder
    if (imageUrls.length === 0) {
        return `
            <div style="width: 100%; height: 300px; background: var(--light-navy); border-radius: var(--border-radius); display: flex; align-items: center; justify-content: center; color: var(--slate);">
                Project Image
            </div>
        `;
    }
    
    // Ensure image URLs are absolute (include API_URL if they're relative)
    imageUrls = imageUrls.map(url => {
        if (url.startsWith('/')) {
            return `${API_URL}${url}`;
        }
        return url;
    });
    
    // Single image
    if (imageUrls.length === 1) {
        return `<img src="${imageUrls[0]}" alt="${project.title}" style="width: 100%; height: auto; border-radius: var(--border-radius);">`;
    }
    
    // Multiple images - create carousel
    const carouselId = `carousel-${project.id}`;
    return `
        <div class="project-carousel" id="${carouselId}">
            <div class="carousel-slides">
                ${imageUrls.map(url => `
                    <div class="carousel-slide">
                        <img src="${url}" alt="${project.title}">
                    </div>
                `).join('')}
            </div>
            <button class="carousel-nav prev" onclick="moveCarousel('${carouselId}', -1)" aria-label="Previous image">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
            </button>
            <button class="carousel-nav next" onclick="moveCarousel('${carouselId}', 1)" aria-label="Next image">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </button>
            <div class="carousel-indicators">
                ${imageUrls.map((_, index) => `
                    <button class="carousel-indicator ${index === 0 ? 'active' : ''}" 
                            onclick="goToSlide('${carouselId}', ${index})"
                            aria-label="Go to image ${index + 1}"></button>
                `).join('')}
            </div>
        </div>
    `;
}

// ==================== CAROUSEL FUNCTIONS ====================

const carouselStates = {};

function initializeCarousels() {
    document.querySelectorAll('.project-carousel').forEach(carousel => {
        const id = carousel.id;
        if (!carouselStates[id]) {
            carouselStates[id] = { currentIndex: 0 };
        }
    });
}

window.moveCarousel = function(carouselId, direction) {
    const carousel = document.getElementById(carouselId);
    if (!carousel) return;
    
    const slides = carousel.querySelector('.carousel-slides');
    const totalSlides = slides.children.length;
    
    if (!carouselStates[carouselId]) {
        carouselStates[carouselId] = { currentIndex: 0 };
    }
    
    let currentIndex = carouselStates[carouselId].currentIndex;
    currentIndex = (currentIndex + direction + totalSlides) % totalSlides;
    carouselStates[carouselId].currentIndex = currentIndex;
    
    updateCarousel(carouselId);
};

window.goToSlide = function(carouselId, index) {
    if (!carouselStates[carouselId]) {
        carouselStates[carouselId] = { currentIndex: 0 };
    }
    
    carouselStates[carouselId].currentIndex = index;
    updateCarousel(carouselId);
};

function updateCarousel(carouselId) {
    const carousel = document.getElementById(carouselId);
    if (!carousel) return;
    
    const slides = carousel.querySelector('.carousel-slides');
    const indicators = carousel.querySelectorAll('.carousel-indicator');
    const currentIndex = carouselStates[carouselId].currentIndex;
    
    slides.style.transform = `translateX(-${currentIndex * 100}%)`;
    
    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentIndex);
    });
}
