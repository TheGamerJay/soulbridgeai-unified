#!/usr/bin/env python3
"""
Test script for the AutoMaintenance system and watchdog functionality
"""

import requests
import json
import time

def test_maintenance_endpoints():
    """Test all maintenance endpoints"""
    base_url = "http://localhost:5000"
    
    print("🔧 Testing Auto-Maintenance System")
    print("=" * 50)
    
    # Test maintenance status
    print("\n1. Testing maintenance status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/maintenance/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Maintenance status retrieved successfully")
            print(f"   System uptime: {data.get('system_uptime', 'N/A')} seconds")
            print(f"   Maintenance actions: {data.get('maintenance_actions', 'N/A')}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test trigger maintenance
    print("\n2. Testing trigger maintenance endpoint...")
    try:
        response = requests.post(f"{base_url}/api/maintenance/trigger", 
                               json={"task": "health_check"})
        if response.status_code == 200:
            data = response.json()
            print("✅ Maintenance triggered successfully")
            print(f"   Message: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test watchdog status
    print("\n3. Testing watchdog status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/maintenance/watchdog")
        if response.status_code == 200:
            data = response.json()
            print("✅ Watchdog status retrieved successfully")
            watchdog_status = data.get('watchdog_status', {})
            print(f"   Monitoring enabled: {watchdog_status.get('monitoring_enabled', 'N/A')}")
            print(f"   Monitored files: {len(watchdog_status.get('monitored_files', []))}")
            print(f"   Changes detected: {watchdog_status.get('changes_detected', 'N/A')}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test watchdog control
    print("\n4. Testing watchdog control...")
    try:
        # Disable watchdog
        response = requests.post(f"{base_url}/api/maintenance/watchdog", 
                               json={"action": "disable"})
        if response.status_code == 200:
            print("✅ Watchdog disabled successfully")
        
        # Enable watchdog
        response = requests.post(f"{base_url}/api/maintenance/watchdog", 
                               json={"action": "enable"})
        if response.status_code == 200:
            print("✅ Watchdog enabled successfully")
            
        # Refresh watchdog
        response = requests.post(f"{base_url}/api/maintenance/watchdog", 
                               json={"action": "refresh"})
        if response.status_code == 200:
            print("✅ Watchdog refreshed successfully")
    except Exception as e:
        print(f"❌ Watchdog control error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Maintenance system testing completed!")

if __name__ == "__main__":
    print("Starting maintenance system tests...")
    print("Make sure the Flask app is running on localhost:5000")
    
    try:
        test_maintenance_endpoints()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")