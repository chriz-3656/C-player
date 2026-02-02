import json
import os
from pathlib import Path

PLAYLISTS_DIR = Path.home() / ".config" / "cplayer" / "playlists"

def ensure_playlists_dir():
    """Ensure the playlists directory exists"""
    PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)

def save_playlist(name, tracks):
    """Save a playlist to disk"""
    try:
        ensure_playlists_dir()
        playlist_path = PLAYLISTS_DIR / f"{name}.json"
        
        with open(playlist_path, 'w') as f:
            json.dump({
                'name': name,
                'tracks': tracks
            }, f, indent=2)
        
        return True
    except Exception:
        return False

def load_playlist(name):
    """Load a playlist from disk"""
    try:
        playlist_path = PLAYLISTS_DIR / f"{name}.json"
        
        if not playlist_path.exists():
            return None
        
        with open(playlist_path, 'r') as f:
            data = json.load(f)
        
        return data.get('tracks', [])
    except Exception:
        return None

def list_playlists():
    """List all saved playlists"""
    try:
        ensure_playlists_dir()
        playlists = []
        
        for file in PLAYLISTS_DIR.glob("*.json"):
            playlists.append(file.stem)
        
        return sorted(playlists)
    except Exception:
        return []

def delete_playlist(name):
    """Delete a playlist"""
    try:
        playlist_path = PLAYLISTS_DIR / f"{name}.json"
        
        if playlist_path.exists():
            playlist_path.unlink()
            return True
        
        return False
    except Exception:
        return False
