// Complete working register system with comprehensive translations
document.addEventListener("DOMContentLoaded", function() {
    
    // === REGISTER FORM HANDLING ===
    const registerForm = document.getElementById("registerForm");
    const registerBtn = document.getElementById("registerBtn");
    const displayNameInput = document.getElementById("display_name");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirm_password");
    
    if (registerForm) {
        registerForm.onsubmit = null;
        registerForm.addEventListener("submit", function(e) {
            const displayName = displayNameInput ? displayNameInput.value.trim() : "";
            const email = emailInput ? emailInput.value.trim() : "";
            const password = passwordInput ? passwordInput.value : "";
            const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : "";
            
            if (!displayName || !email || !password || !confirmPassword) {
                e.preventDefault();
                alert("Please fill in all fields");
                return;
            }
            
            if (password !== confirmPassword) {
                e.preventDefault();
                alert("Passwords do not match");
                return;
            }
            
            if (registerBtn) {
                registerBtn.disabled = true;
                registerBtn.textContent = "Creating account...";
            }
            // Let form submit naturally
        });
    }
    
    // === PASSWORD TOGGLE ===
    const passwordToggleBtn = document.getElementById("registerToggleBtn");
    const confirmToggleBtn = document.getElementById("confirmToggleBtn");
    
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
    
    if (confirmToggleBtn && confirmPasswordInput) {
        confirmToggleBtn.addEventListener("click", function() {
            if (confirmPasswordInput.type === "password") {
                confirmPasswordInput.type = "text";
                confirmToggleBtn.textContent = "🙈";
            } else {
                confirmPasswordInput.type = "password";
                confirmToggleBtn.textContent = "👁️";
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
        console.log("🌍 [REGISTER] Changing language to:", langCode);
        localStorage.setItem("selectedLanguage", langCode);
        
        // Update language display
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
            console.log('🌍 [REGISTER] Updated language display to:', langMap[langCode]);
        }
        
        // Hide menu
        if (languageMenu) {
            languageMenu.style.display = "none";
        }
        
        // Apply translations
        try {
            applyTranslations(langCode);
        } catch (error) {
            console.error('🌍 [REGISTER] Error in applyTranslations:', error);
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
        
        // Load language
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
        }
        
        // Apply saved language translations
        applyTranslations(savedLang);
    }
    
    // === COMPREHENSIVE TRANSLATIONS ===
    function applyTranslations(langCode) {
        console.log('🌍 [REGISTER] Applying translations for language:', langCode);
        
        const translations = {
            en: {
                create_account: "Create Account",
                start_journey: "Start your journey with AI companions",
                display_name: "Display Name",
                email: "Email",
                password: "Password",
                confirm_password: "Confirm Password",
                req_8_chars: "At least 8 characters",
                req_uppercase: "One uppercase letter",
                req_lowercase: "One lowercase letter", 
                req_number: "One number",
                agree_to: "I agree to the",
                terms_service: "Terms of Service",
                and: "and",
                privacy_policy: "Privacy Policy",
                already_have_account: "Already have an account?",
                sign_in: "Sign in",
                back: "← Back",
                language_en: "EN",
                lang_english: "English",
                lang_spanish: "Español",
                lang_french: "Français", 
                lang_german: "Deutsch",
                lang_portuguese: "Português",
                lang_chinese: "中文",
                lang_japanese: "日本語",
                lang_russian: "Русский"
            },
            es: {
                create_account: "Crear Cuenta",
                start_journey: "Comienza tu viaje con compañeros de IA",
                display_name: "Nombre de Pantalla",
                email: "Correo Electrónico", 
                password: "Contraseña",
                confirm_password: "Confirmar Contraseña",
                req_8_chars: "Al menos 8 caracteres",
                req_uppercase: "Una letra mayúscula",
                req_lowercase: "Una letra minúscula",
                req_number: "Un número",
                agree_to: "Acepto los",
                terms_service: "Términos de Servicio",
                and: "y",
                privacy_policy: "Política de Privacidad",
                already_have_account: "¿Ya tienes una cuenta?",
                sign_in: "Iniciar sesión",
                back: "← Atrás",
                language_en: "ES",
                lang_english: "English",
                lang_spanish: "Español",
                lang_french: "Français", 
                lang_german: "Deutsch",
                lang_portuguese: "Português",
                lang_chinese: "中文",
                lang_japanese: "日本語",
                lang_russian: "Русский"
            },
            fr: {
                create_account: "Créer un Compte",
                start_journey: "Commencez votre voyage avec des compagnons IA",
                display_name: "Nom d'Affichage",
                email: "E-mail",
                password: "Mot de Passe",
                confirm_password: "Confirmer le Mot de Passe",
                req_8_chars: "Au moins 8 caractères",
                req_uppercase: "Une lettre majuscule",
                req_lowercase: "Une lettre minuscule",
                req_number: "Un chiffre",
                agree_to: "J'accepte les",
                terms_service: "Conditions de Service",
                and: "et",
                privacy_policy: "Politique de Confidentialité",
                already_have_account: "Vous avez déjà un compte?",
                sign_in: "Se connecter",
                back: "← Retour",
                language_en: "FR"
            },
            de: {
                create_account: "Konto Erstellen",
                start_journey: "Beginnen Sie Ihre Reise mit KI-Begleitern",
                display_name: "Anzeigename",
                email: "E-Mail",
                password: "Passwort",
                confirm_password: "Passwort Bestätigen",
                req_8_chars: "Mindestens 8 Zeichen",
                req_uppercase: "Ein Großbuchstabe",
                req_lowercase: "Ein Kleinbuchstabe",
                req_number: "Eine Zahl",
                agree_to: "Ich stimme den",
                terms_service: "Nutzungsbedingungen",
                and: "und",
                privacy_policy: "Datenschutzrichtlinie",
                already_have_account: "Haben Sie bereits ein Konto?",
                sign_in: "Anmelden",
                back: "← Zurück",
                language_en: "DE"
            },
            pt: {
                create_account: "Criar Conta",
                start_journey: "Comece sua jornada com companheiros de IA",
                display_name: "Nome de Exibição",
                email: "E-mail",
                password: "Senha",
                confirm_password: "Confirmar Senha",
                req_8_chars: "Pelo menos 8 caracteres",
                req_uppercase: "Uma letra maiúscula",
                req_lowercase: "Uma letra minúscula",
                req_number: "Um número",
                agree_to: "Eu concordo com os",
                terms_service: "Termos de Serviço",
                and: "e",
                privacy_policy: "Política de Privacidade",
                already_have_account: "Já tem uma conta?",
                sign_in: "Entrar",
                back: "← Voltar",
                language_en: "PT"
            },
            zh: {
                create_account: "创建账户",
                start_journey: "与AI伙伴开始您的旅程",
                display_name: "显示名称",
                email: "电子邮件",
                password: "密码",
                confirm_password: "确认密码",
                req_8_chars: "至少8个字符",
                req_uppercase: "一个大写字母",
                req_lowercase: "一个小写字母",
                req_number: "一个数字",
                agree_to: "我同意",
                terms_service: "服务条款",
                and: "和",
                privacy_policy: "隐私政策",
                already_have_account: "已经有账户了？",
                sign_in: "登录",
                back: "← 返回",
                language_en: "ZH"
            },
            ja: {
                create_account: "アカウント作成",
                start_journey: "AIコンパニオンとあなたの旅を始めましょう",
                display_name: "表示名",
                email: "メールアドレス",
                password: "パスワード",
                confirm_password: "パスワード確認",
                req_8_chars: "8文字以上",
                req_uppercase: "大文字1つ",
                req_lowercase: "小文字1つ",
                req_number: "数字1つ",
                agree_to: "私は同意します",
                terms_service: "利用規約",
                and: "と",
                privacy_policy: "プライバシーポリシー",
                already_have_account: "すでにアカウントをお持ちですか？",
                sign_in: "ログイン",
                back: "← 戻る",
                language_en: "JP"
            },
            ru: {
                create_account: "Создать Аккаунт",
                start_journey: "Начните свое путешествие с ИИ-спутниками",
                display_name: "Отображаемое Имя",
                email: "Электронная Почта",
                password: "Пароль",
                confirm_password: "Подтвердить Пароль",
                req_8_chars: "Минимум 8 символов",
                req_uppercase: "Одна заглавная буква",
                req_lowercase: "Одна строчная буква",
                req_number: "Одна цифра",
                agree_to: "Я согласен с",
                terms_service: "Условиями Обслуживания",
                and: "и",
                privacy_policy: "Политикой Конфиденциальности",
                already_have_account: "Уже есть аккаунт?",
                sign_in: "Войти",
                back: "← Назад",
                language_en: "RU"
            }
        };
        
        const translation = translations[langCode] || translations.en;
        console.log('🌍 [REGISTER] Translation object:', translation);
        
        // Find all elements with data-translate attribute
        const elements = document.querySelectorAll('[data-translate]');
        console.log('🌍 [REGISTER] Found elements with data-translate:', elements.length);
        
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            console.log('🌍 [REGISTER] Processing element with key:', key, 'current text:', element.textContent.trim());
            if (translation[key]) {
                element.textContent = translation[key];
                console.log('🌍 [REGISTER] Updated to:', translation[key]);
            } else {
                console.warn('🌍 [REGISTER] Missing translation for key:', key);
            }
        });
        
        // Update placeholders
        const inputs = document.querySelectorAll('[data-translate-placeholder]');
        inputs.forEach(input => {
            const key = input.getAttribute('data-translate-placeholder');
            if (translation[key]) {
                input.placeholder = translation[key];
                console.log('🌍 [REGISTER] Updated placeholder for:', key, 'to:', translation[key]);
            }
        });
        
        console.log('🌍 [REGISTER] Translation application complete');
    }
    
    // Initialize settings
    loadSavedSettings();
    
});