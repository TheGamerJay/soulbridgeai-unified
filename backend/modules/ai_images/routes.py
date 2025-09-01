"""
SoulBridge AI - AI Image Generation Routes  
All AI image generation endpoints extracted from backend/app.py
Flask Blueprint for modular architecture
"""
import logging
from flask import Blueprint, request, jsonify, session, redirect, render_template
from datetime import datetime
from .ai_image_service import AIImageService
from .gallery_manager import GalleryManager

logger = logging.getLogger(__name__)

# Create Blueprint
ai_images_bp = Blueprint('ai_images', __name__, url_prefix='/ai-image-generation')

# Initialize services (to be configured in main app)
ai_image_service = None
gallery_manager = None

def init_ai_images_routes(app, openai_client, credits_manager, database):
    """Initialize AI images routes with dependencies"""
    global ai_image_service, gallery_manager
    
    ai_image_service = AIImageService(openai_client, credits_manager)
    gallery_manager = GalleryManager(database)
    
    # Blueprint already registered in main app - just initialize services
    logger.info("✅ AI Images routes initialized")

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session and session.get('user_id') is not None

# ================================
# MAIN AI IMAGE GENERATION PAGES
# ================================

@ai_images_bp.route("/")
def ai_image_generation_page():
    """AI image generation main page"""
    if not is_logged_in():
        return redirect("/login")
    
    # Check if user has ai-image-generation access (Silver/Gold tier, addon, or trial)
    user_plan = session.get('user_plan', 'bronze')
    user_addons = session.get('user_addons', [])
    trial_active = session.get('trial_active', False)
    
    if user_plan not in ['silver', 'gold'] and not trial_active and 'ai-image-generation' not in user_addons:
        return redirect("/subscription?feature=ai-image-generation")
    
    return render_template("ai_image_generation.html")

@ai_images_bp.route("/silver")
def ai_image_generation_silver():
    """AI image generation Silver tier page"""
    if not is_logged_in():
        return redirect("/login")
    
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    
    # Check Silver tier access
    if user_plan not in ['silver', 'gold'] and not trial_active:
        return redirect("/subscription?feature=ai-image-generation")
    
    return render_template("ai_image_generation.html", tier="silver")

@ai_images_bp.route("/gold")  
def ai_image_generation_gold():
    """AI image generation Gold tier page"""
    if not is_logged_in():
        return redirect("/login")
    
    user_plan = session.get('user_plan', 'bronze')
    trial_active = session.get('trial_active', False)
    
    # Check Gold tier access (trial users can access, but real Gold users get unlimited)
    if user_plan not in ['gold'] and not trial_active:
        return redirect("/subscription?feature=ai-image-generation")
    
    return render_template("ai_image_generation.html", tier="gold")

# ================================
# API ENDPOINTS
# ================================

@ai_images_bp.route("/api/generate", methods=["POST"])
def generate_image():
    """Generate AI image from prompt"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not ai_image_service:
            return jsonify({"success": False, "error": "AI Image service not available"}), 503
        
        # Check access and limits
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        access_check = ai_image_service.check_access_and_limits(
            user_id, user_plan, trial_active, user_addons
        )
        
        if not access_check['has_access']:
            return jsonify({"success": False, "error": access_check['error']}), 403
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Validate prompt
        prompt = data.get('prompt', '').strip()
        validation = ai_image_service.validate_prompt(prompt)
        if not validation['valid']:
            return jsonify({"success": False, "error": validation['error']}), 400
        
        # Extract parameters
        style = data.get('style', 'photorealistic')
        size = data.get('size', '1024x1024')
        quality = data.get('quality', 'standard')
        
        # Generate image
        result = ai_image_service.generate_image(
            user_id, validation['cleaned_prompt'], style, size, quality
        )
        
        if result['success']:
            # Update session usage tracking
            current_month = datetime.now().strftime('%Y-%m')
            usage_key = f'ai_image_usage_{current_month}'
            session[usage_key] = session.get(usage_key, 0) + 1
            
            logger.info(f"✅ Generated AI image for user {user_id}")
            
            return jsonify({
                "success": True,
                "imageUrl": result['image_url'],
                "originalPrompt": result['original_prompt'],
                "enhancedPrompt": result['enhanced_prompt'],
                "revisedPrompt": result.get('revised_prompt', ''),
                "style": result['style'],
                "size": result['size'],
                "generationTime": result['generation_time']
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"AI image generation error: {e}")
        return jsonify({"success": False, "error": "Failed to generate image"}), 500

@ai_images_bp.route("/api/analyze-reference", methods=["POST"])
def analyze_reference_image():
    """Analyze reference image using GPT-4 Vision to create detailed description"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not ai_image_service:
            return jsonify({"success": False, "error": "AI Image service not available"}), 503
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Silver/Gold tier, addon, or trial"}), 403
        
        data = request.get_json()
        if not data or 'imageData' not in data:
            return jsonify({"success": False, "error": "No image data provided"}), 400
        
        # Analyze image
        user_id = session.get('user_id')
        result = ai_image_service.analyze_reference_image(data['imageData'], user_id)
        
        if result['success']:
            return jsonify({
                "success": True,
                "description": result['description'],
                "analysisTime": result['analysis_time']
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Reference image analysis error: {e}")
        return jsonify({"success": False, "error": "Failed to analyze reference image"}), 500

@ai_images_bp.route("/api/save", methods=["POST"])
def save_image_to_gallery():
    """Save generated image to gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not gallery_manager:
            return jsonify({"success": False, "error": "Gallery service not available"}), 503
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Silver/Gold tier, addon, or trial"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = session.get('user_id')
        
        # For session-based storage (current implementation)
        if 'ai_image_gallery' not in session:
            session['ai_image_gallery'] = []
        
        # Create image record for session storage
        image_record = {
            "id": len(session['ai_image_gallery']) + 1,
            "imageUrl": data.get('imageUrl'),
            "prompt": data.get('prompt'),
            "style": data.get('style'),
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        session['ai_image_gallery'].append(image_record)
        
        logger.info(f"🖼️ AI image saved to gallery for user {session.get('user_email')}")
        
        return jsonify({
            "success": True,
            "imageId": image_record['id'],
            "message": "Image saved to gallery successfully"
        })
        
    except Exception as e:
        logger.error(f"AI image save error: {e}")
        return jsonify({"success": False, "error": "Failed to save image"}), 500

@ai_images_bp.route("/api/gallery", methods=["GET"])
def get_image_gallery():
    """Get user's AI image gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'ai-image-generation' not in user_addons:
            return jsonify({"success": False, "error": "AI Image Generation requires Silver/Gold tier, addon, or trial"}), 403
        
        # Get images from session (in production, should use database)
        images = session.get('ai_image_gallery', [])
        
        # Sort by timestamp, most recent first
        images.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            "success": True,
            "images": images,
            "count": len(images)
        })
        
    except Exception as e:
        logger.error(f"AI image gallery error: {e}")
        return jsonify({"success": False, "error": "Failed to get gallery"}), 500

