from ytmusicapi import YTMusic
import re

ytmusic = YTMusic()

def search_tracks(query):
    try:
        results = ytmusic.search(query, filter="songs")
        tracks = []
        for r in results[:20]:
            tracks.append({
                "title": r["title"],
                "artist": r["artists"][0]["name"],
                "videoId": r["videoId"],
                "thumbnail": r.get("thumbnails", [{}])[-1].get("url", "")
            })
        return tracks
    except Exception:
        return []

def get_random_songs():
    """Get random songs from YouTube Music charts or trending"""
    try:
        # Try to get songs from charts (this gives trending/popular songs)
        charts = ytmusic.get_charts()
        
        # Extract songs from the charts
        tracks = []
        if charts and 'countries' in charts:
            country_chart = charts['countries']['results'][0]  # Get first country's chart
            if 'chart' in country_chart:
                for item in country_chart['chart'][:20]:  # Get top 20
                    if item.get('type') == 'SONG' or 'videoId' in item:
                        tracks.append({
                            "title": item.get("title", "Unknown"),
                            "artist": item.get("artists", [{"name": "Unknown"}])[0]["name"],
                            "videoId": item.get("videoId", ""),
                            "thumbnail": item.get("thumbnails", [{}])[-1].get("url", "")
                        })
        
        # Fallback: search for popular music if charts didn't work
        if not tracks:
            tracks = search_tracks("top hits 2026")
        
        return tracks[:20]
    except Exception:
        # Ultimate fallback: search for generic popular music
        try:
            return search_tracks("popular music")
        except:
            return []

def get_playlist_songs(playlist_url_or_id):
    """Get songs from a YouTube Music playlist URL or ID"""
    try:
        # Extract playlist ID from URL if needed
        playlist_id = playlist_url_or_id
        
        # Match various YouTube playlist URL formats
        url_patterns = [
            r'list=([a-zA-Z0-9_-]+)',  # Standard parameter
            r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)',
            r'music\.youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, playlist_url_or_id)
            if match:
                playlist_id = match.group(1)
                break
        
        # Fetch playlist details
        playlist = ytmusic.get_playlist(playlist_id, limit=100)
        
        tracks = []
        for item in playlist.get('tracks', []):
            if item.get('videoId'):
                tracks.append({
                    "title": item.get("title", "Unknown"),
                    "artist": item.get("artists", [{"name": "Unknown"}])[0].get("name", "Unknown"),
                    "videoId": item.get("videoId", ""),
                    "thumbnail": item.get("thumbnails", [{}])[-1].get("url", "")
                })
        
        return tracks
    except Exception as e:
        return []
