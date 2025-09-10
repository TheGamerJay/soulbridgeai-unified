"""
Export Routes
API endpoints for exporting content in various formats
"""

import logging
from flask import Blueprint, request, jsonify, session, send_file
from datetime import datetime, timezone
import traceback
import json
import io

from services.export_system import create_export_system, ExportFormat
from security_config import require_auth, rate_limit_moderate
from database import get_user_plan

logger = logging.getLogger(__name__)

# Create blueprint
export_bp = Blueprint('export', __name__, url_prefix='/api/export')

# Initialize export system
try:
    export_system = create_export_system()
    logger.info("✅ Export system loaded")
except Exception as e:
    logger.error(f"❌ Failed to load export system: {e}")
    export_system = None

@export_bp.route('/formats', methods=['GET'])
@require_auth
def get_supported_formats():
    """Get list of supported export formats"""
    
    if not export_system:
        return jsonify({
            'success': False,
            'error': 'Export system unavailable'
        }), 503
    
    try:
        formats = export_system.get_supported_formats()
        
        format_details = {
            ExportFormat.TXT: {
                'name': 'Plain Text',
                'description': 'Simple text file with basic formatting',
                'extension': 'txt',
                'mime_type': 'text/plain'
            },
            ExportFormat.PDF: {
                'name': 'PDF Document',
                'description': 'Professional formatted PDF document',
                'extension': 'pdf',
                'mime_type': 'application/pdf'
            },
            ExportFormat.DOCX: {
                'name': 'Word Document',
                'description': 'Microsoft Word compatible document',
                'extension': 'docx',
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            },
            ExportFormat.JSON: {
                'name': 'JSON Data',
                'description': 'Structured data format with metadata',
                'extension': 'json',
                'mime_type': 'application/json'
            },
            ExportFormat.MD: {
                'name': 'Markdown',
                'description': 'Markdown formatted text file',
                'extension': 'md',
                'mime_type': 'text/markdown'
            },
            ExportFormat.HTML: {
                'name': 'HTML Document',
                'description': 'Web-ready HTML document',
                'extension': 'html',
                'mime_type': 'text/html'
            }
        }
        
        available_formats = []
        for format_code in formats:
            if format_code in format_details:
                format_info = format_details[format_code].copy()
                format_info['code'] = format_code
                available_formats.append(format_info)
        
        return jsonify({
            'success': True,
            'formats': available_formats,
            'count': len(available_formats)
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_supported_formats: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@export_bp.route('/poem', methods=['POST'])
@require_auth
@rate_limit_moderate()
def export_poem():
    """Export a poem in specified format"""
    
    if not export_system:
        return jsonify({
            'success': False,
            'error': 'Export system unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        poem_data = data.get('poem_data', {})
        format_code = data.get('format', 'txt').lower()
        
        if not poem_data or not poem_data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Poem data and content are required'
            }), 400
        
        # Check format support
        if format_code not in export_system.get_supported_formats():
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_code}',
                'supported_formats': export_system.get_supported_formats()
            }), 400
        
        # Check premium format restrictions
        premium_formats = [ExportFormat.PDF, ExportFormat.DOCX]
        if format_code in premium_formats and user_plan == 'bronze':
            return jsonify({
                'success': False,
                'error': f'{format_code.upper()} export requires Silver or Gold tier',
                'upgrade_required': True
            }), 403
        
        # Export the poem
        exported_data = export_system.export_poem(poem_data, format_code)
        
        # Prepare filename
        title = poem_data.get('title', 'poem').replace(' ', '_').replace('/', '_')
        filename = f"{title}.{format_code}"
        
        # Set appropriate mime type
        mime_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'json': 'application/json',
            'md': 'text/markdown',
            'html': 'text/html'
        }
        mime_type = mime_types.get(format_code, 'application/octet-stream')
        
        logger.info(f"✅ Exported poem for user {user_id} in {format_code} format")
        
        # Return file
        return send_file(
            io.BytesIO(exported_data),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"❌ Error in export_poem: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@export_bp.route('/story', methods=['POST'])
@require_auth
@rate_limit_moderate()
def export_story():
    """Export a story in specified format"""
    
    if not export_system:
        return jsonify({
            'success': False,
            'error': 'Export system unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        story_data = data.get('story_data', {})
        format_code = data.get('format', 'txt').lower()
        
        if not story_data or not story_data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Story data and content are required'
            }), 400
        
        # Check format support
        if format_code not in export_system.get_supported_formats():
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_code}',
                'supported_formats': export_system.get_supported_formats()
            }), 400
        
        # Check premium format restrictions
        premium_formats = [ExportFormat.PDF, ExportFormat.DOCX]
        if format_code in premium_formats and user_plan == 'bronze':
            return jsonify({
                'success': False,
                'error': f'{format_code.upper()} export requires Silver or Gold tier',
                'upgrade_required': True
            }), 403
        
        # Export the story
        exported_data = export_system.export_story(story_data, format_code)
        
        # Prepare filename
        title = story_data.get('title', 'story').replace(' ', '_').replace('/', '_')
        filename = f"{title}.{format_code}"
        
        # Set appropriate mime type
        mime_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'json': 'application/json',
            'md': 'text/markdown',
            'html': 'text/html'
        }
        mime_type = mime_types.get(format_code, 'application/octet-stream')
        
        logger.info(f"✅ Exported story for user {user_id} in {format_code} format")
        
        # Return file
        return send_file(
            io.BytesIO(exported_data),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"❌ Error in export_story: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@export_bp.route('/writing', methods=['POST'])
@require_auth
@rate_limit_moderate()
def export_writing():
    """Export writing in specified format"""
    
    if not export_system:
        return jsonify({
            'success': False,
            'error': 'Export system unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        writing_data = data.get('writing_data', {})
        format_code = data.get('format', 'txt').lower()
        
        if not writing_data or not writing_data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Writing data and content are required'
            }), 400
        
        # Check format support
        if format_code not in export_system.get_supported_formats():
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_code}',
                'supported_formats': export_system.get_supported_formats()
            }), 400
        
        # Check premium format restrictions
        premium_formats = [ExportFormat.PDF, ExportFormat.DOCX]
        if format_code in premium_formats and user_plan == 'bronze':
            return jsonify({
                'success': False,
                'error': f'{format_code.upper()} export requires Silver or Gold tier',
                'upgrade_required': True
            }), 403
        
        # Export the writing
        exported_data = export_system.export_writing(writing_data, format_code)
        
        # Prepare filename
        title = writing_data.get('title', 'writing').replace(' ', '_').replace('/', '_')
        filename = f"{title}.{format_code}"
        
        # Set appropriate mime type
        mime_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'json': 'application/json',
            'md': 'text/markdown',
            'html': 'text/html'
        }
        mime_type = mime_types.get(format_code, 'application/octet-stream')
        
        logger.info(f"✅ Exported writing for user {user_id} in {format_code} format")
        
        # Return file
        return send_file(
            io.BytesIO(exported_data),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"❌ Error in export_writing: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@export_bp.route('/collection', methods=['POST'])
@require_auth
@rate_limit_moderate()
def export_collection():
    """Export multiple items as a collection"""
    
    if not export_system:
        return jsonify({
            'success': False,
            'error': 'Export system unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        items = data.get('items', [])
        format_code = data.get('format', 'txt').lower()
        collection_name = data.get('collection_name', 'Collection')
        
        if not items:
            return jsonify({
                'success': False,
                'error': 'Items are required for collection export'
            }), 400
        
        if len(items) > 50:
            return jsonify({
                'success': False,
                'error': 'Maximum 50 items per collection'
            }), 400
        
        # Check format support
        if format_code not in export_system.get_supported_formats():
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_code}',
                'supported_formats': export_system.get_supported_formats()
            }), 400
        
        # Check premium format restrictions
        premium_formats = [ExportFormat.PDF, ExportFormat.DOCX]
        if format_code in premium_formats and user_plan == 'bronze':
            return jsonify({
                'success': False,
                'error': f'{format_code.upper()} export requires Silver or Gold tier',
                'upgrade_required': True
            }), 403
        
        # Check collection export limits
        if user_plan == 'bronze' and len(items) > 5:
            return jsonify({
                'success': False,
                'error': 'Bronze tier limited to 5 items per collection',
                'upgrade_required': True
            }), 403
        elif user_plan == 'silver' and len(items) > 20:
            return jsonify({
                'success': False,
                'error': 'Silver tier limited to 20 items per collection'
            }), 403
        
        # Export the collection
        exported_data = export_system.export_collection(items, format_code, collection_name)
        
        # Prepare filename
        safe_name = collection_name.replace(' ', '_').replace('/', '_')
        if format_code in ['txt', 'json']:
            filename = f"{safe_name}.{format_code}"
            mime_type = 'text/plain' if format_code == 'txt' else 'application/json'
        else:
            filename = f"{safe_name}.zip"
            mime_type = 'application/zip'
        
        logger.info(f"✅ Exported collection for user {user_id}: {len(items)} items in {format_code} format")
        
        # Return file
        return send_file(
            io.BytesIO(exported_data),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"❌ Error in export_collection: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@export_bp.route('/stats', methods=['GET'])
@require_auth
@rate_limit_moderate()
def get_export_stats():
    """Get export statistics and user limits"""
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Export limits by plan
        export_limits = {
            'bronze': {
                'formats': ['txt', 'json', 'md', 'html'],
                'collection_size': 5,
                'premium_formats': False
            },
            'silver': {
                'formats': export_system.get_supported_formats() if export_system else [],
                'collection_size': 20,
                'premium_formats': True
            },
            'gold': {
                'formats': export_system.get_supported_formats() if export_system else [],
                'collection_size': 50,
                'premium_formats': True
            }
        }
        
        user_limits = export_limits.get(user_plan, export_limits['bronze'])
        
        stats = {
            'user_plan': user_plan,
            'available_formats': user_limits['formats'],
            'max_collection_size': user_limits['collection_size'],
            'premium_formats_available': user_limits['premium_formats'],
            'features': {
                'pdf_export': user_plan in ['silver', 'gold'],
                'docx_export': user_plan in ['silver', 'gold'],
                'collection_export': True,
                'unlimited_exports': user_plan == 'gold',
                'batch_processing': user_plan in ['silver', 'gold']
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_export_stats: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500