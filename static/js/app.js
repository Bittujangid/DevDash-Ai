/**
 * ============================================================================
 * DevDash AI - Client-side SPA Architecture & Fetch API Handlers
 * ============================================================================
 */

// Main application class to manage state, routing, DOM rendering, and API calls
class DevDashApp {
    constructor() {
        this.currentUser = null;
        this.activeTab = 'overview-panel';
        this.allResources = []; // Cache for category filter
        
        // DOM Caches
        this.authView = document.getElementById('auth-view');
        this.dashboardView = document.getElementById('dashboard-view');
        this.loginForm = document.getElementById('login-form');
        this.registerForm = document.getElementById('register-form');
        this.authToggle = document.getElementById('auth-toggle');
        this.authSubtitle = document.getElementById('auth-subtitle');
        this.authFooterText = document.getElementById('auth-footer-text');
        
        // Bind UI Events
        this.initEvents();
    }

    // Initialize application and perform session verification
    async init() {
        this.showLoader();
        try {
            const res = await fetch('/api/auth/status');
            const data = await res.json();
            
            if (data.authenticated) {
                this.currentUser = data.user;
                this.setupUserUI();
                await this.fetchSettings();
                this.switchView('dashboard');
                // Fetch dashboard data
                await this.refreshAllData();
            } else {
                this.switchView('auth');
            }
        } catch (error) {
            console.error("Initialization check failed:", error);
            this.showToast("Failed to connect to the backend server.", "error");
            this.switchView('auth');
        } finally {
            this.hideLoader();
        }
    }

