// Complete working login system - replaces all broken functionality
console.log("🔧 Loading complete login fix...");

document.addEventListener("DOMContentLoaded", function() {
    console.log("✅ DOM loaded - initializing login system");
    
    // === LOGIN FORM HANDLING ===
    const loginForm = document.getElementById("loginForm");
    const loginBtn = document.getElementById("loginBtn");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    
    if (loginForm) {
        // Clear any existing handlers
        loginForm.onsubmit = null;
        
        loginForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            console.log("🚀 Login form submitted");
            
            if (loginBtn) {
                loginBtn.disabled = true;
                loginBtn.textContent = "Signing in...";
            }
            
            const email = emailInput ? emailInput.value.trim() : "";
            const password = passwordInput ? passwordInput.value : "";
            
            if (!email || !password) {
                alert("Please enter both email and password");
                if (loginBtn) {
                    loginBtn.disabled = false;
                    loginBtn.textContent = "Sign In";
                }
                return;
            }
            
            try {
                const response = await fetch("/auth/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    credentials: "include",
                    body: JSON.stringify({ email, password })
                });
                
                const data = await response.json();
                console.log("📥 Login response:", data);
                
                if (data.success) {
                    console.log("✅ Login successful, redirecting...");
                    window.location.href = data.redirect || "/";
                } else {
                    console.error("❌ Login failed:", data.error);
                    alert(data.error || "Login failed");
                }
            } catch (error) {
                console.error("🛑 Login error:", error);
                alert("Network error. Please try again.");
            }
            
            if (loginBtn) {
                loginBtn.disabled = false;
                loginBtn.textContent = "Sign In";
            }
        });
    }
    
    // === PASSWORD TOGGLE ===
    const passwordToggleBtn = document.getElementById("loginToggleBtn");
    if (passwordToggleBtn && passwordInput) {
        passwordToggleBtn.addEventListener("click", function() {
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                passwordToggleBtn.textContent = "🙈";
            } else {
                passwordInput.type = "password";
                passwordToggleBtn.textContent = "👁️";
            }
        });
    }
    
    // === THEME TOGGLE ===
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", function() {
            document.body.classList.toggle("day-mode");
            const isDayMode = document.body.classList.contains("day-mode");
            
            const themeText = document.getElementById("themeText");
            const themeIcon = document.getElementById("themeIcon");
            
            if (isDayMode) {
                if (themeText) themeText.textContent = "Day Mode is ON";
                if (themeIcon) themeIcon.textContent = "☀️";
                themeToggle.style.background = "rgba(255, 193, 7, 0.8)";
                themeToggle.style.color = "#000";
                localStorage.setItem("theme", "day");
            } else {
                if (themeText) themeText.textContent = "Night Mode is ON";
                if (themeIcon) themeIcon.textContent = "🌙";
                themeToggle.style.background = "rgba(34, 211, 238, 0.8)";
                themeToggle.style.color = "#000";
                localStorage.setItem("theme", "night");
            }
        });
    }
    
    // === LANGUAGE TOGGLE ===
    const languageSelector = document.getElementById("languageSelector");
    const languageMenu = document.getElementById("languageMenu");
    
    if (languageSelector && languageMenu) {
        languageSelector.addEventListener("click", function() {
            languageMenu.style.display = languageMenu.style.display === "block" ? "none" : "block";
        });
        
        // Close menu when clicking outside
        document.addEventListener("click", function(event) {
            if (!languageSelector.contains(event.target) && !languageMenu.contains(event.target)) {
                languageMenu.style.display = "none";
            }
        });
    }
    
    // === LANGUAGE CHANGE ===
    window.changeLanguage = function(langCode) {
        console.log("🌍 Changing language to:", langCode);
        localStorage.setItem("selectedLanguage", langCode);
        
        // Update language display
        const languageText = document.getElementById("languageText");
        const languages = {
            "en": "🇺🇸 English",
            "es": "🇪🇸 Español", 
            "fr": "🇫🇷 Français",
            "de": "🇩🇪 Deutsch",
            "it": "🇮🇹 Italiano",
            "pt": "🇵🇹 Português",
            "ru": "🇷🇺 Русский",
            "ja": "🇯🇵 日本語",
            "ko": "🇰🇷 한국어",
            "zh": "🇨🇳 中文"
        };
        
        if (languageText && languages[langCode]) {
            languageText.textContent = languages[langCode];
        }
        
        // Hide menu
        if (languageMenu) {
            languageMenu.style.display = "none";
        }
        
        // Apply translations (basic implementation)
        applyTranslations(langCode);
    };
    
    // === LOAD SAVED SETTINGS ===
    function loadSavedSettings() {
        // Load theme
        const savedTheme = localStorage.getItem("theme") || "night";
        if (savedTheme === "day" && document.body) {
            document.body.classList.add("day-mode");
            const themeText = document.getElementById("themeText");
            const themeIcon = document.getElementById("themeIcon");
            
            if (themeText) themeText.textContent = "Day Mode is ON";
            if (themeIcon) themeIcon.textContent = "☀️";
            if (themeToggle) {
                themeToggle.style.background = "rgba(255, 193, 7, 0.8)";
                themeToggle.style.color = "#000";
            }
        }
        
        // Load language
        const savedLang = localStorage.getItem("selectedLanguage") || "en";
        const languageText = document.getElementById("languageText");
        const languages = {
            "en": "🇺🇸 English",
            "es": "🇪🇸 Español",
            "fr": "🇫🇷 Français",
            "de": "🇩🇪 Deutsch",
            "it": "🇮🇹 Italiano",
            "pt": "🇵🇹 Português",
            "ru": "🇷🇺 Русский",
            "ja": "🇯🇵 日本語",
            "ko": "🇰🇷 한국어",
            "zh": "🇨🇳 中文"
        };
        
        if (languageText && languages[savedLang]) {
            languageText.textContent = languages[savedLang];
        }
    }
    
    // === BASIC TRANSLATIONS ===
    function applyTranslations(langCode) {
        const translations = {
            "es": {
                "email": "Correo electrónico",
                "password": "Contraseña",
                "sign_in": "Iniciar sesión",
                "forgot_password": "¿Olvidaste tu contraseña?",
                "create_account": "Crear cuenta"
            },
            "fr": {
                "email": "E-mail",
                "password": "Mot de passe",
                "sign_in": "Se connecter",
                "forgot_password": "Mot de passe oublié?",
                "create_account": "Créer un compte"
            }
        };
        
        const trans = translations[langCode];
        if (trans) {
            document.querySelectorAll("[data-translate]").forEach(element => {
                const key = element.getAttribute("data-translate");
                if (trans[key]) {
                    element.textContent = trans[key];
                }
            });
        }
    }
    
    // Initialize settings
    loadSavedSettings();
    
    console.log("✅ Complete login system initialized successfully");
});