# Data Visualization and Reporting System
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import base64
import io
from business_intelligence import BusinessIntelligenceManager

logger = logging.getLogger(__name__)

class DataVisualizationManager:
    """Advanced data visualization and reporting system"""
    
    def __init__(self, db_manager=None, bi_manager=None):
        self.db = db_manager
        self.bi_manager = bi_manager or BusinessIntelligenceManager(db_manager)
        
    def generate_user_growth_chart_data(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate user growth chart data"""
        try:
            chart_data = {
                "labels": [],
                "datasets": [{
                    "label": "New Users",
                    "data": [],
                    "borderColor": "#22d3ee",
                    "backgroundColor": "rgba(34, 211, 238, 0.1)",
                    "tension": 0.4
                }, {
                    "label": "Total Users",
                    "data": [],
                    "borderColor": "#0891b2",
                    "backgroundColor": "rgba(8, 145, 178, 0.1)",
                    "tension": 0.4
                }]
            }
            
            if self.db:
                cursor = self.db.connection.cursor()
                total_users = 0
                
                for i in range(period_days):
                    date = datetime.now() - timedelta(days=period_days - 1 - i)
                    date_str = date.strftime('%Y-%m-%d')
                    label = date.strftime('%m/%d')
                    
                    # Get new users for this day
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM users 
                        WHERE DATE(created_at) = ?
                    """, (date_str,))
                    
                    new_users = cursor.fetchone()[0]
                    total_users += new_users
                    
                    chart_data["labels"].append(label)
                    chart_data["datasets"][0]["data"].append(new_users)
                    chart_data["datasets"][1]["data"].append(total_users)
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating user growth chart: {e}")
            return {
                "labels": [],
                "datasets": [],
                "error": str(e)
            }
    
    def generate_engagement_metrics_chart(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate engagement metrics chart data"""
        try:
            chart_data = {
                "labels": ["Daily Active Users", "Weekly Active Users", "Monthly Active Users"],
                "datasets": [{
                    "data": [0, 0, 0],
                    "backgroundColor": [
                        "#22d3ee",
                        "#0891b2",
                        "#0e7490"
                    ],
                    "borderWidth": 0
                }]
            }
            
            if self.db:
                cursor = self.db.connection.cursor()
                
                # Daily active users (last 24 hours)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM conversations 
                    WHERE created_at > datetime('now', '-1 day')
                """)
                dau = cursor.fetchone()[0]
                
                # Weekly active users (last 7 days)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM conversations 
                    WHERE created_at > datetime('now', '-7 days')
                """)
                wau = cursor.fetchone()[0]
                
                # Monthly active users (last 30 days)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM conversations 
                    WHERE created_at > datetime('now', '-30 days')
                """)
                mau = cursor.fetchone()[0]
                
                chart_data["datasets"][0]["data"] = [dau, wau, mau]
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating engagement chart: {e}")
            return {
                "labels": [],
                "datasets": [],
                "error": str(e)
            }
    
    def generate_companion_performance_chart(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate companion performance comparison chart"""
        try:
            chart_data = {
                "labels": ["Blayzo", "Blayzica"],
                "datasets": [{
                    "label": "Total Interactions",
                    "data": [0, 0],
                    "backgroundColor": ["#22d3ee", "#f59e0b"],
                    "borderWidth": 0
                }, {
                    "label": "Avg Session Duration (min)",
                    "data": [0, 0],
                    "backgroundColor": ["rgba(34, 211, 238, 0.6)", "rgba(245, 158, 11, 0.6)"],
                    "borderWidth": 0
                }]
            }
            
            if self.db:
                cursor = self.db.connection.cursor()
                
                companions = ["Blayzo", "Blayzica"]
                interactions = []
                durations = []
                
                for companion in companions:
                    # Get total interactions
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM conversations 
                        WHERE ai_companion = ? AND created_at > datetime('now', '-{} days')
                    """.format(period_days), (companion,))
                    
                    interaction_count = cursor.fetchone()[0]
                    interactions.append(interaction_count)
                    
                    # Mock average session duration (in minutes)
                    # In a real implementation, you'd calculate this from actual session data
                    avg_duration = 15 + (hash(companion) % 20)  # Mock: 15-35 minutes
                    durations.append(avg_duration)
                
                chart_data["datasets"][0]["data"] = interactions
                chart_data["datasets"][1]["data"] = durations
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating companion performance chart: {e}")
            return {
                "labels": [],
                "datasets": [],
                "error": str(e)
            }
    
    def generate_revenue_trend_chart(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate revenue trend chart data"""
        try:
            chart_data = {
                "labels": [],
                "datasets": [{
                    "label": "Daily Revenue ($)",
                    "data": [],
                    "borderColor": "#10b981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "tension": 0.4,
                    "fill": True
                }]
            }
            
            # Generate mock revenue data (in a real app, this would come from payment processing)
            for i in range(period_days):
                date = datetime.now() - timedelta(days=period_days - 1 - i)
                label = date.strftime('%m/%d')
                
                # Mock daily revenue calculation
                base_revenue = 100
                day_factor = (i % 7) + 1  # Weekly pattern
                random_factor = (hash(date.strftime('%Y-%m-%d')) % 50) / 10  # Pseudo-random variation
                daily_revenue = base_revenue * day_factor + random_factor
                
                chart_data["labels"].append(label)
                chart_data["datasets"][0]["data"].append(round(daily_revenue, 2))
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating revenue chart: {e}")
            return {
                "labels": [],
                "datasets": [],
                "error": str(e)
            }
    
    def generate_user_segmentation_chart(self) -> Dict[str, Any]:
        """Generate user segmentation pie chart"""
        try:
            chart_data = {
                "labels": ["Free Users", "Premium Users", "Enterprise Users"],
                "datasets": [{
                    "data": [0, 0, 0],
                    "backgroundColor": [
                        "#6b7280",
                        "#22d3ee", 
                        "#f59e0b"
                    ],
                    "borderWidth": 2,
                    "borderColor": "#ffffff"
                }]
            }
            
            if self.db:
                cursor = self.db.connection.cursor()
                
                # Count users by subscription tier
                cursor.execute("""
                    SELECT 
                        subscription_tier,
                        COUNT(*) as count
                    FROM users 
                    GROUP BY subscription_tier
                """)
                
                results = cursor.fetchall()
                tier_counts = {"free": 0, "premium": 0, "enterprise": 0}
                
                for tier, count in results:
                    if tier and tier.lower() in tier_counts:
                        tier_counts[tier.lower()] = count
                
                chart_data["datasets"][0]["data"] = [
                    tier_counts["free"],
                    tier_counts["premium"], 
                    tier_counts["enterprise"]
                ]
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating segmentation chart: {e}")
            return {
                "labels": [],
                "datasets": [],
                "error": str(e)
            }
    
    def generate_comprehensive_report(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        try:
            report = {
                "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "generated_at": datetime.now().isoformat(),
                "period_days": period_days,
                "charts": {
                    "user_growth": self.generate_user_growth_chart_data(period_days),
                    "engagement_metrics": self.generate_engagement_metrics_chart(period_days),
                    "companion_performance": self.generate_companion_performance_chart(period_days),
                    "revenue_trend": self.generate_revenue_trend_chart(period_days),
                    "user_segmentation": self.generate_user_segmentation_chart()
                },
                "summary": self._generate_report_summary(period_days),
                "recommendations": self._generate_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def _generate_report_summary(self, period_days: int) -> Dict[str, Any]:
        """Generate executive summary for the report"""
        try:
            summary = {
                "key_metrics": {},
                "highlights": [],
                "concerns": []
            }
            
            # Get basic metrics from BI manager
            user_analytics = self.bi_manager.get_comprehensive_user_analytics(period_days)
            revenue_analytics = self.bi_manager.get_revenue_analytics(period_days)
            
            summary["key_metrics"] = {
                "total_users": user_analytics.get("total_users", 0),
                "active_users": user_analytics.get("active_users", 0),
                "total_revenue": revenue_analytics.get("total_revenue", 0),
                "conversion_rate": revenue_analytics.get("conversion_rate", 0)
            }
            
            # Generate highlights based on metrics
            if user_analytics.get("new_users_today", 0) > 5:
                summary["highlights"].append("Strong daily user acquisition")
            
            if revenue_analytics.get("total_revenue", 0) > 1000:
                summary["highlights"].append("Revenue target exceeded")
            
            # Generate concerns
            if user_analytics.get("active_users", 0) / max(user_analytics.get("total_users", 1), 1) < 0.3:
                summary["concerns"].append("Low user engagement rate")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating report summary: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = [
            "Implement user onboarding flow to improve activation rates",
            "A/B test different companion personalities to optimize engagement",
            "Add push notifications for inactive users to improve retention",
            "Create premium features that justify subscription pricing",
            "Implement referral program to boost organic growth",
            "Add analytics dashboard for users to track their emotional journey"
        ]
        
        # Return a subset of recommendations
        return recommendations[:4]
    
    def export_report_data(self, report_data: Dict[str, Any], format_type: str = "json") -> Dict[str, Any]:
        """Export report data in various formats"""
        try:
            if format_type.lower() == "json":
                return {
                    "content": json.dumps(report_data, indent=2),
                    "content_type": "application/json",
                    "filename": f"soulbridge_report_{datetime.now().strftime('%Y%m%d')}.json"
                }
            
            elif format_type.lower() == "csv":
                # Generate CSV format for key metrics
                csv_content = "Metric,Value,Period\n"
                summary = report_data.get("summary", {}).get("key_metrics", {})
                
                for metric, value in summary.items():
                    csv_content += f"{metric},{value},{report_data.get('period_days', 30)}\n"
                
                return {
                    "content": csv_content,
                    "content_type": "text/csv",
                    "filename": f"soulbridge_metrics_{datetime.now().strftime('%Y%m%d')}.csv"
                }
            
            else:
                return {"error": f"Unsupported format: {format_type}"}
                
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return {"error": str(e)}