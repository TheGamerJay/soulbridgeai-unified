/**
 * Universal Button Fix for SoulBridge AI
 * Ensures all buttons work regardless of CSP or security restrictions
 */

window.UniversalButtonFix = {
    initialized: false,
    
    init: function() {
        if (this.initialized) return;
        
        console.log('🔧 Initializing Universal Button Fix...');
        
        // Common button functions that should work everywhere
        this.ensureGlobalFunctions();
        this.addBackupEventListeners();
        this.fixFormSubmissions();
        
        this.initialized = true;
        console.log('✅ Universal Button Fix initialized');
    },
    
    ensureGlobalFunctions: function() {
        // Theme toggle (common across many pages) - Fixed inline style conflicts
        if (typeof window.toggleTheme !== 'function') {
            window.toggleTheme = function() {
                try {
                    console.log('🌙 Theme toggle via universal fix');
                    
                    // Toggle body class
                    document.body.classList.toggle('day-mode');
                    const isDayMode = document.body.classList.contains('day-mode');
                    
                    // Get elements
                    const themeText = document.getElementById('themeText');
                    const themeIcon = document.getElementById('themeIcon');
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
                            themeToggle.style.color = '#000';
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
                                if (computedStyle.backgroundColor.includes('0, 0, 0')) {
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
                    
                    console.log(`✅ Theme switched to: ${isDayMode ? 'Day' : 'Night'} mode`);
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
                    }
                    
                    // Find toggle button more reliably - FIXED for login page
                    let toggleBtn = null;
                    
                    // Get the exact button that was clicked (if called from button handler)
                    const clickedButton = window.event?.target || window.event?.currentTarget;
                    if (clickedButton && clickedButton.classList.contains('password-toggle')) {
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
                    
                    // Update button appearance - ENHANCED for login page
                    if (toggleBtn) {
                        // Multiple update methods to ensure it works
                        toggleBtn.textContent = newIcon;
                        toggleBtn.innerHTML = newIcon;
                        toggleBtn.innerText = newIcon;
                        toggleBtn.setAttribute('aria-label', newLabel);
                        
                        // Force DOM update with multiple techniques
                        toggleBtn.style.visibility = 'hidden';
                        toggleBtn.offsetHeight; // Force reflow
                        toggleBtn.style.visibility = 'visible';
                        
                        // Also try updating parent container to trigger refresh
                        const parent = toggleBtn.parentElement;
                        if (parent) {
                            parent.style.transform = 'translateZ(0)'; // Force repaint
                            setTimeout(() => {
                                parent.style.transform = '';
                            }, 1);
                        }
                        
                        console.log(`🔄 Button text forcibly updated to: ${newIcon}`);
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
            window.toggleLanguageMenu = function() {
                try {
                    console.log('🌐 Language menu toggle via universal fix');
                    const menu = document.getElementById('languageMenu');
                    if (menu) {
                        menu.style.display = menu.style.display === 'none' || !menu.style.display ? 'block' : 'none';
                    }
                } catch (error) {
                    console.error('❌ Universal toggleLanguageMenu error:', error);
                }
            };
        }
        
        if (typeof window.changeLanguage !== 'function') {
            window.changeLanguage = function(lang) {
                try {
                    console.log('🌐 Language change via universal fix:', lang);
                    localStorage.setItem('selectedLanguage', lang);
                    location.reload();
                } catch (error) {
                    console.error('❌ Universal changeLanguage error:', error);
                }
            };
        }
        
        // Navigation functions (from chat page)
        if (typeof window.toggleNavigationAssistant !== 'function') {
            window.toggleNavigationAssistant = function() {
                try {
                    console.log('🔍 Navigation assistant via universal fix');
                    const modal = document.getElementById('navAssistantModal');
                    if (!modal) return;
                    
                    if (modal.style.display === 'none' || modal.style.display === '') {
                        modal.style.display = 'flex';
                        const questionInput = document.getElementById('navQuestion');
                        if (questionInput) questionInput.focus();
                    } else {
                        modal.style.display = 'none';
                        const navResponse = document.getElementById('navResponse');
                        if (navResponse) navResponse.style.display = 'none';
                    }
                } catch (error) {
                    console.error('❌ Universal toggleNavigationAssistant error:', error);
                }
            };
        }
        
        if (typeof window.openUserProfile !== 'function') {
            window.openUserProfile = function() {
                try {
                    console.log('👤 Profile navigation via universal fix');
                    window.location.href = '/profile';
                } catch (error) {
                    console.error('❌ Universal openUserProfile error:', error);
                }
            };
        }
        
        if (typeof window.openCommunityDashboard !== 'function') {
            window.openCommunityDashboard = function() {
                try {
                    console.log('🌟 Community navigation via universal fix');
                    window.location.href = '/community-dashboard';
                } catch (error) {
                    console.error('❌ Universal openCommunityDashboard error:', error);
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
                console.log('👁️ Login password toggle clicked via Universal Button Fix');
                window.event = e; // Pass event context
                window.togglePassword('password');
            },
            'registerToggleBtn': (e) => {
                console.log('👁️ Register password toggle clicked via Universal Button Fix');
                window.event = e; // Pass event context
                window.togglePassword('password');
            },
            'toggleBtn': (e) => {
                console.log('👁️ Password toggle clicked via Universal Button Fix');
                window.event = e; // Pass event context
                window.togglePassword('password');
            },
            'confirmToggleBtn': (e) => {
                console.log('👁️ Confirm password toggle clicked via Universal Button Fix');
                window.event = e; // Pass event context
                window.togglePassword('confirm_password');
            },
            'loginBtn': (e) => {
                console.log('🔧 Login button clicked via universal fix');
                e.preventDefault(); // Prevent default behavior
                
                // Get form data
                const email = document.getElementById('email')?.value;
                const password = document.getElementById('password')?.value;
                
                console.log('📧 Email:', email);
                console.log('🔑 Password length:', password?.length);
                
                // Validate fields
                if (!email || !password) {
                    alert('Please fill in both email and password');
                    return;
                }
                
                // Get button element
                const loginBtn = document.getElementById('loginBtn');
                if (loginBtn) {
                    loginBtn.disabled = true;
                    loginBtn.textContent = 'Signing In...';
                }
                
                // Submit login via AJAX using FormData (matches Flask form expectations)
                const formData = new FormData();
                formData.append('email', email);
                formData.append('password', password);
                
                fetch('/auth/login', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    console.log('🔍 Login response status:', response.status);
                    
                    // Handle redirect response (302/301)
                    if (response.redirected || response.status === 302 || response.status === 301) {
                        console.log('✅ Login successful - redirecting to:', response.url);
                        window.location.href = response.url || '/';
                        return;
                    }
                    
                    // Try to parse JSON response
                    return response.json().catch(() => {
                        // If not JSON, handle as HTML redirect
                        if (response.ok) {
                            console.log('✅ Login successful - redirecting to dashboard');
                            window.location.href = '/';
                        } else {
                            throw new Error('Login failed with status ' + response.status);
                        }
                    });
                })
                .then(data => {
                    if (data) {
                        if (data.success) {
                            console.log('✅ Login successful!');
                            window.location.href = data.redirect || '/';
                        } else {
                            console.log('❌ Login failed:', data.error || data.message);
                            alert(data.error || data.message || 'Login failed');
                            if (loginBtn) {
                                loginBtn.disabled = false;
                                loginBtn.textContent = 'Sign In';
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('❌ Login error:', error);
                    alert('Login failed. Please try again.');
                    if (loginBtn) {
                        loginBtn.disabled = false;
                        loginBtn.textContent = 'Sign In';
                    }
                });
            }
        };
        
        // Add direct listeners to known buttons
        Object.keys(buttonMappings).forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button && !button.hasAttribute('data-universal-fixed')) {
                button.setAttribute('data-universal-fixed', 'true');
                button.addEventListener('click', function(e) {
                    console.log(`🔧 Universal fix handling: ${buttonId}`);
                    try {
                        buttonMappings[buttonId](e);
                    } catch (error) {
                        console.error(`❌ Universal fix error for ${buttonId}:`, error);
                    }
                });
                console.log(`✅ Added universal listener to: ${buttonId}`);
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
                            console.log(`🌐 Language change via universal fix: ${lang}`);
                            window.changeLanguage(lang);
                        });
                    }
                }
            }
        });
        
        console.log(`✅ Universal Button Fix setup complete`);
    },
    
    fixFormSubmissions: function() {
        // Ensure form submissions work
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            if (!form.hasAttribute('data-backup-submit')) {
                form.setAttribute('data-backup-submit', 'true');
                form.addEventListener('submit', function(e) {
                    console.log('📝 Form submission via universal fix');
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