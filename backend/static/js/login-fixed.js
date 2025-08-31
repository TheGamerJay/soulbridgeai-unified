// Complete working login system - replaces all broken functionality
document.addEventListener("DOMContentLoaded", function() {
    
    // === LOGIN FORM HANDLING ===
    const loginForm = document.getElementById("loginForm");
    const loginBtn = document.getElementById("loginBtn");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    
    if (loginForm) {
        loginForm.onsubmit = null;
        loginForm.addEventListener("submit", function(e) {
            const email = emailInput ? emailInput.value.trim() : "";
            const password = passwordInput ? passwordInput.value : "";
            if (!email || !password) {
                e.preventDefault();
                alert("Please enter both email and password");
                return;
            }
            if (loginBtn) {
                loginBtn.disabled = true;
                loginBtn.textContent = "Signing in...";
            }
            // Let form submit naturally
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
        
        // Update language display (match template's currentLanguage element)
        const currentLanguage = document.getElementById("currentLanguage");
        const langMap = {
            'en': 'EN',
            'es': 'ES', 
            'fr': 'FR',
            'de': 'DE',
            'pt': 'PT',
            'zh': 'ZH',
            'ja': 'JP',
            'ru': 'RU'
        };
        
        if (currentLanguage && langMap[langCode]) {
            currentLanguage.textContent = langMap[langCode];
            console.log('🌐 [EXTERNAL] Updated language display to:', langMap[langCode]);
        }
        
        // Hide menu
        if (languageMenu) {
            languageMenu.style.display = "none";
            console.log('🌐 [EXTERNAL] Language menu hidden');
        }
        
        // Apply translations (basic implementation)
        console.log('🌐 [EXTERNAL] About to call applyTranslations with:', langCode);
        try {
            applyTranslations(langCode);
        } catch (error) {
            console.error('🌐 [EXTERNAL] Error in applyTranslations:', error);
        }
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
        
        // Load language (match template's currentLanguage element)
        const savedLang = localStorage.getItem("selectedLanguage") || "en";
        const currentLanguage = document.getElementById("currentLanguage");
        const langMap = {
            'en': 'EN',
            'es': 'ES',
            'fr': 'FR',
            'de': 'DE',
            'pt': 'PT',
            'zh': 'ZH',
            'ja': 'JP',
            'ru': 'RU'
        };
        
        if (currentLanguage && langMap[savedLang]) {
            currentLanguage.textContent = langMap[savedLang];
            console.log('🌐 [EXTERNAL] Loaded saved language display:', langMap[savedLang]);
        }
        
        // Apply saved language translations
        applyTranslations(savedLang);
    }
    
    // === BASIC TRANSLATIONS ===
    function applyTranslations(langCode) {
        console.log('🌍 [EXTERNAL] Applying translations for language:', langCode);
        
        const translations = {
            en: {
                sign_in: "Sign In",
                sign_in_subtitle: "Sign in to continue your journey",
                email_address: "Email Address", 
                password: "Password",
                forgot_password: "Forgot password?",
                welcome_back: "Welcome Back",
                no_account: "Don't have an account?",
                sign_up: "Sign up",
                language_en: "EN"
            },
            es: {
                sign_in: "Iniciar Sesión",
                sign_in_subtitle: "Inicia sesión para continuar tu viaje",
                email_address: "Dirección de Correo",
                password: "Contraseña", 
                forgot_password: "¿Olvidaste tu contraseña?",
                welcome_back: "Bienvenido de Vuelta",
                no_account: "¿No tienes una cuenta?",
                sign_up: "Registrarse",
                language_en: "ES"
            },
            fr: {
                sign_in: "Se Connecter",
                sign_in_subtitle: "Connectez-vous pour continuer votre voyage",
                email_address: "Adresse E-mail",
                password: "Mot de Passe",
                forgot_password: "Mot de passe oublié?",
                welcome_back: "Bon Retour",
                no_account: "Vous n'avez pas de compte?",
                sign_up: "S'inscrire",
                language_en: "FR"
            },
            de: {
                sign_in: "Anmelden",
                sign_in_subtitle: "Melden Sie sich an, um Ihre Reise fortzusetzen",
                email_address: "E-Mail-Adresse",
                password: "Passwort",
                forgot_password: "Passwort vergessen?",
                welcome_back: "Willkommen zurück",
                no_account: "Haben Sie kein Konto?",
                sign_up: "Registrieren",
                language_en: "DE"
            },
            pt: {
                sign_in: "Entrar",
                sign_in_subtitle: "Faça login para continuar sua jornada",
                email_address: "Endereço de E-mail",
                password: "Senha",
                forgot_password: "Esqueceu a senha?",
                welcome_back: "Bem-vindo de Volta",
                no_account: "Não tem uma conta?",
                sign_up: "Cadastrar-se",
                language_en: "PT"
            },
            zh: {
                sign_in: "登录",
                sign_in_subtitle: "登录以继续您的旅程",
                email_address: "电子邮件地址",
                password: "密码",
                forgot_password: "忘记密码？",
                welcome_back: "欢迎回来",
                no_account: "没有账户？",
                sign_up: "注册",
                language_en: "ZH"
            },
            ja: {
                sign_in: "ログイン",
                sign_in_subtitle: "あなたの旅を続けるためにログインしてください",
                email_address: "メールアドレス",
                password: "パスワード",
                forgot_password: "パスワードを忘れましたか？",
                welcome_back: "おかえりなさい",
                no_account: "アカウントをお持ちでないですか？",
                sign_up: "サインアップ",
                language_en: "JP"
            },
            ru: {
                sign_in: "Войти",
                sign_in_subtitle: "Войдите, чтобы продолжить свое путешествие",
                email_address: "Адрес электронной почты",
                password: "Пароль",
                forgot_password: "Забыли пароль?",
                welcome_back: "Добро пожаловать обратно",
                no_account: "Нет аккаунта?",
                sign_up: "Зарегистрироваться",
                language_en: "RU"
            }
        };
        
        const translation = translations[langCode] || translations.en;
        console.log('🌍 [EXTERNAL] Translation object:', translation);
        
        // Find all elements with data-translate attribute
        const elements = document.querySelectorAll('[data-translate]');
        console.log('🌍 [EXTERNAL] Found elements with data-translate:', elements.length);
        
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            console.log('🌍 [EXTERNAL] Processing element with key:', key, 'current text:', element.textContent.trim());
            if (translation[key]) {
                element.textContent = translation[key];
                console.log('🌍 [EXTERNAL] Updated to:', translation[key]);
            } else {
                console.warn('🌍 [EXTERNAL] Missing translation for key:', key);
            }
        });
        
        // Update placeholders
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        
        if (emailInput && translation.email_address) {
            emailInput.placeholder = translation.email_address;
            console.log('🌍 [EXTERNAL] Updated email placeholder to:', translation.email_address);
        }
        if (passwordInput && translation.password) {
            passwordInput.placeholder = translation.password;
            console.log('🌍 [EXTERNAL] Updated password placeholder to:', translation.password);
        }
        
        console.log('🌍 [EXTERNAL] Translation application complete');
    }
    
    // Initialize settings
    loadSavedSettings();
    
});