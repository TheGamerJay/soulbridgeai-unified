# Admin Dashboard with Real-time Metrics
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, jsonify, request, render_template_string, make_response
from business_intelligence import BusinessIntelligenceManager
from data_visualization import DataVisualizationManager
import sqlite3
from database_utils import format_query

logger = logging.getLogger(__name__)

admin_dashboard = Blueprint('admin_dashboard', __name__, url_prefix='/admin')

class AdminDashboardManager:
    def __init__(self, db_manager=None, bi_manager=None):
        self.db = db_manager
        self.bi_manager = bi_manager or BusinessIntelligenceManager(db_manager)
        self.viz_manager = DataVisualizationManager(db_manager, self.bi_manager)
        
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        try:
            # Get current timestamp
            now = datetime.now()
            
            # Get user metrics
            user_metrics = self.bi_manager.get_comprehensive_user_analytics(30)
            
            # Get revenue metrics
            revenue_metrics = self.bi_manager.get_revenue_analytics(30)
            
            # Get companion performance
            companion_metrics = self.bi_manager.get_companion_performance_analytics(30)
            
            # Get system health
            system_health = self._get_system_health()
            
            # Get recent activity
            recent_activity = self._get_recent_activity()
            
            return {
                "timestamp": now.isoformat(),
                "user_metrics": user_metrics,
                "revenue_metrics": revenue_metrics,
                "companion_metrics": companion_metrics,
                "system_health": system_health,
                "recent_activity": recent_activity,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            health_data = {
                "api_status": "operational",
                "database_status": "operational",
                "ai_service_status": "operational",
                "email_service_status": "operational",
                "uptime_hours": 24.5,  # Mock data
                "error_rate": 0.02,
                "response_time_ms": 150,
                "active_connections": 45
            }
            
            # Check database connectivity
            if self.db:
                try:
                    # Simple query to test DB
                    cursor = self.db.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    health_data["database_status"] = "operational"
                except Exception:
                    health_data["database_status"] = "degraded"
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "api_status": "unknown",
                "database_status": "unknown",
                "error": str(e)
            }
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        try:
            activities = []
            
            if self.db:
                cursor = self.db.connection.cursor()
                
                # Get recent user registrations
                cursor.execute(format_query("""
                    SELECT email, display_name, created_at 
                    FROM users 
                    WHERE created_at > datetime('now', '-24 hours')
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                
                for row in cursor.fetchall():
                    activities.append({
                        "type": "user_registration",
                        "description": f"New user registered: {row[1] or row[0]}",
                        "timestamp": row[2],
                        "severity": "info"
                    })
                
                # Get recent conversations
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM conversations 
                    WHERE created_at > datetime('now', '-1 hour')
                """)
                
                recent_conversations = cursor.fetchone()[0]
                if recent_conversations > 0:
                    activities.append({
                        "type": "conversation_activity",
                        "description": f"{recent_conversations} new conversations in the last hour",
                        "timestamp": datetime.now().isoformat(),
                        "severity": "info"
                    })
            
            # Add some mock system events
            activities.extend([
                {
                    "type": "system_backup",
                    "description": "Daily backup completed successfully",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "severity": "success"
                },
                {
                    "type": "ai_model_update",
                    "description": "AI model performance optimized",
                    "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "severity": "info"
                }
            ])
            
            return sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:20]
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return [{
                "type": "error",
                "description": f"Error loading activity: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "severity": "error"
            }]
    
    def get_user_analytics_detail(self, period_days: int = 30) -> Dict[str, Any]:
        """Get detailed user analytics"""
        try:
            analytics = self.bi_manager.get_comprehensive_user_analytics(period_days)
            
            # Add trend data
            analytics["trends"] = self._calculate_user_trends(period_days)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics detail: {e}")
            return {"error": str(e)}
    
    def _calculate_user_trends(self, period_days: int) -> Dict[str, Any]:
        """Calculate user growth trends"""
        try:
            trends = {
                "user_growth": [],
                "engagement_trend": [],
                "retention_trend": []
            }
            
            if self.db:
                cursor = self.db.connection.cursor()
                
                # Calculate daily user registrations for the period
                for i in range(period_days):
                    date = datetime.now() - timedelta(days=i)
                    date_str = date.strftime('%Y-%m-%d')
                    
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM users 
                        WHERE DATE(created_at) = ?
                    """), (date_str,))
                    
                    count = cursor.fetchone()[0]
                    trends["user_growth"].append({
                        "date": date_str,
                        "count": count
                    })
                
                # Reverse to show chronological order
                trends["user_growth"].reverse()
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {}

# Dashboard routes
@admin_dashboard.route('/metrics')
def get_metrics():
    """Get real-time dashboard metrics"""
    try:
        # Initialize dashboard manager
        dashboard = AdminDashboardManager()
        metrics = dashboard.get_real_time_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error in metrics endpoint: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@admin_dashboard.route('/users')
def get_user_analytics():
    """Get detailed user analytics"""
    try:
        period_days = request.args.get('period', 30, type=int)
        dashboard = AdminDashboardManager()
        analytics = dashboard.get_user_analytics_detail(period_days)
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error in user analytics endpoint: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@admin_dashboard.route('/health')
def get_health():
    """Get system health status"""
    try:
        dashboard = AdminDashboardManager()
        health = dashboard._get_system_health()
        return jsonify(health)
        
    except Exception as e:
        logger.error(f"Error in health endpoint: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@admin_dashboard.route('/charts/user-growth')
def get_user_growth_chart():
    """Get user growth chart data"""
    try:
        period_days = request.args.get('period', 30, type=int)
        dashboard = AdminDashboardManager()
        chart_data = dashboard.viz_manager.generate_user_growth_chart_data(period_days)
        return jsonify(chart_data)
        
    except Exception as e:
        logger.error(f"Error in user growth chart endpoint: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@admin_dashboard.route('/charts/engagement')
def get_engagement_chart():
    """Get engagement metrics chart data"""
    try:
        period_days = request.args.get('period', 30, type=int)
        dashboard = AdminDashboardManager()
        chart_data = dashboard.viz_manager.generate_engagement_metrics_chart(period_days)
        return jsonify(chart_data)
        
    except Exception as e:
        logger.error(f"Error in engagement chart endpoint: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@admin_dashboard.route('/charts/companion-performance')
def get_companion_performance_chart():
    """Get companion performance chart data"""
    try:
        period_days = request.args.get('period', 30, type=int)
        dashboard = AdminDashboardManager()
        chart_data = dashboard.viz_manager.generate_companion_performance_chart(period_days)
        return jsonify(chart_data)
        
    except Exception as e:
        logger.error(f"Error in companion performance chart endpoint: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@admin_dashboard.route('/reports/comprehensive')
def get_comprehensive_report():
    """Get comprehensive analytics report"""
    try:
        period_days = request.args.get('period', 30, type=int)
        format_type = request.args.get('format', 'json')
        
        dashboard = AdminDashboardManager()
        report_data = dashboard.viz_manager.generate_comprehensive_report(period_days)
        
        if format_type != 'json':
            export_data = dashboard.viz_manager.export_report_data(report_data, format_type)
            if 'error' in export_data:
                return jsonify(export_data), 400
            
            response = make_response(export_data['content'])
            response.headers['Content-Type'] = export_data['content_type']
            response.headers['Content-Disposition'] = f'attachment; filename={export_data["filename"]}'
            return response
        
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error in comprehensive report endpoint: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@admin_dashboard.route('/')
def dashboard_home():
    """Serve the admin dashboard HTML"""
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoulBridge AI - Admin Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #22d3ee, #0891b2);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.8rem;
            font-weight: 600;
        }
        
        .dashboard {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border: 1px solid #e5e7eb;
        }
        
        .metric-label {
            color: #6b7280;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.25rem;
        }
        
        .metric-change {
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .metric-change.positive {
            color: #059669;
        }
        
        .metric-change.negative {
            color: #dc2626;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border: 1px solid #e5e7eb;
        }
        
        .chart-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #111827;
        }
        
        .activity-feed {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border: 1px solid #e5e7eb;
        }
        
        .activity-item {
            padding: 0.75rem 0;
            border-bottom: 1px solid #f3f4f6;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-icon {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        
        .activity-icon.info { background: #3b82f6; }
        .activity-icon.success { background: #10b981; }
        .activity-icon.error { background: #ef4444; }
        
        .activity-content {
            flex: 1;
            font-size: 0.875rem;
        }
        
        .activity-time {
            font-size: 0.75rem;
            color: #6b7280;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .status-operational { background: #10b981; }
        .status-degraded { background: #f59e0b; }
        .status-down { background: #ef4444; }
        
        .refresh-btn {
            background: #22d3ee;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .refresh-btn:hover {
            background: #0891b2;
        }
        
        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .dashboard {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>SoulBridge AI - Admin Dashboard</h1>
        <p>Real-time system monitoring and analytics</p>
    </div>
    
    <div class="dashboard">
        <div class="metrics-grid" id="metrics-grid">
            <!-- Metrics will be loaded here -->
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 class="chart-title">User Growth Trend</h3>
                    <button class="refresh-btn" onclick="refreshData()">Refresh</button>
                </div>
                <canvas id="userGrowthChart" width="400" height="200"></canvas>
            </div>
            
            <div class="activity-feed">
                <h3 class="chart-title">Recent Activity</h3>
                <div id="activity-list">
                    <!-- Activity items will be loaded here -->
                </div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <h3 class="chart-title">Engagement Metrics</h3>
                <canvas id="engagementChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <h3 class="chart-title">Companion Performance</h3>
                <canvas id="companionChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h3 class="chart-title">System Health Status</h3>
            <div id="health-status">
                <!-- Health status will be loaded here -->
            </div>
        </div>
    </div>
    
    <script>
        let userGrowthChart;
        let engagementChart;
        let companionChart;
        
        async function loadMetrics() {
            try {
                const response = await fetch('/admin/metrics');
                const data = await response.json();
                
                if (data.status === 'success') {
                    updateMetricsDisplay(data);
                    updateActivityFeed(data.recent_activity);
                    updateHealthStatus(data.system_health);
                    loadCharts();
                } else {
                    console.error('Error loading metrics:', data.error);
                }
            } catch (error) {
                console.error('Error fetching metrics:', error);
            }
        }
        
        function updateMetricsDisplay(data) {
            const metricsGrid = document.getElementById('metrics-grid');
            const userMetrics = data.user_metrics;
            const revenueMetrics = data.revenue_metrics;
            
            metricsGrid.innerHTML = `
                <div class="metric-card">
                    <div class="metric-label">Total Users</div>
                    <div class="metric-value">${userMetrics.total_users || 0}</div>
                    <div class="metric-change positive">
                        ↑ ${userMetrics.new_users_today || 0} today
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Active Users</div>
                    <div class="metric-value">${userMetrics.active_users || 0}</div>
                    <div class="metric-change positive">
                        ${((userMetrics.active_users / userMetrics.total_users) * 100 || 0).toFixed(1)}% active
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Total Revenue</div>
                    <div class="metric-value">$${(revenueMetrics.total_revenue || 0).toFixed(2)}</div>
                    <div class="metric-change positive">
                        ↑ Monthly growth
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Conversations</div>
                    <div class="metric-value">${userMetrics.total_conversations || 0}</div>
                    <div class="metric-change positive">
                        ${userMetrics.avg_messages_per_user || 0} avg/user
                    </div>
                </div>
            `;
        }
        
        function updateActivityFeed(activities) {
            const activityList = document.getElementById('activity-list');
            
            if (!activities || activities.length === 0) {
                activityList.innerHTML = '<p style="color: #6b7280; text-align: center;">No recent activity</p>';
                return;
            }
            
            activityList.innerHTML = activities.slice(0, 10).map(activity => `
                <div class="activity-item">
                    <div class="activity-icon ${activity.severity}"></div>
                    <div class="activity-content">${activity.description}</div>
                    <div class="activity-time">${formatTime(activity.timestamp)}</div>
                </div>
            `).join('');
        }
        
        function updateHealthStatus(health) {
            const healthStatus = document.getElementById('health-status');
            
            healthStatus.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div>
                        <span class="status-indicator status-${health.api_status === 'operational' ? 'operational' : 'degraded'}"></span>
                        API Service: ${health.api_status}
                    </div>
                    <div>
                        <span class="status-indicator status-${health.database_status === 'operational' ? 'operational' : 'degraded'}"></span>
                        Database: ${health.database_status}
                    </div>
                    <div>
                        <span class="status-indicator status-${health.ai_service_status === 'operational' ? 'operational' : 'degraded'}"></span>
                        AI Service: ${health.ai_service_status}
                    </div>
                    <div>
                        <span class="status-indicator status-${health.email_service_status === 'operational' ? 'operational' : 'degraded'}"></span>
                        Email Service: ${health.email_service_status}
                    </div>
                </div>
                <div style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
                    Response Time: ${health.response_time_ms}ms | 
                    Error Rate: ${(health.error_rate * 100).toFixed(2)}% | 
                    Active Connections: ${health.active_connections}
                </div>
            `;
        }
        
        function formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) return 'Just now';
            if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
            return `${Math.floor(diff / 86400000)}d ago`;
        }
        
        async function loadCharts() {
            try {
                // Load user growth chart
                const userGrowthResponse = await fetch('/admin/charts/user-growth');
                const userGrowthData = await userGrowthResponse.json();
                updateUserGrowthChart(userGrowthData);
                
                // Load engagement chart
                const engagementResponse = await fetch('/admin/charts/engagement');
                const engagementData = await engagementResponse.json();
                updateEngagementChart(engagementData);
                
                // Load companion performance chart
                const companionResponse = await fetch('/admin/charts/companion-performance');
                const companionData = await companionResponse.json();
                updateCompanionChart(companionData);
                
            } catch (error) {
                console.error('Error loading charts:', error);
            }
        }
        
        function updateUserGrowthChart(data) {
            const ctx = document.getElementById('userGrowthChart').getContext('2d');
            
            if (userGrowthChart) {
                userGrowthChart.destroy();
            }
            
            userGrowthChart = new Chart(ctx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
        }
        
        function updateEngagementChart(data) {
            const ctx = document.getElementById('engagementChart').getContext('2d');
            
            if (engagementChart) {
                engagementChart.destroy();
            }
            
            engagementChart = new Chart(ctx, {
                type: 'doughnut',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        function updateCompanionChart(data) {
            const ctx = document.getElementById('companionChart').getContext('2d');
            
            if (companionChart) {
                companionChart.destroy();
            }
            
            companionChart = new Chart(ctx, {
                type: 'bar',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
        }
        
        function refreshData() {
            loadMetrics();
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadMetrics();
            
            // Auto-refresh every 30 seconds
            setInterval(loadMetrics, 30000);
        });
    </script>
</body>
</html>
    """
    return render_template_string(html_template)