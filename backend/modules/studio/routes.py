"""
SoulBridge AI - Mini Studio Routes
Professional music production endpoints integrated with Docker services
"""
import logging
from flask import Blueprint, render_template, request, session, jsonify, redirect, send_file
from ..auth.session_manager import requires_login, get_user_id
from ..tiers.access_control import require_gold_access
from .studio_service import StudioService
from io import BytesIO

logger = logging.getLogger(__name__)

# Create blueprint for studio routes
studio_bp = Blueprint('studio', __name__)

@studio_bp.route("/mini-studio")
@requires_login
@require_gold_access
def mini_studio():
    """Mini Studio - Professional music production interface"""
    try:
        user_id = get_user_id()
        studio_service = StudioService()
        
        # Get user credits
        credits_info = studio_service.get_user_credits(user_id)
        credits = credits_info.get('credits_remaining', 0) if credits_info['success'] else 0
        
        # Check studio health
        health_check = studio_service.check_studio_health()
        
        return render_template("mini_studio.html",
                             credits=credits,
                             studio_healthy=health_check.get('all_healthy', False),
                             services_status=health_check.get('services', {}))
        
    except Exception as e:
        logger.error(f"Error loading mini studio: {e}")
        return render_template("error.html", error="Unable to load Mini Studio")

@studio_bp.route("/mini-studio-simple")
@requires_login
@require_gold_access
def mini_studio_simple():
    """Mini Studio Simple - Streamlined interface"""
    return redirect("/mini-studio")  # Redirect to main studio

# API Endpoints for studio functionality
@studio_bp.route("/api/mini-studio/status")
@requires_login
@require_gold_access
def api_studio_status():
    """Get studio status and user credits"""
    try:
        user_id = get_user_id()
        studio_service = StudioService()
        
        # Get credits and health status
        credits_info = studio_service.get_user_credits(user_id)
        health_check = studio_service.check_studio_health()
        
        return jsonify({
            "success": True,
            "credits_remaining": credits_info.get('credits_remaining', 0),
            "studio_healthy": health_check.get('all_healthy', False),
            "services": health_check.get('services', {})
        })
        
    except Exception as e:
        logger.error(f"Error getting studio status: {e}")
        return jsonify({"success": False, "error": "Failed to get studio status"}), 500