@ai_images_bp.route("/api/usage", methods=["GET"])
def get_usage_statistics():
    """Get user's monthly usage statistics"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not ai_image_service:
            return jsonify({"success": False, "error": "AI Image service not available"}), 503
        
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        requested_tier = request.args.get('tier')
        
        # Get usage stats
        stats = ai_image_service.get_usage_stats(user_id, user_plan, trial_active, requested_tier)
        
        if stats['success']:
            # Add session-based usage tracking
            current_month = datetime.now().strftime('%Y-%m')
            usage_key = f'ai_image_usage_{current_month}'
            monthly_usage = session.get(usage_key, 0)
            
            # Override monthly usage from session
            stats['monthly_usage'] = monthly_usage
            stats['remaining'] = max(0, stats['monthly_limit'] - monthly_usage) if stats['monthly_limit'] < 999999 else 999
            
            return jsonify(stats)
        else:
            return jsonify(stats), 500
            
    except Exception as e:
        logger.error(f"Usage statistics error: {e}")
        return jsonify({"success": False, "error": "Failed to get usage statistics"}), 500

# ================================
# GALLERY MANAGEMENT ENDPOINTS  
# ================================

@ai_images_bp.route("/api/gallery/<image_id>/favorite", methods=["POST"])
def toggle_image_favorite(image_id):
    """Toggle favorite status for an image"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not gallery_manager:
            return jsonify({"success": False, "error": "Gallery service not available"}), 503
        
        user_id = session.get('user_id')
        result = gallery_manager.toggle_favorite(user_id, image_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Toggle favorite error: {e}")
        return jsonify({"success": False, "error": "Failed to toggle favorite"}), 500

@ai_images_bp.route("/api/gallery/<image_id>", methods=["DELETE"])
def delete_image_from_gallery(image_id):
    """Delete image from gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not gallery_manager:
            return jsonify({"success": False, "error": "Gallery service not available"}), 503
        
        user_id = session.get('user_id')
        result = gallery_manager.delete_image(user_id, image_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Delete image error: {e}")
        return jsonify({"success": False, "error": "Failed to delete image"}), 500

@ai_images_bp.route("/api/gallery/search", methods=["GET"])
def search_image_gallery():
    """Search user's image gallery"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not gallery_manager:
            return jsonify({"success": False, "error": "Gallery service not available"}), 503
        
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({"success": False, "error": "Search query required"}), 400
        
        user_id = session.get('user_id')
        result = gallery_manager.search_gallery(user_id, query)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Gallery search error: {e}")
        return jsonify({"success": False, "error": "Failed to search gallery"}), 500

# ================================
# UTILITY ENDPOINTS
# ================================

@ai_images_bp.route("/api/validate-prompt", methods=["POST"])
def validate_generation_prompt():
    """Validate image generation prompt"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not ai_image_service:
            return jsonify({"success": False, "error": "AI Image service not available"}), 503
        
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"success": False, "error": "Prompt required"}), 400
        
        result = ai_image_service.validate_prompt(data['prompt'])
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Prompt validation error: {e}")
        return jsonify({"success": False, "error": "Failed to validate prompt"}), 500

@ai_images_bp.route("/api/styles", methods=["GET"])
def get_available_styles():
    """Get available image generation styles"""
    try:
        if not ai_image_service:
            styles = ["photorealistic", "artistic", "cartoon", "abstract", "vintage", "modern", "minimalist", "detailed"]
        else:
            styles = ai_image_service.supported_styles
        
        return jsonify({
            "success": True,
            "styles": styles
        })
        
    except Exception as e:
        logger.error(f"Get styles error: {e}")
        return jsonify({"success": False, "error": "Failed to get styles"}), 500

@ai_images_bp.route("/api/sizes", methods=["GET"])  
def get_available_sizes():
    """Get available image sizes"""
    try:
        if not ai_image_service:
            sizes = ["1024x1024", "1792x1024", "1024x1792"]
        else:
            sizes = ai_image_service.supported_sizes
        
        return jsonify({
            "success": True,
            "sizes": sizes
        })
        
    except Exception as e:
        logger.error(f"Get sizes error: {e}")
        return jsonify({"success": False, "error": "Failed to get sizes"}), 500