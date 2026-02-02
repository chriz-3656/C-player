import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path.home() / ".config" / "cplayer" / "history.json"
MAX_HISTORY_SIZE = 100

def ensure_config_dir():
    """Ensure the config directory exists"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

def add_to_history(track):
    """Add a track to playback history"""
    try:
        ensure_config_dir()
        
        # Load existing history
        history = load_history()
        
        # Add new entry with timestamp
        entry = {
            'track': track,
            'played_at': datetime.now().isoformat()
        }
        
        # Add to beginning of list
        history.insert(0, entry)
        
        # Limit history size
        history = history[:MAX_HISTORY_SIZE]
        
        # Save back to file
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
    except Exception:
        return False

def load_history():
    """Load playback history"""
    try:
        if not HISTORY_FILE.exists():
            return []
        
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        
        return history
    except Exception:
        return []

def clear_history():
    """Clear all playback history"""
    try:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        return True
    except Exception:
        return False

def get_recent_tracks(limit=20):
    """Get recent tracks from history"""
    history = load_history()
    return [entry['track'] for entry in history[:limit]]
