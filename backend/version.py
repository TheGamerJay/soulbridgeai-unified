"""
SoulBridge AI Version Management System
Tracks application versions and deployment history
"""

from datetime import datetime
import json
import os

# Current version - increment with each significant update
VERSION = "2.1.0"
BUILD_NUMBER = "241"
CODENAME = "NavigationFix"

# Version history with meaningful names
VERSION_HISTORY = {
    "2.1.0": {
        "build": "241",
        "codename": "NavigationFix", 
        "date": "2025-01-20",
        "features": [
            "Aggressive cache-busting system",
            "Professional version management",
            "Navigation refresh fixes",
            "Logo cache-busting v=2025",
            "Database initialization improvements",
            "Emergency fix endpoints"
        ],
        "fixes": [
            "Admin mode refresh going to intro",
            "Logo not updating to new version",
            "Empty database preventing login",
            "Deployment cache issues"
        ]
    },
    "2.0.0": {
        "build": "240",
        "codename": "ForceUpdate",
        "date": "2025-01-20", 
        "features": [
            "Permanent login system fixes",
            "Essential users auto-creation",
            "Enhanced health monitoring",
            "Smart navigation system"
        ],
        "fixes": [
            "Critical database empty issue",
            "Login functionality broken",
            "Cache-busting for templates"
        ]
    },
    "1.2.0": {
        "build": "230",
        "codename": "PremiumUpgrade",
        "date": "2025-01-20",
        "features": [
            "Beautiful premium upgrade modals",
            "Color studio rebuild with preview",
            "Referral page fallback system",
            "Mobile responsiveness improvements"
        ],
        "fixes": [
            "Premium companion clicks",
            "Color studio preview alerts",
            "Referral page loading issues",
            "Mobile text overlapping"
        ]
    },
    "1.1.0": {
        "build": "220", 
        "codename": "MobileFirst",
        "date": "2025-01-19",
        "features": [
            "Mobile responsive design",
            "Back button styling",
            "Session management fixes"
        ],
        "fixes": [
            "Mobile navigation issues",
            "Missing back buttons",
            "Session persistence problems"
        ]
    },
    "1.0.0": {
        "build": "200",
        "codename": "Genesis", 
        "date": "2025-01-19",
        "features": [
            "Initial SoulBridge AI release",
            "Character companion system",
            "Premium subscription model",
            "Multi-language support"
        ],
        "fixes": []
    }
}

def get_version_info():
    """Get comprehensive version information"""
    return {
        "version": VERSION,
        "build": BUILD_NUMBER,
        "codename": CODENAME,
        "full_version": f"{VERSION}.{BUILD_NUMBER}",
        "display_name": f"SoulBridge AI v{VERSION} '{CODENAME}'",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "history": VERSION_HISTORY.get(VERSION, {})
    }

def get_version_display():
    """Get user-friendly version display"""
    return f"v{VERSION} '{CODENAME}' (Build {BUILD_NUMBER})"

def get_changelog(version=None):
    """Get changelog for specific version or current"""
    target_version = version or VERSION
    return VERSION_HISTORY.get(target_version, {})

def bump_version(version_type="patch"):
    """Utility to bump version number (for development use)"""
    major, minor, patch = map(int, VERSION.split('.'))
    
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1
    
    return f"{major}.{minor}.{patch}"