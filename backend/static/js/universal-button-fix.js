/**
 * Universal Button Fix for SoulBridge AI
 * Ensures all buttons work regardless of CSP or security restrictions
 */

window.UniversalButtonFix = {
    initialized: false,
    
    init: function() {
        if (this.initialized) return;
        
        
        // Common button functions that should work everywhere
        this.ensureGlobalFunctions();
        this.addBackupEventListeners();
        this.fixFormSubmissions();
        
        this.initialized = true;
    },
    
    ensureGlobalFunctions: function() {
        // Theme toggle (common across many pages) - Fixed inline style conflicts
        if (typeof window.toggleTheme !== 'function') {
            window.toggleTheme = function() {
                try {
                    
                    // Toggle body class
                    document.body.classList.toggle('day-mode');
                    const isDayMode = document.body.classList.contains('day-mode');
                    
                    const themeText = document.getElementById('themeText');
                    const themeToggle = document.getElementById('themeToggle');
                    
                    // Update localStorage
                    localStorage.setItem('theme', isDayMode ? 'day' : 'night');
                    
                    // Update text and icon
                    if (themeText) themeText.textContent = isDayMode ? 'Day Mode is ON' : 'Night Mode is ON';
                    if (themeIcon) themeIcon.textContent = isDayMode ? '☀️' : '🌙';
                    
                    // Force update inline styles to match theme
                    if (themeToggle) {
                        if (isDayMode) {
                            themeToggle.style.background = 'rgba(255, 193, 7, 0.8)';
                        } else {
                            themeToggle.style.background = 'rgba(34, 211, 238, 0.8)';
                            themeToggle.style.color = '#000';
                        }
                    }
                    
                    // Only update main UI elements, not buttons with specific styling
                    const excludedElements = ['themeToggle', 'themeText', 'languageSelector', 'loginBtn', 'registerBtn'];
                    document.querySelectorAll('[style*="color"]:not(button), .auth-card, .form-input').forEach(el => {
                        if (!excludedElements.includes(el.id) && !el.closest('button')) {
                            // Update only main content elements, not navigation buttons
                            const computedStyle = window.getComputedStyle(el);
                            if (isDayMode) {
                                if (computedStyle.color === 'rgb(34, 211, 238)') {
                                    el.style.color = '#000';
                                }
                                    el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                                }
                            } else {
                                if (computedStyle.color === 'rgb(0, 0, 0)') {
                                    el.style.color = '#22d3ee';
                                }
                                if (computedStyle.backgroundColor.includes('255, 255, 255')) {
                                    el.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
                                }
                            }
                        }
                    });
                    
                } catch (error) {
                    console.error('❌ Universal toggleTheme error:', error);
                }
            };
        }
        
        // Password toggle (common in auth pages)
        if (typeof window.togglePassword !== 'function') {
            window.togglePassword = function(fieldId) {
                try {
                    console.log('👁️ Password toggle via universal fix for field:', fieldId);
                    const passwordField = document.getElementById(fieldId);
                    console.log('🔍 Found password field:', passwordField, 'type:', passwordField?.type);
                    
                    if (!passwordField) {
                        console.error('❌ Password field not found:', fieldId);
                        return;
                    let toggleBtn = null;
                    
                    // Get the exact button that was clicked (if called from button handler)
                        toggleBtn = clickedButton;
                        console.log('🎯 Using clicked button directly:', toggleBtn.id);
                    } else {
                        // First try specific IDs based on field
                        if (fieldId === 'password') {
                            toggleBtn = document.getElementById('loginToggleBtn') || 
                                       document.getElementById('registerToggleBtn') ||
                                       document.getElementById('toggleBtn');
                        } else if (fieldId === 'confirm_password') {
                            toggleBtn = document.getElementById('confirmToggleBtn');
                        }
                        
                        // Fallback: find button in same container
                        if (!toggleBtn) {
                            const container = passwordField.closest('.password-container') || passwordField.parentElement;
                            toggleBtn = container?.querySelector('.password-toggle');
                        }
                    }
                    
                    console.log('🔍 Found toggle button:', toggleBtn, 'current text:', toggleBtn?.textContent);
                    
                    // Toggle password visibility
                    const isCurrentlyPassword = passwordField.type === 'password';
                    const newType = isCurrentlyPassword ? 'text' : 'password';
                    const newIcon = isCurrentlyPassword ? '🙈' : '👁️';
                    const newLabel = isCurrentlyPassword ? 'Hide password' : 'Show password';
                    
                    // Update field type
                    passwordField.type = newType;
                    
                    // Update button appearance - ENHANCED for login page reliability
                    if (toggleBtn) {
                        // Multiple update methods to ensure it works on login page
                        toggleBtn.textContent = newIcon;
                        toggleBtn.innerHTML = newIcon;
                        toggleBtn.innerText = newIcon;
                        toggleBtn.setAttribute('aria-label', newLabel);
                        
                        // Force DOM update with multiple techniques for login page
                        toggleBtn.style.visibility = 'hidden';
                        toggleBtn.offsetHeight; // Force reflow
                        toggleBtn.style.visibility = 'visible';
                        
                        // Force repaint of parent container for login page
                        const parent = toggleBtn.parentElement;
                        if (parent) {
                            parent.style.transform = 'translateZ(0)';
                            parent.offsetHeight; // Force reflow
                            parent.style.transform = '';
                        }
                        
                        console.log(`🔄 LOGIN Enhanced button text updated to: ${newIcon}`);
                        console.log(`🔄 LOGIN Button innerHTML: ${toggleBtn.innerHTML}`);
                        console.log(`🔄 LOGIN Button textContent: ${toggleBtn.textContent}`);
                    }
                    
                    // Verify changes took effect
                    console.log(`✅ Password field type changed: ${passwordField.type}`);
                    console.log(`✅ Button text changed: ${toggleBtn?.textContent}`);
                    
                    // Trigger visual update events
                    passwordField.dispatchEvent(new Event('input', { bubbles: true }));
                    
                } catch (error) {
                    console.error('❌ Universal togglePassword error:', error);
                }
            };
        }
        
        // Language functions (common in auth pages)
        if (typeof window.toggleLanguageMenu !== 'function') {
            if (typeof window.togglePassword !== 'function') {
                window.togglePassword = function(fieldId) {
                    try {
                        const passwordField = document.getElementById(fieldId);
                        if (!passwordField) {
                            console.error('❌ Password field not found:', fieldId);
                            return;
                        }
                        let toggleBtn = null;
                        // Get the exact button that was clicked (if called from button handler)
                        const clickedButton = window.event?.target || window.event?.currentTarget;
                        if (clickedButton && clickedButton.classList.contains('password-toggle')) {
                            toggleBtn = clickedButton;
                        } else {
                            // First try specific IDs based on field
                            if (fieldId === 'password') {
                                toggleBtn = document.getElementById('loginToggleBtn') || 
                                           document.getElementById('registerToggleBtn') ||
                                           document.getElementById('toggleBtn');
                            } else if (fieldId === 'confirm_password') {
                                toggleBtn = document.getElementById('confirmToggleBtn');
                            }
                            // Fallback: find button in same container
                            if (!toggleBtn) {
                                const container = passwordField.closest('.password-container') || passwordField.parentElement;
                                toggleBtn = container?.querySelector('.password-toggle');
                            }
                        }
                        // Toggle password visibility
                        const isCurrentlyPassword = passwordField.type === 'password';
                        const newType = isCurrentlyPassword ? 'text' : 'password';
                        const newIcon = isCurrentlyPassword ? '🙈' : '👁️';
                        const newLabel = isCurrentlyPassword ? 'Hide password' : 'Show password';
                        // Update field type
                        passwordField.type = newType;
                        // Update button appearance - ENHANCED for login page reliability
                        if (toggleBtn) {
                            // Multiple update methods to ensure it works on login page
                            toggleBtn.textContent = newIcon;
                            toggleBtn.innerHTML = newIcon;
                            toggleBtn.innerText = newIcon;
                            toggleBtn.setAttribute('aria-label', newLabel);
                            // Force DOM update with multiple techniques for login page
                            toggleBtn.style.visibility = 'hidden';
                            toggleBtn.offsetHeight; // Force reflow
                            toggleBtn.style.visibility = 'visible';
                            // Force repaint of parent container for login page
                            const parent = toggleBtn.parentElement;
                            if (parent) {
                                parent.style.transform = 'translateZ(0)';
                                parent.offsetHeight; // Force reflow
                                parent.style.transform = '';
                            }
                        }
                        // Trigger visual update events
                        passwordField.dispatchEvent(new Event('input', { bubbles: true }));
                    } catch (error) {
                        console.error('❌ Universal togglePassword error:', error);
                    }
                };
            }
            };
        }
        
        if (typeof window.searchUser !== 'function') {
            window.searchUser = function() {
                try {
                    // Add search user logic here
                } catch (error) {
                    console.error('❌ Universal searchUser error:', error);
                }
            };
        }
        
        // Notification functions
        if (typeof window.toggleNotificationPanel !== 'function') {
            window.toggleNotificationPanel = function() {
                try {
                    console.log('🔔 Toggle notifications via universal fix');
                    const panel = document.getElementById('notification-panel');
                    if (panel) {
                        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                    }
                } catch (error) {
                    console.error('❌ Universal toggleNotificationPanel error:', error);
                }
            };
        }
    },
    
    addBackupEventListeners: function() {
        // Force add event listeners to specific button IDs that CSP might block
        const buttonMappings = {
            'themeToggle': () => window.toggleTheme(),
            'languageSelector': () => window.toggleLanguageMenu(),
            'loginToggleBtn': (e) => {
                window.event = e; // Pass event context
                window.togglePassword('password');
            },
            'registerToggleBtn': (e) => {
                window.event = e; // Pass event context
                window.togglePassword('password');
            },
            'toggleBtn': (e) => {
                window.event = e; // Pass event context
                window.togglePassword('password');
            },
            'confirmToggleBtn': (e) => {
                window.event = e; // Pass event context
                window.togglePassword('confirm_password');
            },
            // 'loginBtn' - REMOVED - Let form handle login naturally without any interception
        };
        
        // Add direct listeners to known buttons
        Object.keys(buttonMappings).forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button && !button.hasAttribute('data-universal-fixed')) {
                button.setAttribute('data-universal-fixed', 'true');
                button.addEventListener('click', function(e) {
                    try {
                        buttonMappings[buttonId](e);
                    } catch (error) {
                        console.error(`❌ Universal fix error for ${buttonId}:`, error);
                    }
                });
            }
        });
        
        // Also add listeners to language menu options
        const languageOptions = document.querySelectorAll('.language-option');
        languageOptions.forEach((option, index) => {
            if (!option.hasAttribute('data-universal-fixed')) {
                option.setAttribute('data-universal-fixed', 'true');
                const onclick = option.getAttribute('onclick');
                if (onclick) {
                    const langMatch = onclick.match(/changeLanguage\('([^']+)'\)/);
                    if (langMatch) {
                        const lang = langMatch[1];
                        option.addEventListener('click', function(e) {
                            window.changeLanguage(lang);
                        });
                    }
                }
            }
        });
        
    },
    
    fixFormSubmissions: function() {
        // Ensure form submissions work
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            if (!form.hasAttribute('data-backup-submit')) {
                form.setAttribute('data-backup-submit', 'true');
                form.addEventListener('submit', function(e) {
                    // Let the form submit naturally unless there are validation errors
                });
            }
        });
        
        // Ensure submit buttons work
        const submitButtons = document.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(button => {
            if (!button.hasAttribute('data-backup-submit-btn')) {
                button.setAttribute('data-backup-submit-btn', 'true');
                button.addEventListener('click', function(e) {
                    console.log('🔘 Submit button clicked via universal fix');
                    // Ensure the button can submit its form
                    const form = button.closest('form');
                    if (form && !form.checkValidity()) {
                        form.reportValidity();
                    }
                });
            }
        });
    },
    
    // Reinitialize for dynamically added content
    reinitialize: function() {
        this.addBackupEventListeners();
        this.fixFormSubmissions();
    }
};

// Auto-initialization with duplicate prevention
window.UniversalButtonFix.autoInit = function() {
    if (!this.initialized && !document.body.hasAttribute('data-universal-button-fix-loaded')) {
        console.log('🔧 Auto-initializing Universal Button Fix');
        document.body.setAttribute('data-universal-button-fix-loaded', 'true');
        this.init();
    } else if (this.initialized) {
        console.log('🔧 Universal Button Fix already initialized - skipping');
    }
};

// Single initialization point - prevent duplicates
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            window.UniversalButtonFix.autoInit();
        }, 150); // Slightly longer delay to ensure DOM is ready
    });
} else {
    setTimeout(function() {
        window.UniversalButtonFix.autoInit();
    }, 150);
}

console.log('🔧 Universal Button Fix script loaded');