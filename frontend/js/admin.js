// Admin Panel JavaScript
// API Base URL
const API_URL = window.API_URL;

// State
let authToken = sessionStorage.getItem('authToken') || null;
let currentProject = null;
let currentExperience = null;
let currentSkill = null;
let projectTechnologies = [];
let selectedImages = []; // Array of selected image URLs

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    // CRITICAL: Prevent browser from opening dropped files
    window.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
    }, false);
    
    window.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
    }, false);
    
    if (authToken) {
        showDashboard();
        loadAllData();
    } else {
        showLogin();
    }
    
    setupEventListeners();
});

function setupEventListeners() {
    // Login
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Tabs
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Forms - prevent default submission
    const projectForm = document.getElementById('project-form');
    
    // Use click event on save button instead of form submit
    document.getElementById('project-save-btn').addEventListener('click', handleProjectSubmit);
    
    projectForm.addEventListener('submit', (e) => {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        console.log('[ADMIN] Form submit prevented');
        return false;
    });
    
    // Prevent any accidental form submission
    projectForm.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
            return false;
        }
    });
    
    // Prevent drag-drop from submitting form
    projectForm.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('[ADMIN] Drop event on form prevented');
        return false;
    });
    
    projectForm.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        return false;
    });
    
    document.getElementById('experience-form').addEventListener('submit', handleExperienceSubmit);
    document.getElementById('skill-form').addEventListener('submit', handleSkillSubmit);
    document.getElementById('about-form').addEventListener('submit', handleAboutSubmit);
    
    // Cancel buttons
    document.getElementById('project-cancel-btn').addEventListener('click', resetProjectForm);
    document.getElementById('experience-cancel-btn').addEventListener('click', resetExperienceForm);
    document.getElementById('skill-cancel-btn').addEventListener('click', resetSkillForm);
    
    // Technology input
    setupTechInput();
    
    // File upload
    setupFileUpload();
    
    // Backup button
    document.getElementById('backup-btn').addEventListener('click', handleBackup);
    
    // Restore button
    document.getElementById('restore-btn').addEventListener('click', () => {
        document.getElementById('restore-file-input').click();
    });
    
    document.getElementById('restore-file-input').addEventListener('change', handleRestore);

    setupApiUrlControls();
}

// ==================== AUTHENTICATION ====================

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    
    // Create Basic Auth token
    const token = btoa(`${username}:${password}`);
    
    try {
        // Test authentication with verify endpoint
        const response = await fetch(`${API_URL}/api/admin/verify`, {
            headers: {
                'Authorization': `Basic ${token}`
            }
        });
        
        if (response.ok) {
            authToken = token;
            sessionStorage.setItem('authToken', token);
            showDashboard();
            loadAllData();
        } else if (response.status === 401) {
            errorDiv.textContent = 'Invalid username or password';
            errorDiv.style.display = 'block';
        } else {
            errorDiv.textContent = 'Server error. Please try again.';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Failed to connect to server. Make sure backend is running at http://localhost:8000';
        errorDiv.style.display = 'block';
    }
}

function handleLogout() {
    authToken = null;
    sessionStorage.removeItem('authToken');
    showLogin();
}

function showLogin() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('admin-dashboard').style.display = 'none';
}

function showDashboard() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('admin-dashboard').style.display = 'block';
}

function setupApiUrlControls() {
    const input = document.getElementById('api-url-input');
    const saveBtn = document.getElementById('api-url-save');
    const resetBtn = document.getElementById('api-url-reset');
    const status = document.getElementById('api-url-status');

    if (!input || !saveBtn || !resetBtn || !status) return;

    input.value = window.API_URL || '';

    function showStatus(message, isError = false) {
        status.textContent = message;
        status.style.display = 'block';
        status.style.color = isError ? '#ff6b6b' : '#64ffda';
    }

    saveBtn.addEventListener('click', () => {
        const value = input.value.trim();
        if (!value) {
            showStatus('Please enter a valid URL', true);
            return;
        }
        try {
            const url = new URL(value);
            if (!['http:', 'https:'].includes(url.protocol)) {
                showStatus('URL must start with http or https', true);
                return;
            }
            localStorage.setItem('API_URL', url.toString().replace(/\/+$/, ''));
            showStatus('Saved. Reloading...');
            window.location.reload();
        } catch (e) {
            showStatus('Invalid URL format', true);
        }
    });

    resetBtn.addEventListener('click', () => {
        localStorage.removeItem('API_URL');
        showStatus('Reset. Reloading...');
        window.location.reload();
    });
}

