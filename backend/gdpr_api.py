"""
GDPR Compliance API Endpoints
REST API for data subject rights and privacy compliance
"""
import logging
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from datetime import datetime
from typing import Dict, List, Any
import json

from gdpr_compliance import get_gdpr_manager

logger = logging.getLogger(__name__)

# Authentication decorator
def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Create GDPR API blueprint
gdpr_api = Blueprint('gdpr_api', __name__, url_prefix='/api/gdpr')

@gdpr_api.route('/consent', methods=['POST'])
@require_auth
def record_consent():
    """Record user consent for data processing"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        consent_type = data.get('consent_type')
        granted = data.get('granted', False)
        legal_basis = data.get('legal_basis', 'consent')
        purpose = data.get('purpose', '')
        data_categories = data.get('data_categories', [])
        
        if not consent_type or not purpose:
            return jsonify({'error': 'consent_type and purpose are required'}), 400
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        success = gdpr_manager.record_consent(
            user_id, consent_type, granted, legal_basis, purpose, data_categories
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Consent recorded successfully',
                'consent_type': consent_type,
                'granted': granted,
                'recorded_at': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to record consent'}), 500
            
    except Exception as e:
        logger.error(f"Error recording consent: {e}")
        return jsonify({'error': 'Failed to record consent'}), 500

@gdpr_api.route('/consent', methods=['GET'])
@require_auth
def get_consents():
    """Get all consent records for the user"""
    try:
        user_id = session.get('user_id')
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        consents = gdpr_manager.get_user_consents(user_id)
        
        consents_data = []
        for consent in consents:
            consent_dict = {
                'consent_type': consent.consent_type,
                'granted': consent.granted,
                'granted_at': consent.granted_at.isoformat(),
                'withdrawn_at': consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                'legal_basis': consent.legal_basis,
                'purpose': consent.purpose,
                'data_categories': consent.data_categories
            }
            consents_data.append(consent_dict)
        
        return jsonify({
            'success': True,
            'consents': consents_data,
            'total_consents': len(consents_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting consents: {e}")
        return jsonify({'error': 'Failed to get consents'}), 500

@gdpr_api.route('/data-request', methods=['POST'])
@require_auth
def submit_data_request():
    """Submit a data subject request (access, delete, export, etc.)"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        request_type = data.get('request_type')
        data_categories = data.get('data_categories', [])
        
        # Validate request type
        valid_types = ['access', 'delete', 'export', 'rectify', 'object', 'restrict']
        if request_type not in valid_types:
            return jsonify({
                'error': f'Invalid request type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        request_id = gdpr_manager.submit_data_subject_request(
            user_id, request_type, data_categories
        )
        
        if request_id:
            return jsonify({
                'success': True,
                'request_id': request_id,
                'request_type': request_type,
                'status': 'pending',
                'submitted_at': datetime.now().isoformat(),
                'message': f'Data {request_type} request submitted successfully'
            })
        else:
            return jsonify({'error': 'Failed to submit data request'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting data request: {e}")
        return jsonify({'error': 'Failed to submit data request'}), 500

@gdpr_api.route('/data-request/<request_id>', methods=['GET'])
@require_auth
def get_data_request_status(request_id):
    """Get status of a data subject request"""
    try:
        user_id = session.get('user_id')
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        # Get request details from database
        query = "SELECT * FROM data_subject_requests WHERE request_id = ? AND user_id = ?"
        result = gdpr_manager.db.fetch_one(query, (request_id, user_id))
        
        if not result:
            return jsonify({'error': 'Request not found'}), 404
        
        request_data = {
            'request_id': result[0],
            'user_id': result[1],
            'request_type': result[2],
            'status': result[3],
            'requested_at': result[4],
            'completed_at': result[5],
            'data_categories': json.loads(result[6]) if result[6] else [],
            'notes': result[7],
            'verification_method': result[8]
        }
        
        return jsonify({
            'success': True,
            'request': request_data
        })
        
    except Exception as e:
        logger.error(f"Error getting request status: {e}")
        return jsonify({'error': 'Failed to get request status'}), 500

@gdpr_api.route('/data-requests', methods=['GET'])
@require_auth
def get_user_data_requests():
    """Get all data subject requests for the user"""
    try:
        user_id = session.get('user_id')
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        query = """
            SELECT request_id, request_type, status, requested_at, completed_at, notes
            FROM data_subject_requests 
            WHERE user_id = ? 
            ORDER BY requested_at DESC
        """
        
        results = gdpr_manager.db.fetch_all(query, (user_id,))
        
        requests = []
        for row in results:
            request_data = {
                'request_id': row[0],
                'request_type': row[1],
                'status': row[2],
                'requested_at': row[3],
                'completed_at': row[4],
                'notes': row[5]
            }
            requests.append(request_data)
        
        return jsonify({
            'success': True,
            'requests': requests,
            'total_requests': len(requests)
        })
        
    except Exception as e:
        logger.error(f"Error getting user requests: {e}")
        return jsonify({'error': 'Failed to get user requests'}), 500

@gdpr_api.route('/delete-account', methods=['POST'])
@require_auth
def delete_account():
    """Process account deletion request (Right to be Forgotten)"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        # Require confirmation
        confirmation = data.get('confirmation')
        if confirmation != 'DELETE_MY_ACCOUNT':
            return jsonify({
                'error': 'Account deletion requires confirmation. Send "DELETE_MY_ACCOUNT" in confirmation field'
            }), 400
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        # Submit deletion request
        request_id = gdpr_manager.submit_data_subject_request(user_id, 'delete')
        
        if request_id:
            # Log out user immediately
            session.clear()
            
            return jsonify({
                'success': True,
                'request_id': request_id,
                'message': 'Account deletion request submitted. Your data will be permanently deleted within 30 days.',
                'warning': 'This action cannot be undone. You have been logged out.'
            })
        else:
            return jsonify({'error': 'Failed to submit deletion request'}), 500
            
    except Exception as e:
        logger.error(f"Error processing account deletion: {e}")
        return jsonify({'error': 'Failed to process account deletion'}), 500

@gdpr_api.route('/data-export', methods=['POST'])
@require_auth
def request_data_export():
    """Request complete data export"""
    try:
        user_id = session.get('user_id')
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        request_id = gdpr_manager.submit_data_subject_request(user_id, 'export')
        
        if request_id:
            return jsonify({
                'success': True,
                'request_id': request_id,
                'message': 'Data export request submitted. You will receive a download link when ready.',
                'estimated_time': '24-48 hours'
            })
        else:
            return jsonify({'error': 'Failed to submit export request'}), 500
            
    except Exception as e:
        logger.error(f"Error requesting data export: {e}")
        return jsonify({'error': 'Failed to request data export'}), 500

@gdpr_api.route('/retention-check', methods=['POST'])
def check_retention_compliance():
    """Admin endpoint to check data retention compliance"""
    try:
        # In production, add admin authentication here
        
        gdpr_manager = get_gdpr_manager()
        if not gdpr_manager:
            return jsonify({'error': 'GDPR service unavailable'}), 503
        
        compliance_report = gdpr_manager.check_data_retention_compliance()
        
        return jsonify({
            'success': True,
            'compliance_report': compliance_report
        })
        
    except Exception as e:
        logger.error(f"Error checking retention compliance: {e}")
        return jsonify({'error': 'Failed to check retention compliance'}), 500

# Health check endpoint
@gdpr_api.route('/health', methods=['GET'])
def health_check():
    """Health check for GDPR API"""
    try:
        gdpr_manager = get_gdpr_manager()
        service_status = 'available' if gdpr_manager else 'unavailable'
        
        return jsonify({
            'status': 'healthy',
            'service': service_status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        })
        
    except Exception as e:
        logger.error(f"GDPR health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def init_gdpr_api():
    """Initialize GDPR API"""
    logger.info("GDPR API initialized")
    return gdpr_api