# ===================================
# 📁 FILE: backend/studio/library.py
# ===================================
import os
import json
from datetime import datetime
from .utils import new_id

class StudioLibrary:
    def __init__(self):
        try:
            from config import PATHS
            self.library_dir = os.path.join(PATHS["audio"], "library")
        except ImportError:
            self.library_dir = "storage/audio/library"
        
        os.makedirs(self.library_dir, exist_ok=True)
        self.metadata_file = os.path.join(self.library_dir, "metadata.json")
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """Load library metadata from JSON file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save library metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def save_asset(self, user_id, kind, path, meta=None):
        """
        Save an asset to the user's library
        kind: 'vocal', 'instrumental', 'mixed', 'cover_art', 'midi'
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Asset file not found: {path}")
        
        asset_id = new_id()
        user_library_dir = os.path.join(self.library_dir, str(user_id))
        os.makedirs(user_library_dir, exist_ok=True)
        
        # Get file extension
        _, ext = os.path.splitext(path)
        new_filename = f"{asset_id}_{kind}{ext}"
        new_path = os.path.join(user_library_dir, new_filename)
        
        # Copy file to library
        import shutil
        shutil.copy2(path, new_path)
        
        # Save metadata
        if str(user_id) not in self.metadata:
            self.metadata[str(user_id)] = {}
        
        self.metadata[str(user_id)][asset_id] = {
            "id": asset_id,
            "kind": kind,
            "path": new_path,
            "original_path": path,
            "created_at": datetime.now().isoformat(),
            "meta": meta or {}
        }
        
        self._save_metadata()
        return asset_id
    
    def get_user_assets(self, user_id, kind=None):
        """Get all assets for a user, optionally filtered by kind"""
        user_assets = self.metadata.get(str(user_id), {})
        if kind:
            return {k: v for k, v in user_assets.items() if v.get('kind') == kind}
        return user_assets
    
    def get_asset(self, user_id, asset_id):
        """Get a specific asset"""
        return self.metadata.get(str(user_id), {}).get(asset_id)
    
    def delete_asset(self, user_id, asset_id):
        """Delete an asset from the library"""
        asset = self.get_asset(user_id, asset_id)
        if asset:
            # Delete file
            if os.path.exists(asset['path']):
                os.remove(asset['path'])
            
            # Remove from metadata
            del self.metadata[str(user_id)][asset_id]
            self._save_metadata()
            return True
        return False

# Global library instance
studio_library = StudioLibrary()