@studio_bp.route("/api/mini-studio/project", methods=["POST"])
@requires_login
@require_gold_access
def api_ensure_project():
    """Ensure user has a studio project"""
    try:
        user_id = get_user_id()
        studio_service = StudioService()
        
        result = studio_service.ensure_project(user_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "project_id": result["data"]["project_id"]
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error ensuring project: {e}")
        return jsonify({"success": False, "error": "Failed to create project"}), 500

@studio_bp.route("/api/mini-studio/lyrics/generate", methods=["POST"])
@requires_login
@require_gold_access
def api_generate_lyrics():
    """Generate lyrics using OpenAI with structured outputs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = get_user_id()
        studio_service = StudioService()
        
        # Extract parameters
        project_id = data.get('project_id')
        concept = data.get('concept', 'heartbreak to healing')
        bpm = data.get('bpm', 94)
        key_hint = data.get('key_hint', 'A minor')
        language = data.get('language', 'spanglish')
        
        if not project_id:
            return jsonify({"success": False, "error": "Project ID required"}), 400
        
        result = studio_service.generate_lyrics(user_id, project_id, concept, bpm, key_hint, language)
        
        if result["success"]:
            # 📚 AUTO-SAVE: Save generated lyrics to library
            auto_saved = False
            try:
                from ..library.library_manager import LibraryManager
                from ..shared.database import get_database
                
                database = get_database()
                library_manager = LibraryManager(database)
                
                # Create readable title from concept
                title = f"Studio Lyrics: {concept[:50]}{'...' if len(concept) > 50 else ''}"
                
                # Prepare content for library storage
                lyrics_content = {
                    'asset_id': result["data"]["assetId"],
                    'project_id': project_id,
                    'concept': concept,
                    'bpm': bpm,
                    'key_hint': key_hint,
                    'language': language,
                    'generated_at': datetime.now().isoformat(),
                    'cost': 5,
                    'type': 'mini_studio_lyrics'
                }
                
                # Save to library with metadata
                content_id = library_manager.add_content(
                    user_id=user_id,
                    content_type='mini_studio',
                    title=title,
                    content=str(lyrics_content),  # Store as string for now
                    metadata={
                        'studio_type': 'lyrics',
                        'asset_id': result["data"]["assetId"],
                        'concept': concept,
                        'bpm': bpm,
                        'language': language,
                        'cost': 5,
                        'user_tier': 'gold'  # Mini studio is Gold-only
                    }
                )
                
                auto_saved = bool(content_id)
                if auto_saved:
                    logger.info(f"🎵 Auto-saved studio lyrics {content_id} to library for user {user_id}")
                else:
                    logger.warning(f"Failed to auto-save studio lyrics to library for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Auto-save studio lyrics error: {e}")
                auto_saved = False
                
            return jsonify({
                "success": True,
                "asset_id": result["data"]["assetId"],
                "cost": 5,
                "message": "Lyrics generated successfully",
                "auto_saved": auto_saved,
                "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
            })
        else:
            return jsonify(result), 402 if "credits" in result.get("error", "") else 500
            
    except Exception as e:
        logger.error(f"Error generating lyrics: {e}")
        return jsonify({"success": False, "error": "Lyrics generation failed"}), 500

@studio_bp.route("/api/mini-studio/beats/compose", methods=["POST"])
@requires_login
@require_gold_access
def api_compose_beat():
    """Generate beat using MusicGen with MIDI stems"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = get_user_id()
        studio_service = StudioService()
        
        # Extract parameters
        project_id = data.get('project_id')
        prompt = data.get('prompt', 'melodic trap beat, punchy drums, warm bass')
        bpm = data.get('bpm', 94)
        key = data.get('key', 'A minor')
        seconds = data.get('seconds', 15)
        demucs = data.get('demucs', False)
        
        if not project_id:
            return jsonify({"success": False, "error": "Project ID required"}), 400
        
        result = studio_service.compose_beat(user_id, project_id, prompt, bpm, key, seconds, demucs)
        
        if result["success"]:
            # 📚 AUTO-SAVE: Save generated beat to library
            auto_saved = False
            try:
                from ..library.library_manager import LibraryManager
                from ..shared.database import get_database
                
                database = get_database()
                library_manager = LibraryManager(database)
                
                # Create readable title from prompt
                title = f"Studio Beat: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                
                # Prepare content for library storage
                beat_content = {
                    'asset_id': result["data"]["assetId"],
                    'project_id': project_id,
                    'prompt': prompt,
                    'bpm': bpm,
                    'key': key,
                    'seconds': seconds,
                    'includes_stems': demucs,
                    'generated_at': datetime.now().isoformat(),
                    'cost': 10,
                    'type': 'mini_studio_beat'
                }
                
                # Save to library with metadata
                content_id = library_manager.add_content(
                    user_id=user_id,
                    content_type='mini_studio',
                    title=title,
                    content=str(beat_content),  # Store as string for now
                    metadata={
                        'studio_type': 'beat',
                        'asset_id': result["data"]["assetId"],
                        'prompt': prompt,
                        'bpm': bpm,
                        'key': key,
                        'duration_seconds': seconds,
                        'has_stems': demucs,
                        'cost': 10,
                        'user_tier': 'gold'  # Mini studio is Gold-only
                    }
                )
                
                auto_saved = bool(content_id)
                if auto_saved:
                    logger.info(f"🥁 Auto-saved studio beat {content_id} to library for user {user_id}")
                else:
                    logger.warning(f"Failed to auto-save studio beat to library for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Auto-save studio beat error: {e}")
                auto_saved = False
                
            return jsonify({
                "success": True,
                "asset_id": result["data"]["assetId"],
                "cost": 10,
                "message": "Beat composed successfully",
                "includes_stems": demucs,
                "auto_saved": auto_saved,
                "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
            })
        else:
            return jsonify(result), 402 if "credits" in result.get("error", "") else 500
            
    except Exception as e:
        logger.error(f"Error composing beat: {e}")
        return jsonify({"success": False, "error": "Beat composition failed"}), 500

@studio_bp.route("/api/mini-studio/vocals/sing", methods=["POST"])
@requires_login
@require_gold_access
def api_generate_vocals():
    """Generate vocals using DiffSinger"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = get_user_id()
        studio_service = StudioService()
        
        # Extract parameters
        project_id = data.get('project_id')
        lyrics_asset_id = data.get('lyrics_asset_id')
        beat_asset_id = data.get('beat_asset_id')
        midi_asset_id = data.get('midi_asset_id')
        bpm = data.get('bpm', 94)
        
        if not project_id:
            return jsonify({"success": False, "error": "Project ID required"}), 400
        
        result = studio_service.generate_vocals(user_id, project_id, lyrics_asset_id, beat_asset_id, midi_asset_id, bpm)
        
        if result["success"]:
            # 📚 AUTO-SAVE: Save generated vocals to library
            auto_saved = False
            try:
                from ..library.library_manager import LibraryManager
                from ..shared.database import get_database
                
                database = get_database()
                library_manager = LibraryManager(database)
                
                # Create readable title
                title = f"Studio Vocals: Project {project_id}"
                
                # Prepare content for library storage
                vocals_content = {
                    'asset_id': result["data"]["assetId"],
                    'project_id': project_id,
                    'lyrics_asset_id': lyrics_asset_id,
                    'beat_asset_id': beat_asset_id,
                    'midi_asset_id': midi_asset_id,
                    'bpm': bpm,
                    'generated_at': datetime.now().isoformat(),
                    'cost': result["data"].get("cost", 10),
                    'type': 'mini_studio_vocals'
                }
                
                # Save to library with metadata
                content_id = library_manager.add_content(
                    user_id=user_id,
                    content_type='mini_studio',
                    title=title,
                    content=str(vocals_content),  # Store as string for now
                    metadata={
                        'studio_type': 'vocals',
                        'asset_id': result["data"]["assetId"],
                        'project_id': project_id,
                        'bpm': bpm,
                        'has_lyrics': bool(lyrics_asset_id),
                        'has_beat': bool(beat_asset_id),
                        'has_midi': bool(midi_asset_id),
                        'cost': result["data"].get("cost", 10),
                        'user_tier': 'gold'  # Mini studio is Gold-only
                    }
                )
                
                auto_saved = bool(content_id)
                if auto_saved:
                    logger.info(f"🎤 Auto-saved studio vocals {content_id} to library for user {user_id}")
                else:
                    logger.warning(f"Failed to auto-save studio vocals to library for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Auto-save studio vocals error: {e}")
                auto_saved = False
                
            return jsonify({
                "success": True,
                "asset_id": result["data"]["assetId"],
                "cost": result["data"].get("cost", 10),
                "message": "Vocals generated successfully",
                "auto_saved": auto_saved,
                "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
            })
        else:
            return jsonify(result), 402 if "credits" in result.get("error", "") else 500
            
    except Exception as e:
        logger.error(f"Error generating vocals: {e}")
        return jsonify({"success": False, "error": "Vocal generation failed"}), 500

@studio_bp.route("/api/mini-studio/upload", methods=["POST"])
@requires_login
@require_gold_access
def api_upload_asset():
    """Upload asset to studio (lyrics, beat, midi)"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        project_id = request.form.get('project_id')
        asset_kind = request.form.get('kind')
        
        if not file or file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not project_id:
            return jsonify({"success": False, "error": "Project ID required"}), 400
        
        if asset_kind not in ['lyrics', 'beat', 'midi']:
            return jsonify({"success": False, "error": "Invalid asset kind"}), 400
        
        user_id = get_user_id()
        studio_service = StudioService()
        
        # Read file data
        file_data = file.read()
        filename = file.filename
        
        result = studio_service.upload_asset(user_id, project_id, file_data, filename, asset_kind)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "asset_id": result["data"]["assetId"],
                "origin": result["data"]["origin"],
                "message": f"{asset_kind.title()} uploaded successfully"
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error uploading asset: {e}")
        return jsonify({"success": False, "error": "Asset upload failed"}), 500

@studio_bp.route("/api/mini-studio/library")
@requires_login
@require_gold_access
def api_studio_library():
    """Get user's studio library"""
    try:
        user_id = get_user_id()
        studio_service = StudioService()
        
        result = studio_service.get_studio_library(user_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "library": result["data"]
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error getting studio library: {e}")
        return jsonify({"success": False, "error": "Failed to get library"}), 500

@studio_bp.route("/api/mini-studio/library/<asset_id>", methods=["DELETE"])
@requires_login
@require_gold_access
def api_delete_asset(asset_id):
    """Delete asset from studio library"""
    try:
        user_id = get_user_id()
        studio_service = StudioService()
        
        result = studio_service.delete_asset(user_id, asset_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Asset deleted successfully"
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error deleting asset: {e}")
        return jsonify({"success": False, "error": "Failed to delete asset"}), 500

@studio_bp.route("/api/mini-studio/export/<asset_id>")
@requires_login
@require_gold_access
def api_export_asset(asset_id):
    """Export/download asset from studio"""
    try:
        user_id = get_user_id()
        studio_service = StudioService()
        
        result = studio_service.export_asset(user_id, asset_id)
        
        if result["success"]:
            return send_file(
                BytesIO(result["content"]),
                as_attachment=True,
                download_name=result["filename"],
                mimetype=result["content_type"]
            )
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error exporting asset: {e}")
        return jsonify({"success": False, "error": "Failed to export asset"}), 500

# Health check endpoint
@studio_bp.route("/api/mini-studio/health")
def api_studio_health():
    """Check studio services health"""
    try:
        studio_service = StudioService()
        health_check = studio_service.check_studio_health()
        
        return jsonify({
            "success": True,
            "healthy": health_check.get('all_healthy', False),
            "services": health_check.get('services', {})
        })
        
    except Exception as e:
        logger.error(f"Error checking studio health: {e}")
        return jsonify({"success": False, "error": "Health check failed"}), 500