    // Establish Form Submit Handlers, Button Clicks, and Listeners
    initEvents() {
        // Toggle Sign In vs Sign Up forms
        if (this.authToggle) {
            this.authToggle.addEventListener('click', () => this.toggleAuthForms());
        }

        // Login Submit
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Register Submit
        if (this.registerForm) {
            this.registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Logout Button Click
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Sidebar Navigation Toggles
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const isLogout = e.currentTarget.id === 'nav-logout';
                if (isLogout) {
                    this.handleLogout();
                } else {
                    const target = e.currentTarget.getAttribute('data-target');
                    if (target) {
                        this.switchTab(target, e.currentTarget.id);
                    }
                }
                
                // Automatically dismiss mobile sidebar on link clicks
                const sidebar = document.getElementById('sidebar');
                const sidebarOverlay = document.getElementById('sidebar-overlay');
                if (sidebar) sidebar.classList.remove('open');
                if (sidebarOverlay) sidebarOverlay.classList.remove('active');
            });
        });

        // Mobile Header Sidebar Toggle Trigger
        const menuToggleBtn = document.getElementById('menu-toggle-btn');
        const sidebarOverlay = document.getElementById('sidebar-overlay');
        const sidebar = document.getElementById('sidebar');
        
        if (menuToggleBtn && sidebar && sidebarOverlay) {
            menuToggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
                sidebarOverlay.classList.toggle('active');
            });
        }
        
        if (sidebarOverlay && sidebar) {
            sidebarOverlay.addEventListener('click', () => {
                sidebar.classList.remove('open');
                sidebarOverlay.classList.remove('active');
            });
        }

        // Collapsible Sidebar Desktop Toggling
        const sidebarToggleBtn = document.getElementById('sidebar-collapse-toggle');
        const layout = document.querySelector('.dashboard-layout');
        
        // Load persisted sidebar state from localStorage
        const isCollapsedPersisted = localStorage.getItem('sidebar-collapsed') === 'true';
        if (isCollapsedPersisted && layout) {
            layout.classList.add('collapsed-desktop');
            if (sidebarToggleBtn) {
                const icon = sidebarToggleBtn.querySelector('i');
                if (icon) {
                    icon.className = 'fa-solid fa-chevron-right';
                }
            }
        }

        if (sidebarToggleBtn && layout) {
            sidebarToggleBtn.addEventListener('click', () => {
                layout.classList.toggle('collapsed-desktop');
                const isCollapsed = layout.classList.contains('collapsed-desktop');
                localStorage.setItem('sidebar-collapsed', isCollapsed);
                
                const icon = sidebarToggleBtn.querySelector('i');
                if (icon) {
                    if (isCollapsed) {
                        icon.className = 'fa-solid fa-chevron-right';
                    } else {
                        icon.className = 'fa-solid fa-chevron-left';
                    }
                }
            });
        }

        // Back/Home Navigation triggers on Logo click
        const sidebarLogoHome = document.getElementById('sidebar-logo-home');
        const mobileLogoHome = document.getElementById('mobile-logo-home');
        
        if (sidebarLogoHome) {
            sidebarLogoHome.addEventListener('click', () => {
                this.switchTab('overview-panel');
            });
        }
        if (mobileLogoHome) {
            mobileLogoHome.addEventListener('click', () => {
                this.switchTab('overview-panel');
            });
        }

        // Add Goal form submit
        const addGoalForm = document.getElementById('add-goal-form');
        if (addGoalForm) {
            addGoalForm.addEventListener('submit', (e) => this.handleAddGoal(e));
        }

        // Saved Resource Modal actions
        const openModalBtn = document.getElementById('open-add-resource-modal');
        const closeModalBtn = document.getElementById('close-add-resource-modal');
        const modal = document.getElementById('add-resource-modal');
        const addResForm = document.getElementById('add-resource-form');

        if (openModalBtn && modal) {
            openModalBtn.addEventListener('click', () => modal.classList.add('active'));
        }
        if (closeModalBtn && modal) {
            closeModalBtn.addEventListener('click', () => modal.classList.remove('active'));
        }
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.classList.remove('active');
            });
        }
        if (addResForm) {
            addResForm.addEventListener('submit', (e) => this.handleAddResource(e));
        }

        // AI Chat Form submit
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        }

        // Chat Hamburger Menu Toggle
        const chatMenuBtn = document.getElementById('chat-menu-btn');
        if (chatMenuBtn && sidebar && sidebarOverlay && layout) {
            chatMenuBtn.addEventListener('click', () => {
                if (window.innerWidth <= 1024) {
                    sidebar.classList.toggle('open');
                    sidebarOverlay.classList.toggle('active');
                } else {
                    layout.classList.toggle('collapsed-desktop');
                    const isCollapsed = layout.classList.contains('collapsed-desktop');
                    localStorage.setItem('sidebar-collapsed', isCollapsed);
                    if (sidebarToggleBtn) {
                        const icon = sidebarToggleBtn.querySelector('i');
                        if (icon) {
                            icon.className = isCollapsed ? 'fa-solid fa-chevron-right' : 'fa-solid fa-chevron-left';
                        }
                    }
                }
            });
        }

        // Clear Chat History
        const clearChatBtn = document.getElementById('clear-chat-btn');
        const chatContainer = document.getElementById('chat-messages-container');
        if (clearChatBtn && chatContainer) {
            clearChatBtn.addEventListener('click', () => {
                chatContainer.innerHTML = `
                    <div class="chat-bubble ai">
                        <h3 style="font-size: 1.05rem; margin-bottom: 8px;"><i class="fa-solid fa-square-terminal brand-text" style="margin-right: 6px;"></i> DevDash AI Assistant</h3>
                        <p>Hi there! I am your AI coding assistant, backed by Google Gemini. Ask me any programming questions, let's debug a code block, map out a learning roadmap, or analyze data structures.</p>
                    </div>
                `;
                this.showToast("Chat history cleared.", "success");
            });
        }

        // Refresh Chat Session
        const refreshChatBtn = document.getElementById('refresh-chat-btn');
        if (refreshChatBtn) {
            refreshChatBtn.addEventListener('click', () => {
                this.showLoader();
                setTimeout(() => {
                    if (chatContainer) {
                        chatContainer.innerHTML = `
                            <div class="chat-bubble ai">
                                <h3 style="font-size: 1.05rem; margin-bottom: 8px;"><i class="fa-solid fa-square-terminal brand-text" style="margin-right: 6px;"></i> DevDash AI Assistant</h3>
                                <p>Hi there! I am your AI coding assistant, backed by Google Gemini. Ask me any programming questions, let's debug a code block, map out a learning roadmap, or analyze data structures.</p>
                            </div>
                        `;
                    }
                    this.hideLoader();
                    this.showToast("Chat session refreshed successfully.", "success");
                }, 800);
            });
        }

        // Multi-line Textarea Key & Input Handler
        const chatMessageInput = document.getElementById('chat-message-input');
        if (chatMessageInput) {
            chatMessageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (chatForm) {
                        chatForm.dispatchEvent(new Event('submit'));
                    }
                }
            });

            chatMessageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        }

        // Profile Form Submit
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => this.handleProfileUpdate(e));
        }

        // Global Refresh Dashboard stats button
        const refreshBtn = document.getElementById('refresh-stats-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                refreshBtn.querySelector('i').classList.add('fa-spin');
                this.refreshAllData().finally(() => {
                    setTimeout(() => refreshBtn.querySelector('i').classList.remove('fa-spin'), 600);
                });
            });
        }
    }

    // Toggle between registration and login forms
    toggleAuthForms() {
        if (this.loginForm.classList.contains('hidden')) {
            // Switch to Login Form
            this.loginForm.classList.remove('hidden');
            this.registerForm.classList.add('hidden');
            this.authSubtitle.innerText = "Welcome! Log in to access your custom developer workspace.";
            this.authFooterText.innerText = "Don't have an account?";
            this.authToggle.innerText = "Register";
        } else {
            // Switch to Registration Form
            this.loginForm.classList.add('hidden');
            this.registerForm.classList.remove('hidden');
            this.authSubtitle.innerText = "Sign up for a DevDash account to begin tracking your programming success.";
            this.authFooterText.innerText = "Already registered?";
            this.authToggle.innerText = "Log In";
        }
    }

    // Switch major application states (Auth vs Dashboard)
    switchView(view) {
        if (view === 'dashboard') {
            this.authView.classList.add('hidden');
            this.dashboardView.classList.remove('hidden');
        } else {
            this.authView.classList.remove('hidden');
            this.dashboardView.classList.add('hidden');
            this.currentUser = null;
        }
    }

    // Handle session expiration or unauthorized request
    handleUnauthorized() {
        if (this.currentUser) {
            this.currentUser = null;
            this.showToast("Session expired. Please log in again.", "warning");
            this.switchView('auth');
        }
    }

    // Set up profile details, sidebar username, avatars in UI
    setupUserUI() {
        if (!this.currentUser) return;
        
        // Dynamic time-based greeting for premium SaaS dashboard
        const heroGreeting = document.getElementById('hero-greeting');
        const heroUsername = document.getElementById('hero-username');
        if (heroGreeting && heroUsername) {
            const hour = new Date().getHours();
            let greeting = 'Good Morning';
            if (hour >= 12 && hour < 17) {
                greeting = 'Good Afternoon';
            } else if (hour >= 17) {
                greeting = 'Good Evening';
            }
            heroGreeting.innerText = greeting;
            heroUsername.innerText = this.currentUser.username;
        }

        // Sidebar initials avatar
        const avatarChar = this.currentUser.username.charAt(0).toUpperCase();
        document.getElementById('sidebar-avatar').innerText = avatarChar;
        document.getElementById('sidebar-username').innerText = this.currentUser.username;
        
        // Chat compact initials avatar
        const chatAvatar = document.getElementById('chat-user-avatar');
        if (chatAvatar) {
            chatAvatar.innerText = avatarChar;
        }
        
        // Profile view avatar and preview info
        document.getElementById('profile-avatar-placeholder').innerText = avatarChar;
        document.getElementById('profile-card-username').innerText = this.currentUser.username;
        document.getElementById('profile-card-email').innerText = this.currentUser.email;
        document.getElementById('profile-card-role').innerText = this.currentUser.role || "Developer Workspace";
        document.getElementById('profile-card-bio').innerText = this.currentUser.bio || "No developer bio provided. Write a short paragraph on what you're currently building!";
        
        // Profile inputs population
        document.getElementById('profile-username').value = this.currentUser.username;
        document.getElementById('profile-email').value = this.currentUser.email;
        document.getElementById('profile-role').value = this.currentUser.role || "";
        document.getElementById('profile-github-username').value = this.currentUser.github_username || "";
        document.getElementById('profile-github-link').value = this.currentUser.github_link || "";
        document.getElementById('profile-linkedin-link').value = this.currentUser.linkedin_link || "";
        document.getElementById('profile-portfolio-link').value = this.currentUser.portfolio_link || "";
        document.getElementById('profile-bio').value = this.currentUser.bio || "";
        
        // GitHub button on profile sidebar
        const githubSec = document.getElementById('profile-card-github-sec');
        const githubLink = document.getElementById('profile-card-github-link');
        
        if (this.currentUser.github_link) {
            githubSec.classList.remove('hidden');
            githubLink.href = this.currentUser.github_link;
            githubLink.innerHTML = `<i class="fa-brands fa-github"></i> ${this.currentUser.github_username || 'GitHub'}`;
        } else {
            githubSec.classList.add('hidden');
        }

        // LinkedIn button on profile sidebar
        const linkedinSec = document.getElementById('profile-card-linkedin-sec');
        const linkedinLink = document.getElementById('profile-card-linkedin-link');
        
        if (this.currentUser.linkedin_link) {
            linkedinSec.classList.remove('hidden');
            linkedinLink.href = this.currentUser.linkedin_link;
        } else {
            linkedinSec.classList.add('hidden');
        }

        // Portfolio button on profile sidebar
        const portfolioSec = document.getElementById('profile-card-portfolio-sec');
        const portfolioLink = document.getElementById('profile-card-portfolio-link');
        
        if (this.currentUser.portfolio_link) {
            portfolioSec.classList.remove('hidden');
            portfolioLink.href = this.currentUser.portfolio_link;
        } else {
            portfolioSec.classList.add('hidden');
        }
    }

    // Switch between content panel tabs in the main dashboard view
    switchTab(panelId, activeItemId = null) {
        this.activeTab = panelId;
        
        // Update navigation active state
        document.querySelectorAll('.nav-item').forEach(item => {
            if (activeItemId) {
                if (item.id === activeItemId) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            } else {
                const target = item.getAttribute('data-target');
                if (target === panelId) {
                    if (panelId === 'profile-panel' && item.id === 'nav-settings') {
                        item.classList.remove('active');
                    } else {
                        item.classList.add('active');
                    }
                } else {
                    item.classList.remove('active');
                }
            }
        });

        // Toggle panel display
        document.querySelectorAll('.view-panel').forEach(panel => {
            if (panel.id === panelId) {
                panel.classList.remove('hidden');
            } else {
                panel.classList.add('hidden');
            }
        });

        // Lock overflow on main content for chat panel to prevent double scrollbars and layout shifting
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            if (panelId === 'chat-panel') {
                mainContent.style.overflow = 'hidden';
                mainContent.classList.add('chat-active');
                document.body.classList.add('chat-active-parent');
            } else {
                mainContent.style.overflow = '';
                mainContent.classList.remove('chat-active');
                document.body.classList.remove('chat-active-parent');
            }
        }

        // Set clean title/subtitle headings for the active pane
        const titleEl = document.getElementById('panel-title');
        const subtitleEl = document.getElementById('panel-subtitle');
        
        switch (panelId) {
            case 'overview-panel':
                titleEl.innerText = "Developer Workspace";
                subtitleEl.innerText = "Welcome back to your productivity suite.";
                this.fetchStats();
                break;
            case 'goals-panel':
                titleEl.innerText = "Daily Coding Goals";
                subtitleEl.innerText = "Declare and check off your everyday progress tasks.";
                this.fetchGoals();
                break;
            case 'resources-panel':
                titleEl.innerText = "Saved Resources";
                subtitleEl.innerText = "Archive and reference essential tools, documentations, and guides.";
                this.fetchResources();
                break;
            case 'chat-panel':
                titleEl.innerText = "Gemini Assistant";
                subtitleEl.innerText = "Chat with an advanced AI coding mentor in real-time.";
                break;
            case 'profile-panel':
                titleEl.innerText = "Developer Profile";
                subtitleEl.innerText = "Configure details on your GitHub repository, bio, and credentials.";
                this.setupUserUI();
                break;
            case 'settings-panel':
                titleEl.innerText = "Settings Center";
                subtitleEl.innerText = "Configure appearance, default preferences, and security settings.";
                this.fetchSettings();
                break;
        }
    }

    // Fetch and populate all dashboard data concurrently
    async refreshAllData() {
        try {
            await Promise.all([
                this.fetchStats(),
                this.fetchGoals(),
                this.fetchResources()
            ]);
        } catch (err) {
            console.error("Failed loading initial data:", err);
        }
    }

    // ========================================================================
    // API FETCHER UTILITIES
    // ========================================================================

    // 1. User Registration Flow
    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        
        this.showLoader();
        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            const data = await res.json();
            
            if (data.success) {
                this.showToast(data.message, "success");
                // Clear registration form and switch to login
                this.registerForm.reset();
                this.toggleAuthForms();
            } else {
                this.showToast(data.message || "Registration failed.", "error");
            }
        } catch (error) {
            this.showToast("Connection failed. Try again.", "error");
        } finally {
            this.hideLoader();
        }
    }

    // 2. User Login Flow
    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        this.showLoader();
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if (data.success) {
                this.showToast(data.message, "success");
                this.currentUser = data.user;
                this.setupUserUI();
                await this.fetchSettings();
                this.loginForm.reset();
                this.switchView('dashboard');
                this.switchTab('overview-panel');
                await this.refreshAllData();
            } else {
                this.showToast(data.message || "Authentication failed.", "error");
            }
        } catch (error) {
            this.showToast("Connection failed. Try again.", "error");
        } finally {
            this.hideLoader();
        }
    }

    // 3. User Logout Flow
    async handleLogout() {
        this.showLoader();
        try {
            const res = await fetch('/api/logout', { method: 'POST' });
            const data = await res.json();
            
            if (data.success) {
                this.showToast("Goodbye! Workspace locked.", "info");
                this.switchView('auth');
            } else {
                this.showToast("Logout failed.", "error");
            }
        } catch (error) {
            this.showToast("Network request failed.", "error");
        } finally {
            this.hideLoader();
        }
    }

    // 4. Fetch Statistics
    async fetchStats() {
        try {
            const res = await fetch('/api/dashboard/stats');
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            if (data.success) {
                document.getElementById('stats-total-goals').innerText = data.stats.total_goals;
                document.getElementById('stats-completed-goals').innerText = data.stats.completed_goals;
                document.getElementById('stats-pending-goals').innerText = data.stats.pending_goals;
                document.getElementById('stats-saved-resources').innerText = data.stats.saved_resources;
            }
        } catch (err) {
            console.error("Error fetching stats:", err);
        }
    }

    // 5. Fetch Daily Goals
    async fetchGoals() {
        const container = document.getElementById('goals-list-container');
        try {
            const res = await fetch('/api/goals');
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                if (data.goals.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-list-check"></i>
                            <p>No coding goals set for today. Let's create your first task above!</p>
                        </div>
                    `;
                    return;
                }
                
                let html = '';
                data.goals.forEach(goal => {
                    html += `
                        <div class="glass-panel goal-item ${goal.completed ? 'completed' : ''}" id="goal-item-${goal.id}">
                            <div class="goal-left">
                                <label class="checkbox-container">
                                    <input type="checkbox" ${goal.completed ? 'checked' : ''} onchange="app.toggleGoalComplete(${goal.id}, this.checked)">
                                    <span class="checkmark"></span>
                                </label>
                                <span class="goal-title">${this.escapeHTML(goal.title)}</span>
                                <span class="priority-tag ${goal.priority.toLowerCase()}">${goal.priority}</span>
                            </div>
                            <div class="goal-actions">
                                <button class="btn btn-secondary btn-icon" onclick="app.handleDeleteGoal(${goal.id})" title="Delete Goal">
                                    <i class="fa-solid fa-trash-can" style="color: var(--color-danger);"></i>
                                </button>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            }
        } catch (err) {
            console.error("Error loading goals:", err);
            this.showToast("Failed to load goals checklist.", "error");
        }
    }

    // 6. Add Goal Submit
    async handleAddGoal(e) {
        e.preventDefault();
        const titleInput = document.getElementById('goal-title-input');
        const priorityInput = document.getElementById('goal-priority-input');
        
        const title = titleInput.value.trim();
        const priority = priorityInput.value;
        
        if (!title) return;
        
        try {
            const res = await fetch('/api/goals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, priority })
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                this.showToast("Goal created successfully!", "success");
                titleInput.value = '';
                priorityInput.value = 'Medium';
                await this.fetchGoals();
                await this.fetchStats();
            } else {
                this.showToast(data.message || "Failed to create goal.", "error");
            }
        } catch (error) {
            this.showToast("Goal creation request failed.", "error");
        }
    }

    // 7. Toggle Goal Completed Checked
    async toggleGoalComplete(goalId, isCompleted) {
        const goalEl = document.getElementById(`goal-item-${goalId}`);
        if (goalEl) {
            if (isCompleted) {
                goalEl.classList.add('completed');
            } else {
                goalEl.classList.remove('completed');
            }
        }
        
        try {
            const res = await fetch(`/api/goals/${goalId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ completed: isCompleted })
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                if (isCompleted) {
                    this.showToast("Goal checked off!", "success");
                }
                await this.fetchStats();
            } else {
                this.showToast("Failed updating status.", "error");
                await this.fetchGoals(); // Revert
            }
        } catch (error) {
            this.showToast("Failed communicating with database.", "error");
            await this.fetchGoals(); // Revert
        }
    }

    // 8. Delete Goal
    async handleDeleteGoal(goalId) {
        if (!confirm("Are you sure you want to delete this goal?")) return;
        
        try {
            const res = await fetch(`/api/goals/${goalId}`, {
                method: 'DELETE'
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                this.showToast(data.message, "info");
                await this.fetchGoals();
                await this.fetchStats();
            } else {
                this.showToast("Deletion failed.", "error");
            }
        } catch (error) {
            this.showToast("Server request failed.", "error");
        }
    }

    // 9. Fetch Saved Resources
    async fetchResources() {
        try {
            const res = await fetch('/api/resources');
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                this.allResources = data.resources; // Cache locally for real-time category filtering
                
                // Reset category filter dropdown to 'All'
                const filterDropdown = document.getElementById('res-filter-category');
                if (filterDropdown) {
                    filterDropdown.value = 'All';
                }
                
                this.renderResourcesList(this.allResources);
            }
        } catch (err) {
            console.error("Error fetching bookmarks:", err);
            this.showToast("Failed to load saved resources.", "error");
        }
    }

    // Render list of resources to the grid
    renderResourcesList(resources) {
        const grid = document.getElementById('resources-grid-container');
        if (!grid) return;
        
        if (resources.length === 0) {
            grid.innerHTML = `
                <div class="glass-panel" style="grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--text-muted);">
                    <i class="fa-solid fa-book-bookmark" style="font-size: 3rem; opacity: 0.3; margin-bottom: 15px;"></i>
                    <p>No saved resources found matching the selected category.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        resources.forEach(resItem => {
            html += `
                <div class="glass-panel resource-card">
                    <div>
                        <div class="resource-header">
                            <h4 class="resource-title">${this.escapeHTML(resItem.title)}</h4>
                            <span class="resource-category ${resItem.category.toLowerCase()}">${resItem.category}</span>
                        </div>
                        <p class="resource-desc">${this.escapeHTML(resItem.description || 'No notes added.')}</p>
                    </div>
                    <div class="resource-footer">
                        <a href="${resItem.url}" target="_blank" class="btn btn-secondary" style="padding: 6px 14px; font-size: 0.8rem; gap: 6px;">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Open
                        </a>
                        <button class="btn btn-secondary btn-icon" onclick="app.handleDeleteResource(${resItem.id})" title="Delete Bookmark" style="width: 32px; height: 32px;">
                            <i class="fa-solid fa-trash-can" style="font-size: 0.85rem; color: var(--color-danger);"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        grid.innerHTML = html;
    }

    // Filter resources locally by category
    filterResources(category) {
        if (!this.allResources) return;
        
        if (category === "All") {
            this.renderResourcesList(this.allResources);
        } else {
            const filtered = this.allResources.filter(resItem => resItem.category.toLowerCase() === category.toLowerCase());
            this.renderResourcesList(filtered);
        }
    }

    // 10. Add Resource Form Submit
    async handleAddResource(e) {
        e.preventDefault();
        const title = document.getElementById('res-title-input').value.trim();
        const url = document.getElementById('res-url-input').value.trim();
        const category = document.getElementById('res-category-input').value;
        const description = document.getElementById('res-desc-input').value.trim();
        
        try {
            const res = await fetch('/api/resources', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, url, category, description })
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                this.showToast("Resource bookmarked successfully!", "success");
                document.getElementById('add-resource-form').reset();
                document.getElementById('add-resource-modal').classList.remove('active');
                await this.fetchResources();
                await this.fetchStats();
            } else {
                this.showToast(data.message || "Failed saving resource.", "error");
            }
        } catch (error) {
            this.showToast("Request failed to reach server.", "error");
        }
    }

    // 11. Delete Resource
    async handleDeleteResource(resId) {
        if (!confirm("Are you sure you want to delete this bookmark?")) return;
        
        try {
            const res = await fetch(`/api/resources/${resId}`, { method: 'DELETE' });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                this.showToast(data.message, "info");
                await this.fetchResources();
                await this.fetchStats();
            } else {
                this.showToast("Deletion failed.", "error");
            }
        } catch (error) {
            this.showToast("Request to database failed.", "error");
        }
    }

    // 12. Update Profile Details Submit
    async handleProfileUpdate(e) {
        e.preventDefault();
        
        const username = document.getElementById('profile-username').value.trim();
        const email = document.getElementById('profile-email').value.trim();
        const role = document.getElementById('profile-role').value.trim();
        const github_username = document.getElementById('profile-github-username').value.trim();
        const github_link = document.getElementById('profile-github-link').value.trim();
        const linkedin_link = document.getElementById('profile-linkedin-link').value.trim();
        const portfolio_link = document.getElementById('profile-portfolio-link').value.trim();
        const bio = document.getElementById('profile-bio').value.trim();
        
        this.showLoader();
        try {
            const res = await fetch('/api/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, role, github_username, github_link, linkedin_link, portfolio_link, bio })
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            
            if (data.success) {
                this.showToast(data.message, "success");
                this.currentUser = data.profile;
                this.setupUserUI();
            } else {
                this.showToast(data.message || "Update profile failed.", "error");
            }
        } catch (error) {
            this.showToast("Failed connecting to server.", "error");
        } finally {
            this.hideLoader();
        }
    }

    // ========================================================================
    // AI CODING CHAT ASSISTANT
    // ========================================================================

    // Prompt user question to AI Assistant
    async handleChatSubmit(e) {
        e.preventDefault();
        const input = document.getElementById('chat-message-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        input.value = '';
        input.style.height = ''; // Reset height of textarea to default
        await this.postChatMessage(message);
    }

    // Triggers chat question directly from clicking prompt chips
    async chatQuickPrompt(promptText) {
        this.switchTab('chat-panel');
        await this.postChatMessage(promptText);
    }

    // Core post message and receive reply engine
    async postChatMessage(message) {
        const container = document.getElementById('chat-messages-container');
        
        // Append user chat bubble
        container.innerHTML += `
            <div class="chat-bubble user">
                <p>${this.escapeHTML(message)}</p>
            </div>
        `;
        this.scrollChatBottom();
        
        // Append AI Thinking bubble
        const thinkingId = 'thinking-' + Date.now();
        container.innerHTML += `
            <div class="chat-bubble ai thinking" id="${thinkingId}">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        this.scrollChatBottom();
        
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            
            // Remove Thinking bubble
            const thinkingEl = document.getElementById(thinkingId);
            if (thinkingEl) thinkingEl.remove();
            
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            
            const data = await res.json();
            
            if (res.ok && data.reply) {
                // Parse markdown reply
                const parsedContent = this.parseMarkdown(data.reply);
                
                // Append AI chat bubble with custom unique id for clipboard helper
                const bubbleId = 'ai-bubble-' + Date.now();
                container.innerHTML += `
                    <div class="chat-bubble ai" id="${bubbleId}">
                        <h3 style="font-size: 1.05rem; margin-bottom: 8px;"><i class="fa-solid fa-square-terminal brand-text" style="margin-right: 6px;"></i> DevDash AI</h3>
                        <div>${parsedContent}</div>
                    </div>
                `;
                
                // Bind copy click listeners to code blocks inside the newly generated bubble
                this.bindCopyCodeListeners(bubbleId);
            } else {
                container.innerHTML += `
                    <div class="chat-bubble ai">
                        <p style="color: var(--color-danger);"><i class="fa-solid fa-triangle-exclamation"></i> Error: Unable to receive AI response. Let's try again in a moment.</p>
                    </div>
                `;
            }
        } catch (error) {
            const thinkingEl = document.getElementById(thinkingId);
            if (thinkingEl) thinkingEl.remove();
            
            container.innerHTML += `
                <div class="chat-bubble ai">
                    <p style="color: var(--color-danger);"><i class="fa-solid fa-triangle-exclamation"></i> Network Error: Connection interrupted.</p>
                </div>
            `;
        } finally {
            this.scrollChatBottom();
        }
    }

    // Scroll chatbot messages panel directly to bottom
    scrollChatBottom() {
        const container = document.getElementById('chat-messages-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
            // Short timeout to guarantee perfect scroll position after asynchronous DOM/layout updates (like Prism styling)
            setTimeout(() => {
                container.scrollTop = container.scrollHeight;
            }, 50);
        }
    }

    // Folds and binds single click copy triggers to any `pre code` block generated
    bindCopyCodeListeners(bubbleId) {
        const bubble = document.getElementById(bubbleId);
        if (!bubble) return;

        // Perform Prism.js syntax highlighting
        if (typeof Prism !== 'undefined') {
            Prism.highlightAllUnder(bubble);
        }

        // Wrap every <pre> in a code-container block and attach a copy button
        bubble.querySelectorAll('pre').forEach(pre => {
            if (pre.parentElement.classList.contains('code-container')) return;

            const codeContainer = document.createElement('div');
            codeContainer.className = 'code-container';

            // Insert codeContainer before the pre element
            pre.parentNode.insertBefore(codeContainer, pre);
            // Move pre inside the codeContainer
            codeContainer.appendChild(pre);

            // Create copy button
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';

            btn.addEventListener('click', () => {
                const codeEl = pre.querySelector('code');
                const codeText = codeEl ? codeEl.innerText : pre.innerText;
                navigator.clipboard.writeText(codeText).then(() => {
                    btn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--color-success);"></i> Copied!';
                    setTimeout(() => {
                        btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                    }, 2500);
                });
            });

            codeContainer.appendChild(btn);
        });
    }

    // Modern Markdown Parser supporting GFM marked.js with a robust fallback
    parseMarkdown(text) {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                gfm: true,
                breaks: true
            });
            return marked.parse(text);
        }

        // Fallback: robust regex-based parser when marked is offline
        let html = text;
        
        // 1. Escape basic HTML tags to prevent cross-site scripting (XSS)
        html = this.escapeHTML(html);
        
        // 2. Parse fenced code blocks with code markup preservation
        // Search matching ```language ... ``` (handling both LF and CRLF newlines)
        const codeBlocks = [];
        html = html.replace(/```(\w*)\r?\n([\s\S]*?)\r?\n```/g, (match, lang, code) => {
            const index = codeBlocks.length;
            codeBlocks.push({ lang, code });
            return `__CODE_BLOCK_PLACEHOLDER_${index}__`;
        });
        
        // 3. Parse bold markdown (`**bold text**`)
        html = html.replace(/\*\*([\s\S]*?)\*\*/g, '<strong>$1</strong>');
        
        // 4. Parse inline code highlights (` `code` `)
        html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');
        
        // 5. Parse GitHub Callout blockquotes: e.g. > [!NOTE] or > [!IMPORTANT]
        html = html.replace(/^&gt;\s*\[!(NOTE|IMPORTANT|TIP|WARNING|CAUTION)\]\s*\r?\n([\s\S]*?)(?=(?:\r?\n\r?\n|\r?\n[^\r?\n&gt;]|$))/gm, (match, type, content) => {
            const cleanContent = content.replace(/^&gt;\s?/gm, '').trim();
            return `<blockquote class="alert-${type.toLowerCase()}"><strong>${type}:</strong> ${cleanContent}</blockquote>`;
        });
        
        // 6. Parse regular Blockquotes starting with >
        html = html.replace(/^&gt;\s?([\s\S]*?)(?=(?:\r?\n\r?\n|\r?\n[^\r?\n&gt;]|$))/gm, (match, content) => {
            const cleanContent = content.replace(/^&gt;\s?/gm, '').trim();
            return `<blockquote>${cleanContent}</blockquote>`;
        });
        
        // 7. Parse headings (### heading)
        html = html.replace(/^###\s+(.*?)$/gm, '<h3>$1</h3>');
        html = html.replace(/^##\s+(.*?)$/gm, '<h2>$1</h2>');
        html = html.replace(/^#\s+(.*?)$/gm, '<h1>$1</h1>');
        
        // 8. Parse bullet lists (- item or * item)
        html = html.replace(/^\s*[-*]\s+(.*?)$/gm, '<li>$1</li>');
        // Wrap <li> sequences in <ul>. Simple approach:
        html = html.replace(/((?:<li>.*?<\/li>\s*)+)/gs, '<ul>$1</ul>');
        
        // 9. Parse single line breaks (preserving paragraphs)
        html = html.replace(/\r?\n\r?\n/g, '</p><p>');
        html = `<p>${html}</p>`;
        // Clean empty paragraphs
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/<p>\s*<\/p>/g, '');
        
        // 10. Restore code blocks placeholders safely
        codeBlocks.forEach((block, index) => {
            const placeholder = `__CODE_BLOCK_PLACEHOLDER_${index}__`;
            // Wrap in code block
            const cleanCode = block.code.trim();
            const preHtml = `<pre><code class="language-${block.lang}">${cleanCode}</code></pre>`;
            // Replacing inside our paragraphs
            html = html.replace(placeholder, preHtml);
        });
        
        return html;
    }

    // ========================================================================
    // GENERAL UTILITY FUNCTIONS
    // ========================================================================

    // Escape raw HTML strings safely
    escapeHTML(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Display a dynamic toast notification that slides in and auto-expires
    showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        // Get matching status icon
        let icon = '<i class="fa-solid fa-circle-info" style="color: var(--accent-cyan);"></i>';
        if (type === 'success') icon = '<i class="fa-solid fa-circle-check" style="color: var(--color-success);"></i>';
        if (type === 'error') icon = '<i class="fa-solid fa-circle-exclamation" style="color: var(--color-danger);"></i>';
        if (type === 'warning') icon = '<i class="fa-solid fa-triangle-exclamation" style="color: var(--color-warning);"></i>';
        
        toast.innerHTML = `
            <div class="toast-content">
                ${icon}
                <span>${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        container.appendChild(toast);
        
        // Close event
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.style.transform = 'translateX(100%)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        });
        
        // Auto expire
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transform = 'translateX(100%)';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 400);
            }
        }, duration);
    }

    // Loader display functions for AJAX fetches
    showLoader() {
        // Appends or enables a loading indicator
        let loader = document.getElementById('global-app-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'global-app-loader';
            loader.style.position = 'fixed';
            loader.style.top = '20px';
            loader.style.left = '50%';
            loader.style.transform = 'translateX(-50%)';
            loader.style.zIndex = '99999';
            loader.style.background = 'rgba(15, 21, 45, 0.9)';
            loader.style.padding = '8px 16px';
            loader.style.borderRadius = '50px';
            loader.style.boxShadow = '0 4px 15px rgba(0,0,0,0.5)';
            loader.style.display = 'flex';
            loader.style.alignItems = 'center';
            loader.style.gap = '10px';
            loader.style.fontSize = '0.9rem';
            loader.style.border = '1px solid var(--border-glass)';
            loader.style.color = '#ffffff';
            loader.innerHTML = '<span class="spinner"></span> Syncing workspace...';
            document.body.appendChild(loader);
        }
        loader.style.display = 'flex';
    }

    hideLoader() {
        const loader = document.getElementById('global-app-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    // ========================================================================
    // DEDICATED SETTINGS CENTER HANDLERS
    // ========================================================================

    // 1. Fetch user settings and populate Settings controls
    async fetchSettings() {
        try {
            const res = await fetch('/api/settings');
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            if (data.success) {
                const settings = data.settings;
                
                const themeSelect = document.getElementById('settings-theme');
                if (themeSelect) themeSelect.value = settings.theme;
                
                const bannerCheck = document.getElementById('settings-show-banner');
                if (bannerCheck) bannerCheck.checked = settings.show_welcome_banner;
                
                const actionsCheck = document.getElementById('settings-show-actions');
                if (actionsCheck) actionsCheck.checked = settings.show_quick_actions;
                
                const animationCheck = document.getElementById('settings-sidebar-animation');
                if (animationCheck) animationCheck.checked = settings.sidebar_animation;
                
                // Dynamically apply visual theme and workspace preferences
                this.applyTheme(settings.theme);
                this.applyWelcomeBanner(settings.show_welcome_banner);
                this.applyQuickActions(settings.show_quick_actions);
                this.applySidebarAnimation(settings.sidebar_animation);
            }
        } catch (err) {
            console.error("Error loading user settings:", err);
        }
    }

    // 2. Apply theme (dark, light, or system) dynamically to document root
    applyTheme(theme) {
        if (theme === 'light') {
            document.documentElement.classList.add('light-theme');
        } else if (theme === 'dark') {
            document.documentElement.classList.remove('light-theme');
        } else if (theme === 'system') {
            const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
            if (prefersLight) {
                document.documentElement.classList.add('light-theme');
            } else {
                document.documentElement.classList.remove('light-theme');
            }
        }
    }

    // Apply welcome banner visibility
    applyWelcomeBanner(show) {
        const banner = document.querySelector('.hero-card');
        if (banner) {
            if (show) {
                banner.classList.remove('hidden');
            } else {
                banner.classList.add('hidden');
            }
        }
    }

    // Apply quick actions visibility
    applyQuickActions(show) {
        const actions = document.querySelector('.hero-actions');
        if (actions) {
            if (show) {
                actions.classList.remove('hidden');
            } else {
                actions.classList.add('hidden');
            }
        }
    }

    // Apply sidebar animations toggle
    applySidebarAnimation(enabled) {
        if (enabled) {
            document.documentElement.classList.remove('no-transitions');
        } else {
            document.documentElement.classList.add('no-transitions');
        }
    }

    // Auto-save changes to the database on change listeners
    async saveSettings() {
        const themeSelect = document.getElementById('settings-theme');
        const theme = themeSelect ? themeSelect.value : 'dark';
        
        const bannerCheck = document.getElementById('settings-show-banner');
        const show_welcome_banner = bannerCheck ? bannerCheck.checked : true;
        
        const actionsCheck = document.getElementById('settings-show-actions');
        const show_quick_actions = actionsCheck ? actionsCheck.checked : true;
        
        const animationCheck = document.getElementById('settings-sidebar-animation');
        const sidebar_animation = animationCheck ? animationCheck.checked : true;
        
        // Apply settings instantly in frontend
        this.applyTheme(theme);
        this.applyWelcomeBanner(show_welcome_banner);
        this.applyQuickActions(show_quick_actions);
        this.applySidebarAnimation(sidebar_animation);
        
        try {
            const res = await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    theme,
                    show_welcome_banner,
                    show_quick_actions,
                    sidebar_animation
                })
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            if (!data.success) {
                console.error("Auto-saving settings failed on server:", data.message);
            }
        } catch (err) {
            console.error("Failed auto-saving settings changes:", err);
            this.showToast("Failed to save settings changes.", "error");
        }
    }

    // 4. Update Password Submit Flow
    async handleChangePassword(e) {
        e.preventDefault();
        
        const current_password = document.getElementById('settings-current-pass').value;
        const new_password = document.getElementById('settings-new-pass').value;
        const confirm_password = document.getElementById('settings-confirm-pass').value;
        
        if (new_password !== confirm_password) {
            this.showToast("New passwords do not match.", "error");
            return;
        }
        
        if (new_password.length < 8) {
            this.showToast("New password must be at least 8 characters long.", "error");
            return;
        }
        
        this.showLoader();
        try {
            const res = await fetch('/api/settings/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password, new_password, confirm_password })
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            if (data.success) {
                this.showToast(data.message, "success");
                document.getElementById('settings-password-form').reset();
            } else {
                this.showToast(data.message || "Password change failed.", "error");
            }
        } catch (err) {
            this.showToast("Password change request failed.", "error");
        } finally {
            this.hideLoader();
        }
    }

    // 5. CSV Exporters
    exportGoals() {
        window.location.href = '/api/settings/export/goals';
    }
    
    exportResources() {
        window.location.href = '/api/settings/export/resources';
    }

    // 6. Clear chat interface
    clearAIChat() {
        const chatContainer = document.getElementById('chat-messages-container');
        if (chatContainer) {
            chatContainer.innerHTML = `
                <div class="chat-bubble ai">
                    <h3 style="font-size: 1.05rem; margin-bottom: 8px;"><i class="fa-solid fa-square-terminal brand-text" style="margin-right: 6px;"></i> DevDash AI Assistant</h3>
                    <p>Hi there! I am your AI coding assistant, backed by Google Gemini. Ask me any programming questions, let's debug a code block, map out a learning roadmap, or analyze data structures.</p>
                </div>
            `;
            this.showToast("AI Chat history cleared successfully.", "success");
        }
    }

    // 7. Wipe all goals and resources with dual alert warnings
    async resetWorkspace() {
        const confirm1 = confirm("⚠️ WARNING: This will permanently delete all your daily coding goals and saved learning resources. This action CANNOT be undone.\n\nAre you sure you want to proceed?");
        if (!confirm1) return;
        
        const confirm2 = confirm("🔥 DOUBLE CONFIRMATION REQUIRED:\n\nAre you absolutely sure you want to wipe your DevDash AI workspace data? Click OK to reset.");
        if (!confirm2) return;
        
        this.showLoader();
        try {
            const res = await fetch('/api/settings/reset-workspace', {
                method: 'POST'
            });
            if (res.status === 401) {
                this.handleUnauthorized();
                return;
            }
            const data = await res.json();
            if (data.success) {
                this.showToast(data.message, "success");
                await this.refreshAllData();
            } else {
                this.showToast(data.message || "Failed to reset workspace.", "error");
            }
        } catch (err) {
            this.showToast("Failed to communicate with database.", "error");
        } finally {
            this.hideLoader();
        }
    }
}

// Instantiate and initialize the main application on page load
const app = new DevDashApp();
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
