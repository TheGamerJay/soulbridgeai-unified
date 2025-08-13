# ====================================
# 📁 FILE: backend/routes/api_export.py
# ====================================
from flask import Blueprint, request, jsonify, session, abort
from studio.export import export_file
from studio.library import studio_library
import logging

logger = logging.getLogger(__name__)

def is_logged_in():
    return session.get('user_id') is not None

def get_effective_plan(user_plan, trial_active):
    if trial_active and user_plan == "free":
        return "max"
    return user_plan

bp = Blueprint("api_export", __name__)

@bp.route("/api/export/<asset_id>", methods=["GET"])
def api_export(asset_id):
    """Export and download files from the studio library"""
    try:
        if not is_logged_in():
            return abort(401)
        
        # Check access permissions
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        if effective_plan != 'max':
            return abort(403)
        
        user_id = session.get('user_id')
        fmt = request.args.get('fmt', '')  # Optional format conversion
        
        # Get asset from library
        asset = studio_library.get_asset(user_id, asset_id)
        if not asset:
            return abort(404)
        
        asset_path = asset['path']
        
        # Handle format conversion if requested
        if fmt and fmt.lower() in ['mp3', 'wav', 'mid', 'png']:
            original_ext = asset_path.split('.')[-1].lower()
            
            if fmt.lower() == 'mp3' and original_ext == 'wav':
                # Convert WAV to MP3
                try:
                    from studio.audio import wav_to_mp3
                    asset_path = wav_to_mp3(asset_path)
                except Exception as e:
                    logger.error(f"WAV to MP3 conversion error: {e}")
                    return jsonify({"error": "Failed to convert to MP3"}), 500
        
        # Generate download filename
        kind = asset.get('kind', 'file')
        ext = asset_path.split('.')[-1]
        download_name = f"{kind}_{asset_id}.{ext}"
        
        return export_file(asset_path, download_name=download_name)
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return abort(500)

@bp.route("/api/library", methods=["GET"])
def api_library():
    """Get user's studio library assets"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        kind = request.args.get('kind')  # Optional filter by asset type
        
        assets = studio_library.get_user_assets(user_id, kind=kind)
        
        # Convert paths to relative for security
        safe_assets = {}
        for asset_id, asset_data in assets.items():
            safe_asset = asset_data.copy()
            # Keep filename for display and path for selectors
            safe_asset['filename'] = asset_data['path'].split('/')[-1]
            safe_asset['path'] = asset_data['path']  # Keep path for file selectors
            safe_asset.pop('original_path', None)  # Remove original path
            safe_assets[asset_id] = safe_asset
        
        return jsonify({
            "success": True,
            "assets": safe_assets,
            "count": len(safe_assets)
        })
        
    except Exception as e:
        logger.error(f"Library API error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@bp.route("/api/library/<asset_id>", methods=["DELETE"])
def api_delete_asset(asset_id):
    """Delete an asset from the library"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        
        if studio_library.delete_asset(user_id, asset_id):
            return jsonify({
                "success": True,
                "message": "Asset deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Asset not found"
            }), 404
        
    except Exception as e:
        logger.error(f"Delete asset error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500