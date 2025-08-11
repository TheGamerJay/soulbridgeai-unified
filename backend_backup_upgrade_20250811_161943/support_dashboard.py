"""
Support Dashboard for Customer Service Team
Real-time ticket management and analytics
"""
from flask import Blueprint, render_template_string, request, jsonify, session
from functools import wraps
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

def create_support_dashboard(support_chatbot, db_manager):
    """Create support dashboard blueprint"""
    
    support_dashboard = Blueprint('support_dashboard', __name__, url_prefix='/support-dashboard')
    
    def require_admin_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In production, check for admin role
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    @support_dashboard.route('/')
    @require_admin_auth
    def dashboard():
        """Main support dashboard"""
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SoulBridge AI - Support Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 1rem;
            opacity: 0.9;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
        }
        
        .chart-title {
            color: #333;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .tickets-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
        }
        
        .section-title {
            color: #333;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 20px;
        }
        
        .tickets-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .tickets-table th,
        .tickets-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .tickets-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .status-open { background: #fff3cd; color: #856404; }
        .status-in_progress { background: #d1ecf1; color: #0c5460; }
        .status-resolved { background: #d4edda; color: #155724; }
        .status-closed { background: #f8d7da; color: #721c24; }
        
        .priority-high { color: #dc3545; font-weight: bold; }
        .priority-medium { color: #fd7e14; }
        .priority-low { color: #28a745; }
        .priority-urgent { color: #dc3545; background: #fff; padding: 2px 8px; border-radius: 4px; }
        
        .refresh-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            margin-bottom: 20px;
        }
        
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>🎯 Support Dashboard</h1>
            <p>Real-time customer support analytics and ticket management</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="totalTickets">-</div>
                <div class="stat-label">Total Tickets</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="openTickets">-</div>
                <div class="stat-label">Open Tickets</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avgResponseTime">-</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="satisfactionScore">-</div>
                <div class="stat-label">Satisfaction Score</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">Ticket Status Distribution</div>
                <canvas id="statusChart" width="400" height="300"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Daily Ticket Volume</div>
                <canvas id="volumeChart" width="400" height="300"></canvas>
            </div>
        </div>
        
        <div class="tickets-section">
            <div class="section-title">Recent Tickets</div>
            <button class="refresh-btn" onclick="loadDashboardData()">🔄 Refresh Data</button>
            <table class="tickets-table">
                <thead>
                    <tr>
                        <th>Ticket ID</th>
                        <th>Subject</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="ticketsTable">
                    <tr><td colspan="6">Loading tickets...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let statusChart, volumeChart;
        
        function initCharts() {
            // Status Distribution Chart
            const statusCtx = document.getElementById('statusChart').getContext('2d');
            statusChart = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Open', 'In Progress', 'Resolved', 'Closed'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            '#ffc107',
                            '#17a2b8',
                            '#28a745',
                            '#6c757d'
                        ],
                        borderWidth: 0
                    }]
                },
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
            
            // Volume Chart
            const volumeCtx = document.getElementById('volumeChart').getContext('2d');
            volumeChart = new Chart(volumeCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Daily Tickets',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        function updateStats(data) {
            document.getElementById('totalTickets').textContent = data.total_tickets || 0;
            document.getElementById('openTickets').textContent = data.open_tickets || 0;
            document.getElementById('avgResponseTime').textContent = data.avg_response_time || '< 1h';
            document.getElementById('satisfactionScore').textContent = (data.satisfaction_score || 4.5) + '/5';
        }
        
        function updateCharts(data) {
            // Update status chart
            const statusData = data.status_distribution || {};
            statusChart.data.datasets[0].data = [
                statusData.open || 0,
                statusData.in_progress || 0,
                statusData.resolved || 0,
                statusData.closed || 0
            ];
            statusChart.update();
            
            // Update volume chart
            const volumeData = data.daily_volume || {};
            volumeChart.data.labels = Object.keys(volumeData);
            volumeChart.data.datasets[0].data = Object.values(volumeData);
            volumeChart.update();
        }
        
        function updateTicketsTable(tickets) {
            const tbody = document.getElementById('ticketsTable');
            
            if (!tickets || tickets.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6">No tickets found</td></tr>';
                return;
            }
            
            tbody.innerHTML = tickets.map(ticket => `
                <tr>
                    <td>${ticket.id}</td>
                    <td>${ticket.subject}</td>
                    <td><span class="status-badge status-${ticket.status}">${ticket.status}</span></td>
                    <td><span class="priority-${ticket.priority}">${ticket.priority}</span></td>
                    <td>${new Date(ticket.created_at).toLocaleDateString()}</td>
                    <td>
                        <button onclick="viewTicket('${ticket.id}')">View</button>
                    </td>
                </tr>
            `).join('');
        }
        
        function viewTicket(ticketId) {
            // In a real app, this would open a ticket detail modal
            alert(`View ticket: ${ticketId}`);
        }
        
        async function loadDashboardData() {
            try {
                const response = await fetch('/support-dashboard/api/analytics');
                const data = await response.json();
                
                if (data.success) {
                    updateStats(data.analytics);
                    updateCharts(data.analytics);
                    updateTicketsTable(data.recent_tickets || []);
                } else {
                    console.error('Failed to load dashboard data:', data.error);
                }
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            loadDashboardData();
            
            // Auto-refresh every 30 seconds
            setInterval(loadDashboardData, 30000);
        });
    </script>
</body>
</html>
        """
        return dashboard_html
    
    @support_dashboard.route('/api/analytics')
    @require_admin_auth
    def get_analytics():
        """Get support analytics data"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database unavailable'}), 503
            
            # Get ticket statistics
            total_tickets_query = "SELECT COUNT(*) FROM support_tickets"
            total_tickets = db_manager.fetch_one(total_tickets_query)[0] if db_manager.fetch_one(total_tickets_query) else 0
            
            open_tickets_query = "SELECT COUNT(*) FROM support_tickets WHERE status = 'open'"
            open_tickets = db_manager.fetch_one(open_tickets_query)[0] if db_manager.fetch_one(open_tickets_query) else 0
            
            # Status distribution
            status_query = """
            SELECT status, COUNT(*) FROM support_tickets 
            GROUP BY status
            """
            status_results = db_manager.fetch_all(status_query) if db_manager else []
            status_distribution = {status: count for status, count in status_results}
            
            # Daily volume (last 7 days)
            volume_query = """
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM support_tickets 
            WHERE created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            volume_results = db_manager.fetch_all(volume_query) if db_manager else []
            daily_volume = {date: count for date, count in volume_results}
            
            # Average satisfaction score
            satisfaction_query = """
            SELECT AVG(satisfaction_rating) FROM support_tickets 
            WHERE satisfaction_rating IS NOT NULL
            """
            avg_satisfaction = db_manager.fetch_one(satisfaction_query)
            satisfaction_score = round(avg_satisfaction[0], 1) if avg_satisfaction and avg_satisfaction[0] else 4.5
            
            # Recent tickets
            recent_tickets_query = """
            SELECT id, subject, status, priority, created_at 
            FROM support_tickets 
            ORDER BY created_at DESC 
            LIMIT 10
            """
            recent_tickets_results = db_manager.fetch_all(recent_tickets_query) if db_manager else []
            recent_tickets = [
                {
                    'id': row[0],
                    'subject': row[1],
                    'status': row[2],
                    'priority': row[3],
                    'created_at': row[4]
                }
                for row in recent_tickets_results
            ]
            
            analytics = {
                'total_tickets': total_tickets,
                'open_tickets': open_tickets,
                'avg_response_time': '< 1h',  # Would be calculated from actual data
                'satisfaction_score': satisfaction_score,
                'status_distribution': status_distribution,
                'daily_volume': daily_volume
            }
            
            return jsonify({
                'success': True,
                'analytics': analytics,
                'recent_tickets': recent_tickets
            })
            
        except Exception as e:
            logger.error(f"Error getting support analytics: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @support_dashboard.route('/api/ticket/<ticket_id>')
    @require_admin_auth
    def get_ticket_details(ticket_id):
        """Get detailed ticket information"""
        try:
            if not db_manager:
                return jsonify({'error': 'Database unavailable'}), 503
            
            ticket_query = """
            SELECT * FROM support_tickets WHERE id = ?
            """
            ticket = db_manager.fetch_one(ticket_query, (ticket_id,))
            
            if not ticket:
                return jsonify({'error': 'Ticket not found'}), 404
            
            # Get conversation history
            conversation_query = """
            SELECT sender, message, timestamp FROM support_conversations 
            WHERE conversation_id LIKE ? 
            ORDER BY timestamp ASC
            """
            conversation = db_manager.fetch_all(conversation_query, (f"%{ticket_id}%",))
            
            ticket_data = {
                'id': ticket[0],
                'user_id': ticket[1],
                'subject': ticket[2],
                'description': ticket[3],
                'category': ticket[4],
                'priority': ticket[5],
                'status': ticket[6],
                'created_at': ticket[7],
                'updated_at': ticket[8],
                'assigned_agent': ticket[9],
                'resolution': ticket[10],
                'satisfaction_rating': ticket[11],
                'conversation': [
                    {'sender': msg[0], 'message': msg[1], 'timestamp': msg[2]}
                    for msg in conversation
                ]
            }
            
            return jsonify({
                'success': True,
                'ticket': ticket_data
            })
            
        except Exception as e:
            logger.error(f"Error getting ticket details: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return support_dashboard

def init_support_dashboard(support_chatbot, db_manager):
    """Initialize support dashboard blueprint"""
    try:
        dashboard = create_support_dashboard(support_chatbot, db_manager)
        logger.info("Support dashboard initialized successfully")
        return dashboard
    except Exception as e:
        logger.error(f"Error initializing support dashboard: {e}")
        return None