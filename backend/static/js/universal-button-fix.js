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
                        if (themeText) themeText.textContent = 'Day Mode is ON';
                        if (themeIcon) themeIcon.textContent = '☀️';
                        if (themeToggle) {
                            themeToggle.style.background = 'rgba(255, 193, 7, 0.8)';
                            themeToggle.style.color = '#000';
                        }
                    } else {
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
                    console.log('👁️ Password toggle via universal fix');
                    const passwordField = document.getElementById(fieldId);
                    const toggleBtn = document.getElementById('toggleBtn') || 
                                     document.querySelector(`[onclick*="${fieldId}"]`);
                    
                    if (passwordField && passwordField.type === 'password') {
                        passwordField.type = 'text';
                        if (toggleBtn) toggleBtn.textContent = '🙈';
                    } else if (passwordField) {
                        passwordField.type = 'password';
                        if (toggleBtn) toggleBtn.textContent = '👁️';
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
        // Add backup event listeners to all elements with onclick
        const elementsWithOnclick = document.querySelectorAll('[onclick]');
        elementsWithOnclick.forEach(element => {
            const onclickValue = element.getAttribute('onclick');
            if (onclickValue && !element.hasAttribute('data-backup-listener')) {
                element.setAttribute('data-backup-listener', 'true');
                element.addEventListener('click', function(e) {
                    try {
                        console.log('🔧 Universal backup click for:', onclickValue);
                        eval(onclickValue);
                    } catch (error) {
                        console.error('❌ Universal backup click error:', error);
                    }
                });
            }
        });
        
        console.log(`✅ Added backup listeners to ${elementsWithOnclick.length} elements`);
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