/**
 * Garlic and Chives - Main Application
 * Main JavaScript file for the application
 */

// Main application object
window.app = {
    // Initialize the application
    init: function() {
        this.setupEventListeners();
        this.setupSidebar();
        this.loadDashboardData();
        this.setupNavigation();
    },

    // Setup event listeners
    setupEventListeners: function() {
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                const sidebar = document.getElementById('sidebar');
                if (sidebar) {
                    const offcanvas = new bootstrap.Offcanvas(sidebar);
                    offcanvas.toggle();
                }
            });
        }

        // Handle navigation clicks
        document.addEventListener('click', function(e) {
            if (e.target.closest('.sidebar-nav .nav-link')) {
                const link = e.target.closest('.sidebar-nav .nav-link');
                const href = link.getAttribute('href');
                
                // Don't prevent default for collapse toggles
                if (link.hasAttribute('data-bs-toggle') && link.getAttribute('data-bs-toggle') === 'collapse') {
                    return;
                }
                
                // Handle actual navigation
                if (href && href !== '#' && href !== window.location.pathname) {
                    e.preventDefault();
                    window.app.navigateTo(href);
                }
            }
        });

        // Handle collapse state changes
        document.addEventListener('shown.bs.collapse', function(e) {
            const target = e.target;
            const trigger = document.querySelector(`[data-bs-target="#${target.id}"]`);
            if (trigger) {
                trigger.querySelector('.bi-chevron-right').style.transform = 'rotate(90deg)';
            }
        });

        document.addEventListener('hidden.bs.collapse', function(e) {
            const target = e.target;
            const trigger = document.querySelector(`[data-bs-target="#${target.id}"]`);
            if (trigger) {
                trigger.querySelector('.bi-chevron-right').style.transform = 'rotate(0deg)';
            }
        });
    },

    // Setup sidebar functionality
    setupSidebar: function() {
        // Auto-expand sections based on current page
        const currentPath = window.location.pathname;
        this.expandRelevantSections(currentPath);
    },

    // Expand relevant sections based on current page
    expandRelevantSections: function(path) {
        const sections = {
            '/upload/bankofamerica': 'boa-submenu',
            '/files/bankofamerica': 'boa-submenu',
            '/upload/chase': 'chase-submenu',
            '/files/chase': 'chase-submenu',
            '/upload/sysco': 'sysco-submenu',
            '/files/sysco': 'sysco-submenu',
            '/upload/restaurantdepot': 'restaurantdepot-submenu',
            '/files/restaurantdepot': 'restaurantdepot-submenu'
        };

        const sectionId = sections[path];
        if (sectionId) {
            const section = document.getElementById(sectionId);
            if (section) {
                const collapse = new bootstrap.Collapse(section, { show: true });
            }
        }
    },

    // Setup navigation
    setupNavigation: function() {
        const currentPath = window.location.pathname;
        this.setActiveNavigation(currentPath);
    },

    // Set active navigation based on current path
    setActiveNavigation: function(path) {
        // Remove all active classes
        document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // Set active based on current path
        const activeSelectors = {
            '/': '[data-page="dashboard"]',
            '/source/bankofamerica': '[data-page="source-boa"]',
            '/source/chase': '[data-page="source-chase"]',
            '/source/sysco': '[data-page="source-sysco"]',
            '/source/restaurantdepot': '[data-page="source-restaurantdepot"]',
            '/analytics': '[data-page="analytics"]',
            '/settings': '[data-page="settings"]'
        };

        const selector = activeSelectors[path];
        if (selector) {
            const activeLink = document.querySelector(`.sidebar-nav ${selector}`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
    },

    // Navigate to a new page
    navigateTo: function(url) {
        // Show loading state
        this.showLoading();
        
        // Navigate to the URL
        window.location.href = url;
    },

    // Load dashboard data
    loadDashboardData: function() {
        // This function will be implemented when we add dashboard functionality
        console.log('Dashboard data loading...');
    },

    // Show loading overlay
    showLoading: function() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    },

    // Hide loading overlay
    hideLoading: function() {
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.app.init();
});
