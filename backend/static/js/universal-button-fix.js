/**
 * Universal Button Fix for SoulBridge AI
 * Ensures all buttons work regardless of CSP or security restrictions
 * Cleaned for production: all debug and console statements removed, block structure repaired.
 */

window.UniversalButtonFix = {
    initialized: false,

    init: function() {
        if (this.initialized) return;
        this.ensureGlobalFunctions();
        this.addBackupEventListeners();
        this.fixFormSubmissions();
        this.initialized = true;
    },

    ensureGlobalFunctions: function() {
        // Theme toggle
        if (typeof window.toggleTheme !== 'function') {
            window.toggleTheme = function() {
                document.body.classList.toggle('day-mode');
                const isDayMode = document.body.classList.contains('day-mode');
                const themeText = document.getElementById('themeText');
                const themeToggle = document.getElementById('themeToggle');
                localStorage.setItem('theme', isDayMode ? 'day' : 'night');
                if (themeText) themeText.textContent = isDayMode ? 'Day Mode is ON' : 'Night Mode is ON';
                if (typeof themeIcon !== 'undefined') themeIcon.textContent = isDayMode ? '☀️' : '🌙';
                if (themeToggle) {
                    if (isDayMode) {
                        themeToggle.style.background = 'rgba(255, 193, 7, 0.8)';
                    } else {
                        themeToggle.style.background = 'rgba(34, 211, 238, 0.8)';
                        themeToggle.style.color = '#000';
                    }
                }
                const excludedElements = ['themeToggle', 'themeText', 'languageSelector', 'loginBtn', 'registerBtn'];
                document.querySelectorAll('[style*="color"]:not(button), .auth-card, .form-input').forEach(el => {
                    if (!excludedElements.includes(el.id) && !el.closest('button')) {
                        const computedStyle = window.getComputedStyle(el);
                        if (isDayMode) {
                            if (computedStyle.color === 'rgb(34, 211, 238)') el.style.color = '#000';
                            if (computedStyle.backgroundColor.includes('255, 255, 255')) el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                        } else {
                            if (computedStyle.color === 'rgb(0, 0, 0)') el.style.color = '#22d3ee';
                            if (computedStyle.backgroundColor.includes('255, 255, 255')) el.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
                        }
                    }
                });
            };
        }

        // Password toggle
        if (typeof window.togglePassword !== 'function') {
            window.togglePassword = function(fieldId) {
                const passwordField = document.getElementById(fieldId);
                if (!passwordField) return;
                let toggleBtn = null;
                const clickedButton = window.event?.target || window.event?.currentTarget;
                if (clickedButton && clickedButton.classList && clickedButton.classList.contains('password-toggle')) {
                    toggleBtn = clickedButton;
                } else {
                    if (fieldId === 'password') {
                        toggleBtn = document.getElementById('loginToggleBtn') || document.getElementById('registerToggleBtn') || document.getElementById('toggleBtn');
                    } else if (fieldId === 'confirm_password') {
                        toggleBtn = document.getElementById('confirmToggleBtn');
                    }
                    if (!toggleBtn) {
                        const container = passwordField.closest('.password-container') || passwordField.parentElement;
                        toggleBtn = container?.querySelector('.password-toggle');
                    }
                }
                const isCurrentlyPassword = passwordField.type === 'password';
                const newType = isCurrentlyPassword ? 'text' : 'password';
                const newIcon = isCurrentlyPassword ? '🙈' : '👁️';
                const newLabel = isCurrentlyPassword ? 'Hide password' : 'Show password';
                passwordField.type = newType;
                if (toggleBtn) {
                    toggleBtn.textContent = newIcon;
                    toggleBtn.innerHTML = newIcon;
                    toggleBtn.innerText = newIcon;
                    toggleBtn.setAttribute('aria-label', newLabel);
                    toggleBtn.style.visibility = 'hidden';
                    toggleBtn.offsetHeight;
                    toggleBtn.style.visibility = 'visible';
                    const parent = toggleBtn.parentElement;
                    if (parent) {
                        parent.style.transform = 'translateZ(0)';
                        parent.offsetHeight;
                        parent.style.transform = '';
                    }
                }
                passwordField.dispatchEvent(new Event('input', { bubbles: true }));
            };
        }

        // Language menu (stub)
        if (typeof window.toggleLanguageMenu !== 'function') {
            window.toggleLanguageMenu = function() {};
        }

        // Notification panel
        if (typeof window.toggleNotificationPanel !== 'function') {
            window.toggleNotificationPanel = function() {
                const panel = document.getElementById('notification-panel');
                if (panel) {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                }
            };
        }
    },

    addBackupEventListeners: function() {
        const buttonMappings = {
            'themeToggle': () => window.toggleTheme(),
            'languageSelector': () => window.toggleLanguageMenu(),
            'loginToggleBtn': (e) => { window.event = e; window.togglePassword('password'); },
            'registerToggleBtn': (e) => { window.event = e; window.togglePassword('password'); },
            'toggleBtn': (e) => { window.event = e; window.togglePassword('password'); },
            'confirmToggleBtn': (e) => { window.event = e; window.togglePassword('confirm_password'); },
        };
        Object.keys(buttonMappings).forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button && !button.hasAttribute('data-universal-fixed')) {
                button.setAttribute('data-universal-fixed', 'true');
                button.addEventListener('click', function(e) {
                    try { buttonMappings[buttonId](e); } catch (error) {}
                });
            }
        });
        // Language options
        const languageOptions = document.querySelectorAll('.language-option');
        languageOptions.forEach(option => {
            if (!option.hasAttribute('data-universal-fixed')) {
                option.setAttribute('data-universal-fixed', 'true');
                const onclick = option.getAttribute('onclick');
                if (onclick) {
                    const langMatch = onclick.match(/changeLanguage\('([^']+)'\)/);
                    if (langMatch) {
                        const lang = langMatch[1];
                        option.addEventListener('click', function() {
                            if (typeof window.changeLanguage === 'function') window.changeLanguage(lang);
                        });
                    }
                }
            }
        });
    },

    fixFormSubmissions: function() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            if (!form.hasAttribute('data-backup-submit')) {
                form.setAttribute('data-backup-submit', 'true');
                form.addEventListener('submit', function() {
                    // Let the form submit naturally unless there are validation errors
                });
            }
        });
        const submitButtons = document.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(button => {
            if (!button.hasAttribute('data-backup-submit-btn')) {
                button.setAttribute('data-backup-submit-btn', 'true');
                button.addEventListener('click', function() {
                    const form = button.closest('form');
                    if (form && !form.checkValidity()) {
                        form.reportValidity();
                    }
                });
            }
        });
    },

    reinitialize: function() {
        this.addBackupEventListeners();
        this.fixFormSubmissions();
    }
};

window.UniversalButtonFix.autoInit = function() {
    if (!this.initialized && !document.body.hasAttribute('data-universal-button-fix-loaded')) {
        document.body.setAttribute('data-universal-button-fix-loaded', 'true');
        this.init();
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            window.UniversalButtonFix.autoInit();
        }, 150);
    });
} else {
    setTimeout(function() {
        window.UniversalButtonFix.autoInit();
    }, 150);
}
