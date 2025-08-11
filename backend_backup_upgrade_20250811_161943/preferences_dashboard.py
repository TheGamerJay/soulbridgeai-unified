"""
User Preferences Dashboard
Advanced customization interface for users
"""
from flask import Blueprint, render_template_string, request, jsonify, session
from functools import wraps
import logging
import json

logger = logging.getLogger(__name__)

def create_preferences_dashboard(preferences_manager):
    """Create preferences dashboard blueprint"""
    
    preferences_dashboard = Blueprint('preferences_dashboard', __name__, url_prefix='/preferences')
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    @preferences_dashboard.route('/')
    @require_auth
    def dashboard():
        """Main preferences dashboard"""
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoulBridge AI - Preferences</title>
    <style>
        :root {
            --primary: #667eea;
            --secondary: #764ba2;
            --background: #ffffff;
            --surface: #f8f9fa;
            --text: #333333;
            --accent: #667eea;
            --border: #e9ecef;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text);
        }
        
        .preferences-container {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--background);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            display: grid;
            grid-template-columns: 300px 1fr;
            min-height: 80vh;
        }
        
        .sidebar {
            background: var(--surface);
            padding: 30px;
            border-right: 1px solid var(--border);
        }
        
        .sidebar h2 {
            color: var(--text);
            font-size: 1.5rem;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .nav-menu {
            list-style: none;
        }
        
        .nav-item {
            margin-bottom: 10px;
        }
        
        .nav-link {
            display: block;
            padding: 15px 20px;
            background: transparent;
            border: none;
            color: var(--text);
            text-decoration: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            text-align: left;
            font-size: 1rem;
        }
        
        .nav-link:hover,
        .nav-link.active {
            background: var(--primary);
            color: white;
            transform: translateX(5px);
        }
        
        .main-content {
            padding: 40px;
            overflow-y: auto;
        }
        
        .content-section {
            display: none;
        }
        
        .content-section.active {
            display: block;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .section-header {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 2rem;
            color: var(--text);
            margin-bottom: 10px;
        }
        
        .section-description {
            color: #666;
            font-size: 1.1rem;
        }
        
        .setting-group {
            background: var(--surface);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid var(--border);
        }
        
        .setting-title {
            font-size: 1.2rem;
            color: var(--text);
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .setting-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 0;
            border-bottom: 1px solid var(--border);
        }
        
        .setting-item:last-child {
            border-bottom: none;
        }
        
        .setting-label {
            flex: 1;
        }
        
        .setting-name {
            font-weight: 500;
            margin-bottom: 5px;
        }
        
        .setting-desc {
            color: #666;
            font-size: 0.9rem;
        }
        
        .setting-control {
            margin-left: 20px;
        }
        
        .toggle-switch {
            position: relative;
            width: 50px;
            height: 26px;
            background: #ccc;
            border-radius: 13px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .toggle-switch.active {
            background: var(--primary);
        }
        
        .toggle-switch::after {
            content: '';
            position: absolute;
            width: 22px;
            height: 22px;
            background: white;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: transform 0.3s;
        }
        
        .toggle-switch.active::after {
            transform: translateX(24px);
        }
        
        .select-input,
        .text-input {
            padding: 10px 15px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: white;
            min-width: 150px;
        }
        
        .color-picker {
            width: 60px;
            height: 40px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        
        .theme-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .theme-card {
            border: 2px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: white;
        }
        
        .theme-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        
        .theme-card.selected {
            border-color: var(--primary);
            background: rgba(102, 126, 234, 0.1);
        }
        
        .theme-name {
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .theme-colors {
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }
        
        .theme-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: var(--surface);
            color: var(--text);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover {
            background: var(--border);
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .alert.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .privacy-score {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .privacy-score-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .accessibility-preview {
            background: var(--surface);
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
        }
        
        @media (max-width: 768px) {
            .preferences-container {
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
            }
            
            .sidebar {
                padding: 20px;
            }
            
            .nav-menu {
                display: flex;
                overflow-x: auto;
                gap: 10px;
            }
            
            .nav-item {
                margin-bottom: 0;
                min-width: 120px;
            }
        }
    </style>
</head>
<body>
    <div class="preferences-container">
        <div class="sidebar">
            <h2>⚙️ Preferences</h2>
            <ul class="nav-menu">
                <li class="nav-item">
                    <button class="nav-link active" data-section="ui">🎨 Appearance</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-section="notifications">🔔 Notifications</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-section="privacy">🔒 Privacy</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-section="ai">🤖 AI Assistant</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-section="accessibility">♿ Accessibility</button>
                </li>
            </ul>
        </div>
        
        <div class="main-content">
            <div id="alert" class="alert"></div>
            
            <!-- Appearance Settings -->
            <div class="content-section active" id="ui-section">
                <div class="section-header">
                    <h1 class="section-title">Appearance & Theme</h1>
                    <p class="section-description">Customize how SoulBridge AI looks and feels</p>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Theme Selection</div>
                    <div id="theme-grid" class="theme-grid">
                        <!-- Themes will be loaded here -->
                    </div>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Display Options</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Font Size</div>
                            <div class="setting-desc">Adjust text size for better readability</div>
                        </div>
                        <div class="setting-control">
                            <select class="select-input" id="font-size">
                                <option value="small">Small</option>
                                <option value="medium">Medium</option>
                                <option value="large">Large</option>
                            </select>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Animations</div>
                            <div class="setting-desc">Enable smooth transitions and animations</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="animation-toggle"></div>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Sidebar</div>
                            <div class="setting-desc">Keep sidebar collapsed by default</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="sidebar-toggle"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Notification Settings -->
            <div class="content-section" id="notifications-section">
                <div class="section-header">
                    <h1 class="section-title">Notification Preferences</h1>
                    <p class="section-description">Control how and when you receive notifications</p>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Notification Channels</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Email Notifications</div>
                            <div class="setting-desc">Receive notifications via email</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="email-notifications"></div>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Push Notifications</div>
                            <div class="setting-desc">Browser push notifications</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="push-notifications"></div>
                        </div>
                    </div>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Timing & Frequency</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Notification Frequency</div>
                            <div class="setting-desc">How often to receive notifications</div>
                        </div>
                        <div class="setting-control">
                            <select class="select-input" id="notification-frequency">
                                <option value="immediate">Immediate</option>
                                <option value="hourly">Hourly</option>
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="disabled">Disabled</option>
                            </select>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Quiet Hours</div>
                            <div class="setting-desc">No notifications during these times</div>
                        </div>
                        <div class="setting-control">
                            <input type="time" class="text-input" id="quiet-start" style="margin-right: 10px;">
                            <input type="time" class="text-input" id="quiet-end">
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Privacy Settings -->
            <div class="content-section" id="privacy-section">
                <div class="section-header">
                    <h1 class="section-title">Privacy & Security</h1>
                    <p class="section-description">Control your data and privacy settings</p>
                </div>
                
                <div class="privacy-score">
                    <div class="privacy-score-value" id="privacy-score">-</div>
                    <div>Privacy Score</div>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Profile Visibility</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Profile Visibility</div>
                            <div class="setting-desc">Who can see your profile information</div>
                        </div>
                        <div class="setting-control">
                            <select class="select-input" id="profile-visibility">
                                <option value="public">Public</option>
                                <option value="friends">Friends Only</option>
                                <option value="private">Private</option>
                            </select>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Mood Sharing</div>
                            <div class="setting-desc">Who can see your mood and wellness data</div>
                        </div>
                        <div class="setting-control">
                            <select class="select-input" id="mood-sharing">
                                <option value="public">Public</option>
                                <option value="friends">Friends Only</option>
                                <option value="private">Private</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Data & Analytics</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Activity Tracking</div>
                            <div class="setting-desc">Allow tracking for personalized insights</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="activity-tracking"></div>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Data Analytics</div>
                            <div class="setting-desc">Help improve the service with usage data</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="data-analytics"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- AI Settings -->
            <div class="content-section" id="ai-section">
                <div class="section-header">
                    <h1 class="section-title">AI Assistant Settings</h1>
                    <p class="section-description">Customize your AI companion's behavior</p>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Personality & Style</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Personality Type</div>
                            <div class="setting-desc">How your AI assistant behaves</div>
                        </div>
                        <div class="setting-control">
                            <select class="select-input" id="personality-type">
                                <option value="supportive">Supportive</option>
                                <option value="analytical">Analytical</option>
                                <option value="creative">Creative</option>
                                <option value="balanced">Balanced</option>
                            </select>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Response Length</div>
                            <div class="setting-desc">Preferred length of AI responses</div>
                        </div>
                        <div class="setting-control">
                            <select class="select-input" id="response-length">
                                <option value="short">Short</option>
                                <option value="medium">Medium</option>
                                <option value="detailed">Detailed</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Learning & Memory</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Learning Enabled</div>
                            <div class="setting-desc">Allow AI to learn from your conversations</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="learning-enabled"></div>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Proactive Suggestions</div>
                            <div class="setting-desc">AI can suggest activities and insights</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="proactive-suggestions"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Accessibility Settings -->
            <div class="content-section" id="accessibility-section">
                <div class="section-header">
                    <h1 class="section-title">Accessibility Options</h1>
                    <p class="section-description">Make SoulBridge AI work better for you</p>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Visual Accessibility</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">High Contrast</div>
                            <div class="setting-desc">Increase contrast for better visibility</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="high-contrast"></div>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Large Text</div>
                            <div class="setting-desc">Increase text size throughout the app</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="large-text"></div>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Reduced Motion</div>
                            <div class="setting-desc">Minimize animations and transitions</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="reduced-motion"></div>
                        </div>
                    </div>
                </div>
                
                <div class="setting-group">
                    <div class="setting-title">Navigation</div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Keyboard Navigation</div>
                            <div class="setting-desc">Enhanced keyboard navigation support</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="keyboard-navigation"></div>
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-label">
                            <div class="setting-name">Screen Reader Mode</div>
                            <div class="setting-desc">Optimize for screen reader compatibility</div>
                        </div>
                        <div class="setting-control">
                            <div class="toggle-switch" id="screen-reader-mode"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="action-buttons">
                <button class="btn btn-primary" onclick="savePreferences()">💾 Save Changes</button>
                <button class="btn btn-secondary" onclick="resetSection()">🔄 Reset to Defaults</button>
                <button class="btn btn-secondary" onclick="exportPreferences()">📤 Export Settings</button>
            </div>
        </div>
    </div>

    <script>
        let currentSection = 'ui';
        let preferences = {};
        let themes = {};
        
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function() {
                const section = this.dataset.section;
                switchSection(section);
            });
        });
        
        function switchSection(section) {
            // Update navigation
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            document.querySelector(`[data-section="${section}"]`).classList.add('active');
            
            // Update content
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(`${section}-section`).classList.add('active');
            
            currentSection = section;
        }
        
        // Toggle switches
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('toggle-switch')) {
                e.target.classList.toggle('active');
            }
        });
        
        // Theme selection
        function renderThemes() {
            const themeGrid = document.getElementById('theme-grid');
            let html = '';
            
            for (const [key, theme] of Object.entries(themes.predefined_themes || {})) {
                html += `
                    <div class="theme-card" data-theme="${key}">
                        <div class="theme-name">${theme.name}</div>
                        <div class="theme-colors">
                            <div class="theme-color" style="background: ${theme.primary}"></div>
                            <div class="theme-color" style="background: ${theme.secondary}"></div>
                            <div class="theme-color" style="background: ${theme.accent}"></div>
                        </div>
                    </div>
                `;
            }
            
            themeGrid.innerHTML = html;
            
            // Add click handlers
            document.querySelectorAll('.theme-card').forEach(card => {
                card.addEventListener('click', function() {
                    document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('selected'));
                    this.classList.add('selected');
                });
            });
        }
        
        function loadPreferences() {
            fetch('/api/preferences/')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        preferences = data.preferences;
                        updateUI();
                    }
                })
                .catch(error => console.error('Error loading preferences:', error));
        }
        
        function loadThemes() {
            fetch('/api/preferences/themes')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        themes = data;
                        renderThemes();
                    }
                })
                .catch(error => console.error('Error loading themes:', error));
        }
        
        function updateUI() {
            // UI preferences
            const ui = preferences.ui || {};
            document.getElementById('font-size').value = ui.font_size || 'medium';
            setToggle('animation-toggle', ui.animation_enabled !== false);
            setToggle('sidebar-toggle', ui.sidebar_collapsed === true);
            
            // Notification preferences
            const notifications = preferences.notifications || {};
            setToggle('email-notifications', notifications.email_enabled !== false);
            setToggle('push-notifications', notifications.push_enabled !== false);
            document.getElementById('notification-frequency').value = notifications.frequency || 'immediate';
            document.getElementById('quiet-start').value = notifications.quiet_hours_start || '22:00';
            document.getElementById('quiet-end').value = notifications.quiet_hours_end || '08:00';
            
            // Privacy preferences
            const privacy = preferences.privacy || {};
            document.getElementById('profile-visibility').value = privacy.profile_visibility || 'friends';
            document.getElementById('mood-sharing').value = privacy.mood_sharing || 'friends';
            setToggle('activity-tracking', privacy.activity_tracking !== false);
            setToggle('data-analytics', privacy.data_analytics !== false);
            
            // AI preferences
            const ai = preferences.ai || {};
            document.getElementById('personality-type').value = ai.personality_type || 'balanced';
            document.getElementById('response-length').value = ai.response_length || 'medium';
            setToggle('learning-enabled', ai.learning_enabled !== false);
            setToggle('proactive-suggestions', ai.proactive_suggestions !== false);
            
            // Accessibility preferences
            const accessibility = preferences.accessibility || {};
            setToggle('high-contrast', accessibility.high_contrast === true);
            setToggle('large-text', accessibility.large_text === true);
            setToggle('reduced-motion', accessibility.reduced_motion === true);
            setToggle('keyboard-navigation', accessibility.keyboard_navigation === true);
            setToggle('screen-reader-mode', accessibility.screen_reader_mode === true);
            
            // Update privacy score
            updatePrivacyScore();
        }
        
        function setToggle(id, active) {
            const toggle = document.getElementById(id);
            if (toggle) {
                toggle.classList.toggle('active', active);
            }
        }
        
        function getToggleState(id) {
            return document.getElementById(id).classList.contains('active');
        }
        
        function updatePrivacyScore() {
            // Calculate privacy score
            const privacy = preferences.privacy || {};
            let score = 0;
            
            if (privacy.profile_visibility === 'private') score += 25;
            else if (privacy.profile_visibility === 'friends') score += 15;
            
            if (privacy.mood_sharing === 'private') score += 25;
            else if (privacy.mood_sharing === 'friends') score += 15;
            
            if (!privacy.activity_tracking) score += 15;
            if (!privacy.data_analytics) score += 15;
            if (!privacy.marketing_emails) score += 10;
            if (!privacy.third_party_sharing) score += 20;
            if (!privacy.location_tracking) score += 15;
            
            document.getElementById('privacy-score').textContent = Math.min(score, 100);
        }
        
        function savePreferences() {
            const data = collectPreferences();
            
            fetch(`/api/preferences/${currentSection}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showAlert('Preferences saved successfully!', 'success');
                    preferences[currentSection] = result.preferences;
                    updatePrivacyScore();
                } else {
                    showAlert('Failed to save preferences: ' + result.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error saving preferences:', error);
                showAlert('Error saving preferences', 'error');
            });
        }
        
        function collectPreferences() {
            const data = {};
            
            if (currentSection === 'ui') {
                data.font_size = document.getElementById('font-size').value;
                data.animation_enabled = getToggleState('animation-toggle');
                data.sidebar_collapsed = getToggleState('sidebar-toggle');
            } else if (currentSection === 'notifications') {
                data.email_enabled = getToggleState('email-notifications');
                data.push_enabled = getToggleState('push-notifications');
                data.frequency = document.getElementById('notification-frequency').value;
                data.quiet_hours_start = document.getElementById('quiet-start').value;
                data.quiet_hours_end = document.getElementById('quiet-end').value;
            } else if (currentSection === 'privacy') {
                data.profile_visibility = document.getElementById('profile-visibility').value;
                data.mood_sharing = document.getElementById('mood-sharing').value;
                data.activity_tracking = getToggleState('activity-tracking');
                data.data_analytics = getToggleState('data-analytics');
            } else if (currentSection === 'ai') {
                data.personality_type = document.getElementById('personality-type').value;
                data.response_length = document.getElementById('response-length').value;
                data.learning_enabled = getToggleState('learning-enabled');
                data.proactive_suggestions = getToggleState('proactive-suggestions');
            } else if (currentSection === 'accessibility') {
                data.high_contrast = getToggleState('high-contrast');
                data.large_text = getToggleState('large-text');
                data.reduced_motion = getToggleState('reduced-motion');
                data.keyboard_navigation = getToggleState('keyboard-navigation');
                data.screen_reader_mode = getToggleState('screen-reader-mode');
            }
            
            return data;
        }
        
        function resetSection() {
            if (confirm('Are you sure you want to reset this section to defaults?')) {
                fetch(`/api/preferences/reset/${currentSection}`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        showAlert('Preferences reset to defaults', 'success');
                        preferences[currentSection] = result.preferences;
                        updateUI();
                    } else {
                        showAlert('Failed to reset preferences: ' + result.error, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error resetting preferences:', error);
                    showAlert('Error resetting preferences', 'error');
                });
            }
        }
        
        function exportPreferences() {
            fetch('/api/preferences/export')
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        const dataStr = JSON.stringify(result.export_data, null, 2);
                        const dataBlob = new Blob([dataStr], {type: 'application/json'});
                        
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(dataBlob);
                        link.download = 'soulbridge_preferences.json';
                        link.click();
                        
                        showAlert('Preferences exported successfully!', 'success');
                    } else {
                        showAlert('Failed to export preferences: ' + result.error, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error exporting preferences:', error);
                    showAlert('Error exporting preferences', 'error');
                });
        }
        
        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert ${type}`;
            alert.style.display = 'block';
            
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000);
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadPreferences();
            loadThemes();
        });
    </script>
</body>
</html>
        """
        return dashboard_html
    
    return preferences_dashboard

def init_preferences_dashboard(preferences_manager):
    """Initialize preferences dashboard blueprint"""
    try:
        dashboard = create_preferences_dashboard(preferences_manager)
        logger.info("Preferences dashboard initialized successfully")
        return dashboard
    except Exception as e:
        logger.error(f"Error initializing preferences dashboard: {e}")
        return None