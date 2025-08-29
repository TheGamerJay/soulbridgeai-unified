
# Quick debug login - add this to app.py temporarily
@app.route('/debug-login', methods=['POST'])
def debug_login():
    try:
        from database_utils import get_database
        db = get_database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email, user_plan, trial_active FROM users WHERE email = ?', ('aceelnene@gmail.com',))
        result = cursor.fetchone()
        
        if result:
            user_id, email, user_plan, trial_active = result
            session['user_id'] = user_id
            session['user_email'] = email
            session['user_plan'] = user_plan or 'bronze'
            session['trial_active'] = bool(trial_active)
            session['logged_in'] = True
            
            return jsonify({
                'success': True,
                'message': 'Debug login successful',
                'user_plan': user_plan or 'bronze',
                'trial_active': bool(trial_active)
            })
        else:
            return jsonify({'success': False, 'error': 'User not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