// ==================== API CALLS ====================

async function apiCall(endpoint, method = 'GET', body = null) {
    console.log(`[API] Calling ${method} ${endpoint}`);
    
    if (endpoint.startsWith('/api/admin') && !authToken) {
        throw new Error('Unauthorized');
    }
    
    const options = {
        method,
        headers: {
            'Authorization': `Basic ${authToken}`,
        }
    };
    
    if (body && !(body instanceof FormData)) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
        console.log('[API] Request body:', body);
    } else if (body) {
        options.body = body;
    }
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        console.log(`[API] Response status: ${response.status}`);
        
        if (response.status === 401) {
            handleLogout();
            throw new Error('Unauthorized');
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[API] Error response:', errorText);
            let error;
            try {
                error = JSON.parse(errorText);
            } catch {
                error = { detail: errorText };
            }
            throw new Error(error.detail || 'Request failed');
        }
        
        const result = await response.json();
        console.log('[API] Response data:', result);
        return result;
    } catch (error) {
        console.error('[API] Request failed:', error);
        throw error;
    }
}

// ==================== LOAD DATA ====================

async function loadAllData() {
    try {
        await Promise.all([
            loadProjects(),
            loadExperience(),
            loadSkills(),
            loadAbout(),
            loadContacts()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
        showNotification('Failed to load data', 'error');
    }
}

async function loadProjects() {
    try {
        const projects = await apiCall('/api/projects');
        renderProjectsList(projects);
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

async function loadExperience() {
    try {
        const experience = await apiCall('/api/experience');
        renderExperienceList(experience);
    } catch (error) {
        console.error('Error loading experience:', error);
    }
}

async function loadSkills() {
    try {
        const skills = await apiCall('/api/skills');
        renderSkillsList(skills);
    } catch (error) {
        console.error('Error loading skills:', error);
    }
}

async function loadAbout() {
    try {
        const about = await apiCall('/api/about');
        if (about && about.id) {
            document.getElementById('about-bio').value = about.bio || '';
            document.getElementById('about-company').value = about.current_company || '';
            document.getElementById('about-role').value = about.current_role || '';
        }
    } catch (error) {
        console.error('Error loading about:', error);
    }
}

async function loadContacts() {
    try {
        const contacts = await apiCall('/api/admin/contacts');
        renderContactsList(contacts);
    } catch (error) {
        console.error('Error loading contacts:', error);
    }
}

// ==================== RENDER FUNCTIONS ====================

function renderProjectsList(projects) {
    const container = document.getElementById('projects-list');
    
    if (projects.length === 0) {
        container.innerHTML = '<p style="color: var(--slate);">No projects yet. Add your first project above!</p>';
        return;
    }
    
    container.innerHTML = projects.map(project => `
        <div class="data-item">
            <div class="data-item-content">
                <div class="data-item-title">${project.title} ${project.is_featured ? '<span class="tag">Featured</span>' : ''}</div>
                <div class="data-item-description">${project.description}</div>
                <div class="data-item-tags">
                    ${project.technologies.map(tech => `<span class="tag">${tech}</span>`).join('')}
                </div>
            </div>
            <div class="data-item-actions">
                <button class="btn btn-small" onclick="editProject(${project.id})">Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteProject(${project.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function renderExperienceList(experiences) {
    const container = document.getElementById('experience-list');
    
    if (experiences.length === 0) {
        container.innerHTML = '<p style="color: var(--slate);">No experience entries yet. Add your first entry above!</p>';
        return;
    }
    
    container.innerHTML = experiences.map(exp => `
        <div class="data-item">
            <div class="data-item-content">
                <div class="data-item-title">${exp.role} @ ${exp.company}</div>
                <div class="data-item-meta">${exp.date_range}</div>
                <ul style="color: var(--light-slate); padding-left: 20px; margin-top: 10px;">
                    ${exp.responsibilities.map(resp => `<li>${resp}</li>`).join('')}
                </ul>
            </div>
            <div class="data-item-actions">
                <button class="btn btn-small" onclick="editExperience(${exp.id})">Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteExperience(${exp.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function renderSkillsList(skills) {
    const container = document.getElementById('skills-list');
    
    if (skills.length === 0) {
        container.innerHTML = '<p style="color: var(--slate);">No skills yet. Add your first skill above!</p>';
        return;
    }
    
    // Group skills by category
    const grouped = skills.reduce((acc, skill) => {
        const category = skill.category || 'Other';
        if (!acc[category]) acc[category] = [];
        acc[category].push(skill);
        return acc;
    }, {});
    
    container.innerHTML = Object.entries(grouped).map(([category, categorySkills]) => `
        <div style="margin-bottom: 20px;">
            <h4 style="color: var(--green); font-family: var(--font-mono); margin-bottom: 10px;">${category}</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                ${categorySkills.map(skill => `
                    <div class="data-item" style="margin: 0; padding: 10px 15px; flex-direction: row; align-items: center; gap: 10px;">
                        <span style="color: var(--lightest-slate);">${skill.name}</span>
                        <div style="display: flex; gap: 5px;">
                            <button class="btn btn-small" onclick="editSkill(${skill.id})" style="padding: 4px 8px; font-size: 11px;">Edit</button>
                            <button class="btn btn-small btn-danger" onclick="deleteSkill(${skill.id})" style="padding: 4px 8px; font-size: 11px;">Delete</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function renderContactsList(contacts) {
    const container = document.getElementById('contacts-list');
    
    if (contacts.length === 0) {
        container.innerHTML = '<p style="color: var(--slate);">No contact submissions yet.</p>';
        return;
    }
    
    container.innerHTML = contacts.map(contact => `
        <div class="contact-item">
            <div class="contact-header">
                <div class="contact-name">${contact.name}</div>
                <div>
                    <span class="status-badge ${contact.email_sent ? 'sent' : 'pending'}">
                        ${contact.email_sent ? 'Email Sent' : 'Pending'}
                    </span>
                    <span class="contact-date">${new Date(contact.created_at).toLocaleString()}</span>
                    <button onclick="deleteContact(${contact.id})" class="btn-delete-small" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="contact-email"><a href="mailto:${contact.email}">${contact.email}</a></div>
            ${contact.subject ? `<div class="contact-subject">Subject: ${contact.subject}</div>` : ''}
            <div class="contact-message">${contact.message}</div>
        </div>
    `).join('');
}

window.deleteContact = async function(id) {
    if (!confirm('Are you sure you want to delete this contact submission?')) {
        return;
    }
    
    try {
        await apiCall(`/api/admin/contacts/${id}`, 'DELETE');
        alert('Contact deleted successfully');
        loadContacts();
    } catch (error) {
        console.error('Error deleting contact:', error);
        alert('Failed to delete contact');
    }
};

// ==================== PROJECT CRUD ====================

window.editProject = async function(id) {
    try {
        const projects = await apiCall('/api/projects');
        const project = projects.find(p => p.id === id);
        
        if (!project) return;
        
        currentProject = project;
        projectTechnologies = [...project.technologies];
        
        document.getElementById('project-id').value = project.id;
        document.getElementById('project-title').value = project.title;
        document.getElementById('project-description').value = project.description;
        document.getElementById('project-featured').checked = project.is_featured;
        document.getElementById('project-github').value = project.github_url || '';
        document.getElementById('project-external').value = project.external_url || '';
        document.getElementById('project-image-url').value = project.image_url || '';
        document.getElementById('project-order').value = project.display_order;
        
        renderTechTags();
        
        // Handle image URLs
        if (project.image_urls && project.image_urls.length > 0) {
            selectedImages = [...project.image_urls];
        } else if (project.image_url) {
            selectedImages = [project.image_url];
        } else {
            selectedImages = [];
        }
        
        // Render selected images
        if (window.renderSelectedImages) {
            window.renderSelectedImages();
        }
        
        document.getElementById('project-form-title').textContent = 'Edit Project';
        document.getElementById('project-cancel-btn').style.display = 'inline-block';
        
        // Scroll to form
        document.getElementById('project-form').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error loading project:', error);
        showNotification('Failed to load project', 'error');
    }
};

window.deleteProject = async function(id) {
    if (!confirm('Are you sure you want to delete this project?')) return;
    
    try {
        await apiCall(`/api/admin/projects/${id}`, 'DELETE');
        showNotification('Project deleted successfully', 'success');
        loadProjects();
    } catch (error) {
        console.error('Error deleting project:', error);
        showNotification('Failed to delete project', 'error');
    }
};

async function handleProjectSubmit(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    console.log('[ADMIN] Project form submitted');
    
    if (projectTechnologies.length === 0) {
        showNotification('Please add at least one technology', 'error');
        return false;
    }
    
    const projectData = {
        title: document.getElementById('project-title').value,
        description: document.getElementById('project-description').value,
        technologies: projectTechnologies,
        github_url: document.getElementById('project-github').value || null,
        external_url: document.getElementById('project-external').value || null,
        image_url: selectedImages.length > 0 ? selectedImages[0] : null, // First image for backward compatibility
        image_urls: selectedImages.length > 0 ? selectedImages : null,
        is_featured: document.getElementById('project-featured').checked,
        display_order: parseInt(document.getElementById('project-order').value)
    };
    
    console.log('[ADMIN] Project data:', projectData);
    
    try {
        const projectId = document.getElementById('project-id').value;
        
        if (projectId) {
            // Update existing
            console.log('[ADMIN] Updating project:', projectId);
            const result = await apiCall(`/api/admin/projects/${projectId}`, 'PUT', projectData);
            console.log('[ADMIN] Update result:', result);
            showNotification('Project updated successfully', 'success');
        } else {
            // Create new
            console.log('[ADMIN] Creating new project');
            const result = await apiCall('/api/admin/projects', 'POST', projectData);
            console.log('[ADMIN] Create result:', result);
            showNotification('Project created successfully', 'success');
        }
        
        resetProjectForm();
        await loadProjects();
        console.log('[ADMIN] Projects reloaded');
    } catch (error) {
        console.error('[ADMIN] Error saving project:', error);
        showNotification(`Failed to save project: ${error.message}`, 'error');
    }
}

function resetProjectForm() {
    document.getElementById('project-form').reset();
    document.getElementById('project-id').value = '';
    document.getElementById('project-form-title').textContent = 'Add New Project';
    document.getElementById('project-cancel-btn').style.display = 'none';
    
    // Reset selected images
    selectedImages = [];
    const selectedContainer = document.getElementById('selected-images-container');
    if (selectedContainer) {
        selectedContainer.style.display = 'none';
    }
    
    projectTechnologies = [];
    renderTechTags();
    currentProject = null;
}

// ==================== EXPERIENCE CRUD ====================

window.editExperience = async function(id) {
    try {
        const experiences = await apiCall('/api/experience');
        const experience = experiences.find(e => e.id === id);
        
        if (!experience) return;
        
        currentExperience = experience;
        
        document.getElementById('experience-id').value = experience.id;
        document.getElementById('experience-company').value = experience.company;
        document.getElementById('experience-company-url').value = experience.company_url || '';
        document.getElementById('experience-role').value = experience.role;
        document.getElementById('experience-date').value = experience.date_range;
        document.getElementById('experience-responsibilities').value = experience.responsibilities.join('\n');
        document.getElementById('experience-order').value = experience.display_order;
        
        document.getElementById('experience-form-title').textContent = 'Edit Experience';
        document.getElementById('experience-cancel-btn').style.display = 'inline-block';
        
        document.getElementById('experience-form').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error loading experience:', error);
        showNotification('Failed to load experience', 'error');
    }
};

window.deleteExperience = async function(id) {
    if (!confirm('Are you sure you want to delete this experience entry?')) return;
    
    try {
        await apiCall(`/api/admin/experience/${id}`, 'DELETE');
        showNotification('Experience deleted successfully', 'success');
        loadExperience();
    } catch (error) {
        console.error('Error deleting experience:', error);
        showNotification('Failed to delete experience', 'error');
    }
};

async function handleExperienceSubmit(e) {
    e.preventDefault();
    
    console.log('[EXPERIENCE] Form submitted');
    
    const responsibilities = document.getElementById('experience-responsibilities').value
        .split('\n')
        .filter(r => r.trim())
        .map(r => r.trim());
    
    console.log('[EXPERIENCE] Responsibilities:', responsibilities);
    
    if (responsibilities.length === 0) {
        showNotification('Please add at least one responsibility', 'error');
        return;
    }
    
    const experienceData = {
        company: document.getElementById('experience-company').value,
        company_url: document.getElementById('experience-company-url').value || null,
        role: document.getElementById('experience-role').value,
        date_range: document.getElementById('experience-date').value,
        responsibilities: responsibilities,
        display_order: parseInt(document.getElementById('experience-order').value)
    };
    
    console.log('[EXPERIENCE] Data to save:', experienceData);
    
    try {
        const experienceId = document.getElementById('experience-id').value;
        
        if (experienceId) {
            console.log('[EXPERIENCE] Updating experience:', experienceId);
            const result = await apiCall(`/api/admin/experience/${experienceId}`, 'PUT', experienceData);
            console.log('[EXPERIENCE] Update result:', result);
            showNotification('Experience updated successfully', 'success');
        } else {
            console.log('[EXPERIENCE] Creating new experience');
            const result = await apiCall('/api/admin/experience', 'POST', experienceData);
            console.log('[EXPERIENCE] Create result:', result);
            showNotification('Experience created successfully', 'success');
        }
        
        resetExperienceForm();
        await loadExperience();
        console.log('[EXPERIENCE] Experience list reloaded');
    } catch (error) {
        console.error('[EXPERIENCE] Error saving experience:', error);
        showNotification(`Failed to save experience: ${error.message}`, 'error');
    }
}

function resetExperienceForm() {
    document.getElementById('experience-form').reset();
    document.getElementById('experience-id').value = '';
    document.getElementById('experience-form-title').textContent = 'Add New Experience';
    document.getElementById('experience-cancel-btn').style.display = 'none';
    currentExperience = null;
}

// ==================== SKILL CRUD ====================

window.editSkill = async function(id) {
    try {
        const skills = await apiCall('/api/skills');
        const skill = skills.find(s => s.id === id);
        
        if (!skill) return;
        
        currentSkill = skill;
        
        document.getElementById('skill-id').value = skill.id;
        document.getElementById('skill-name').value = skill.name;
        document.getElementById('skill-category').value = skill.category || '';
        
        document.getElementById('skill-form-title').textContent = 'Edit Skill';
        document.getElementById('skill-cancel-btn').style.display = 'inline-block';
        
        document.getElementById('skill-form').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error loading skill:', error);
        showNotification('Failed to load skill', 'error');
    }
};

window.deleteSkill = async function(id) {
    if (!confirm('Are you sure you want to delete this skill?')) return;
    
    try {
        await apiCall(`/api/admin/skills/${id}`, 'DELETE');
        showNotification('Skill deleted successfully', 'success');
        loadSkills();
    } catch (error) {
        console.error('Error deleting skill:', error);
        showNotification('Failed to delete skill', 'error');
    }
};

async function handleSkillSubmit(e) {
    e.preventDefault();
    
    const skillData = {
        name: document.getElementById('skill-name').value,
        category: document.getElementById('skill-category').value || null
    };
    
    try {
        const skillId = document.getElementById('skill-id').value;
        
        if (skillId) {
            await apiCall(`/api/admin/skills/${skillId}`, 'PUT', skillData);
            showNotification('Skill updated successfully', 'success');
        } else {
            await apiCall('/api/admin/skills', 'POST', skillData);
            showNotification('Skill created successfully', 'success');
        }
        
        resetSkillForm();
        loadSkills();
    } catch (error) {
        console.error('Error saving skill:', error);
        showNotification('Failed to save skill', 'error');
    }
}

function resetSkillForm() {
    document.getElementById('skill-form').reset();
    document.getElementById('skill-id').value = '';
    document.getElementById('skill-form-title').textContent = 'Add New Skill';
    document.getElementById('skill-cancel-btn').style.display = 'none';
    currentSkill = null;
}

// ==================== ABOUT ====================

async function handleAboutSubmit(e) {
    e.preventDefault();
    
    const aboutData = {
        bio: document.getElementById('about-bio').value,
        current_company: document.getElementById('about-company').value || null,
        current_role: document.getElementById('about-role').value || null
    };
    
    try {
        await apiCall('/api/admin/about', 'POST', aboutData);
        showNotification('About section updated successfully', 'success');
    } catch (error) {
        console.error('Error saving about:', error);
        showNotification('Failed to save about section', 'error');
    }
}

// ==================== TECHNOLOGY TAGS ====================

function setupTechInput() {
    const input = document.getElementById('project-tech-input');
    
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const value = input.value.trim();
            if (value && !projectTechnologies.includes(value)) {
                projectTechnologies.push(value);
                renderTechTags();
                input.value = '';
            }
        }
    });
}

function renderTechTags() {
    const container = document.getElementById('project-tech-container');
    const input = document.getElementById('project-tech-input');
    
    const tagsHTML = projectTechnologies.map((tech, index) => `
        <div class="tech-tag">
            ${tech}
            <button type="button" onclick="removeTech(${index})">&times;</button>
        </div>
    `).join('');
    
    container.innerHTML = tagsHTML;
    container.appendChild(input);
}

window.removeTech = function(index) {
    projectTechnologies.splice(index, 1);
    renderTechTags();
};

// ==================== FILE UPLOAD ====================

function setupFileUpload() {
    const urlInput = document.getElementById('project-image-url-input');
    const addBtn = document.getElementById('add-image-url-btn');
    const selectedContainer = document.getElementById('selected-images-container');
    const selectedList = document.getElementById('selected-images-list');

    if (!urlInput || !addBtn || !selectedContainer || !selectedList) {
        console.error('[UPLOAD] Required elements not found');
        return;
    }

    console.log('[UPLOAD] URL-only image selection initialized');

    addBtn.addEventListener('click', () => {
        const value = urlInput.value.trim();
        if (!value) {
            showNotification('Please enter an image URL', 'error');
            return;
        }
        try {
            const url = new URL(value);
            if (!['http:', 'https:'].includes(url.protocol)) {
                showNotification('URL must start with http or https', 'error');
                return;
            }
            if (!selectedImages.includes(url.toString())) {
                selectedImages.push(url.toString());
                renderSelectedImages();
                showNotification('Image added', 'success');
            }
            urlInput.value = '';
        } catch (e) {
            showNotification('Invalid URL format', 'error');
        }
    });

    // Render selected images with drag-and-drop reordering
    function renderSelectedImages() {
        if (selectedImages.length === 0) {
            selectedContainer.style.display = 'none';
            return;
        }
        
        selectedContainer.style.display = 'block';
        selectedList.innerHTML = selectedImages.map((url, index) => `
            <div class="selected-image-item" draggable="true" data-index="${index}" data-url="${url}">
                <img src="${url.startsWith('/') ? API_URL + url : url}" alt="Image ${index + 1}">
                <button class="selected-image-remove" onclick="removeSelectedImage(${index})" type="button">×</button>
                <span class="selected-image-order">${index + 1}</span>
            </div>
        `).join('');
        
        // Setup drag and drop for reordering
        setupDragAndDrop();
    }
    
    // Remove selected image (global)
    window.removeSelectedImage = function(index) {
        selectedImages.splice(index, 1);
        renderSelectedImages();
    };
    
    // Setup drag and drop for reordering
    function setupDragAndDrop() {
        const items = selectedList.querySelectorAll('.selected-image-item');
        let draggedElement = null;
        
        items.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                draggedElement = item;
                e.dataTransfer.effectAllowed = 'move';
                item.style.opacity = '0.5';
            });
            
            item.addEventListener('dragend', () => {
                item.style.opacity = '1';
                // Update array based on final DOM order
                const newOrder = Array.from(selectedList.querySelectorAll('.selected-image-item'))
                    .map(el => el.dataset.url);
                selectedImages = newOrder;
                renderSelectedImages();
            });
            
            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                if (draggedElement === item) return;
                
                const rect = item.getBoundingClientRect();
                const midpoint = rect.left + rect.width / 2;
                
                if (e.clientX < midpoint) {
                    selectedList.insertBefore(draggedElement, item);
                } else {
                    selectedList.insertBefore(draggedElement, item.nextSibling);
                }
            });
        });
    }
    
    // Initialize rendering if project is being edited
    window.renderSelectedImages = renderSelectedImages;
}

// ==================== BACKUP ====================

async function handleBackup() {
    try {
        const result = await apiCall('/api/admin/backup');
        
        if (result.success) {
            // Download the backup
            window.location.href = `${API_URL}${result.download_url}`;
            showNotification(`Backup created: ${result.filename}`, 'success');
        }
    } catch (error) {
        console.error('Backup error:', error);
        showNotification('Failed to create backup', 'error');
    }
}

async function handleRestore(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.json')) {
        alert('Please select a valid .json file');
        return;
    }
    
    if (!confirm('⚠️ WARNING: This will replace your current database with the uploaded file. A backup of the current database will be created automatically. Continue?')) {
        event.target.value = ''; // Reset file input
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_URL}/api/admin/restore`, {
            method: 'POST',
            headers: {
                'Authorization': `Basic ${authToken}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Restore failed');
        }
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ Database restored successfully!\n\nBackup of old database: ${result.backup_created}\n\nThe page will reload to show the new data.`);
            window.location.href = window.location.pathname;
        }
    } catch (error) {
        console.error('Restore error:', error);
        alert('❌ Failed to restore database');
    } finally {
        event.target.value = ''; // Reset file input
    }
}

// ==================== TABS ====================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ==================== IMAGES MANAGEMENT ====================
// Removed for URL-only image support.

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 4000);
}
