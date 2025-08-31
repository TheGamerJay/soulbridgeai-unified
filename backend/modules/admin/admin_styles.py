"""
SoulBridge AI - Admin Styles and Templates
Extracted from app.py monolith using strategic bulk extraction
"""

def get_admin_css() -> str:
    """Get admin dashboard CSS styles"""
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(255,255,255,0.1);
            padding: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .header h1 {
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }
        
        .nav {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        .nav a {
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .nav a:hover, .nav a.active {
            background: rgba(255,255,255,0.2);
            color: white;
        }
        
        .container {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
        }
        
        .stat-title {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }
        
        .stat-description {
            font-size: 0.8rem;
            opacity: 0.7;
        }
        
        .section {
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            margin-bottom: 1.5rem;
        }
        
        .section h2 {
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        
        .btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 0.75rem 1.5rem;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }
        
        .btn-danger {
            background: rgba(220,53,69,0.3);
            border-color: rgba(220,53,69,0.5);
        }
        
        .btn-danger:hover {
            background: rgba(220,53,69,0.5);
        }
        
        .btn-success {
            background: rgba(40,167,69,0.3);
            border-color: rgba(40,167,69,0.5);
        }
        
        .btn-success:hover {
            background: rgba(40,167,69,0.5);
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 5px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 0.9rem;
        }
        
        .form-control::placeholder {
            color: rgba(255,255,255,0.6);
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        .table th,
        .table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .table th {
            background: rgba(255,255,255,0.1);
            font-weight: 600;
        }
        
        .table tr:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .alert {
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            border: 1px solid transparent;
        }
        
        .alert-success {
            background: rgba(40,167,69,0.2);
            border-color: rgba(40,167,69,0.3);
            color: #d4edda;
        }
        
        .alert-danger {
            background: rgba(220,53,69,0.2);
            border-color: rgba(220,53,69,0.3);
            color: #f8d7da;
        }
        
        .alert-warning {
            background: rgba(255,193,7,0.2);
            border-color: rgba(255,193,7,0.3);
            color: #fff3cd;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            opacity: 0.7;
        }
        
        .loading::after {
            content: '⏳';
            display: block;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .nav {
                flex-direction: column;
            }
        }
    """

def get_admin_dashboard_template(stats: dict) -> str:
    """Generate admin dashboard HTML template"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🐕 WatchDog Admin Dashboard - SoulBridge AI</title>
        <style>
            {get_admin_css()}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐕 WATCHDOG ADMIN DASHBOARD</h1>
            <div class="nav">
                <a href="/admin/dashboard" class="active">📊 DASHBOARD</a>
                <a href="/admin/users">👥 USERS</a>
                <a href="/admin/trials">🎯 TRIALS</a>
                <a href="/admin/database">🗄️ DATABASE</a>
                <a href="/admin/surveillance">👁️ SURVEILLANCE</a>
                <a href="/admin/logout">🚪 LOGOUT</a>
            </div>
        </div>
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">Total Users</div>
                    <div class="stat-value">{stats.get('total_users', 0):,}</div>
                    <div class="stat-description">Registered accounts</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">Active Sessions</div>
                    <div class="stat-value">{stats.get('active_sessions', 0):,}</div>
                    <div class="stat-description">Currently online</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">Active Users (24h)</div>
                    <div class="stat-value">{stats.get('active_users', 0):,}</div>
                    <div class="stat-description">Daily active users</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">Database Status</div>
                    <div class="stat-value">{stats.get('database_status', {}).get('status', 'UNKNOWN')}</div>
                    <div class="stat-description">{stats.get('database_status', {}).get('message', 'Unknown status')}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-title">Premium Conversions</div>
                    <div class="stat-value">{stats.get('premium_conversions', 0):,}</div>
                    <div class="stat-description">Paid subscribers</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🛠️ Quick Actions</h2>
                <a href="/admin/users" class="btn">👥 Manage Users</a>
                <a href="/admin/trials/reset-all" class="btn btn-danger">🔄 Reset All Trials</a>
                <a href="/admin/trials/expire-all" class="btn btn-danger">⏰ Expire All Trials</a>
                <a href="/admin/database" class="btn">🗄️ Database Tools</a>
                <a href="/admin/sql" class="btn">📝 SQL Console</a>
            </div>
            
            <div class="section">
                <h2>⚠️ System Alerts</h2>
                <div class="alert alert-success">
                    ✅ All systems operational
                </div>
            </div>
        </div>
        
        <script>
            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    """