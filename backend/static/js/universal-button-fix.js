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
        // Theme toggle (common across many pages)
        if (typeof window.toggleTheme !== 'function') {
            window.toggleTheme = function() {
                try {
                    console.log('🌙 Theme toggle via universal fix');
                    document.body.classList.toggle('day-mode');
                    const themeText = document.getElementById('themeText');
                    const themeIcon = document.getElementById('themeIcon');
                    const themeToggle = document.getElementById('themeToggle');
                    
                    if (document.body.classList.contains('day-mode')) {
                        localStorage.setItem('theme', 'day');
                        if (themeText) themeText.textContent = 'Day Mode is ON';
                        if (themeIcon) themeIcon.textContent = '☀️';
                        if (themeToggle) {
                            themeToggle.style.background = 'rgba(255, 193, 7, 0.8)';
                            themeToggle.style.color = '#000';
                        }
                    } else {
                        localStorage.setItem('theme', 'night');
                        if (themeText) themeText.textContent = 'Night Mode is ON';
                        if (themeIcon) themeIcon.textContent = '🌙';
                        if (themeToggle) {
                            themeToggle.style.background = 'rgba(34, 211, 238, 0.8)';
                            themeToggle.style.color = '#000';
                        }
                    }
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
                    console.log('🔍 Found password field:', passwordField);
                    
                    if (!passwordField) {
                        console.error('❌ Password field not found:', fieldId);
                        return;
                    }
                    
                    const toggleBtn = document.getElementById('toggleBtn') || 
                                     document.getElementById('loginToggleBtn') ||
                                     document.getElementById('registerToggleBtn') ||
                                     document.getElementById('confirmToggleBtn') ||
                                     document.querySelector(`[onclick*="${fieldId}"]`);
                    
                    console.log('🔍 Found toggle button:', toggleBtn);
                    
                    if (passwordField.type === 'password') {
                        passwordField.type = 'text';
                        if (toggleBtn) toggleBtn.textContent = '🙈';
                        console.log('✅ Password shown');
                    } else {
                        passwordField.type = 'password';
                        if (toggleBtn) toggleBtn.textContent = '👁️';
                        console.log('✅ Password hidden');
                    }
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
            'loginToggleBtn': () => {
                console.log('👁️ Login password toggle clicked via Universal Button Fix');
                window.togglePassword('password');
            },
            'registerToggleBtn': () => {
                console.log('👁️ Register password toggle clicked via Universal Button Fix');
                window.togglePassword('password');
            },
            'toggleBtn': () => {
                console.log('👁️ Password toggle clicked via Universal Button Fix');
                window.togglePassword('password');
            },
            'confirmToggleBtn': () => {
                console.log('👁️ Confirm password toggle clicked via Universal Button Fix');
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
                
                // Submit login via AJAX
                fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('✅ Login successful!');
                        window.location.href = data.redirect || '/';
                    } else {
                        console.log('❌ Login failed:', data.error);
                        alert(data.error || 'Login failed');
                        if (loginBtn) {
                            loginBtn.disabled = false;
                            loginBtn.textContent = 'Sign In';
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

// Only auto-initialize if not manually controlled
window.UniversalButtonFix.autoInit = function() {
    if (!this.initialized) {
        console.log('🔧 Auto-initializing Universal Button Fix');
        this.init();
    }
};

// Auto-initialize when script loads (but allow manual override)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            window.UniversalButtonFix.autoInit();
        }, 100);
    });
} else {
    setTimeout(function() {
        window.UniversalButtonFix.autoInit();
    }, 100);
}

// Also reinitialize after window load
window.addEventListener('load', function() {
    setTimeout(function() {
        if (window.UniversalButtonFix.initialized) {
            window.UniversalButtonFix.reinitialize();
        }
    }, 800);
});

console.log('🔧 Universal Button Fix script loaded');