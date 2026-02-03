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

def get_watch_song(watch_url):
    """Get song info from a YouTube Music watch URL"""
    try:
        # Extract video ID from watch URL
        video_id = None
        watch_patterns = [
            r'v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in watch_patterns:
            match = re.search(pattern, watch_url)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            return None
            
        # Get video details
        watch_result = ytmusic.get_song(video_id)
        
        if watch_result and 'videoDetails' in watch_result:
            details = watch_result['videoDetails']
            return {
                'title': details.get('title', 'Unknown'),
                'artist': details.get('author', 'Unknown'),
                'videoId': video_id,
                'thumbnail': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            }
        
        return None
    except Exception as e:
        print(f"Watch URL error: {e}")
        return None

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
        
        # Try different limit values to handle various playlist sizes
        limits_to_try = [100, 200, 50, 300]
        playlist = None
        
        for limit in limits_to_try:
            try:
                playlist = ytmusic.get_playlist(playlist_id, limit=limit)
                if playlist and playlist.get('tracks'):
                    # Check if we got meaningful data
                    valid_tracks = [t for t in playlist['tracks'] if t.get('videoId')]
                    if len(valid_tracks) > 0:
                        break
            except Exception:
                continue
        
        # If we still don't have playlist data, try alternative approach
        if not playlist or not playlist.get('tracks'):
            # Try with authenticated session (if available)
            try:
                auth_ytmusic = YTMusic()  # Try default auth
                playlist = auth_ytmusic.get_playlist(playlist_id, limit=100)
            except Exception:
                pass
        
        if not playlist:
            return []
        
        tracks = []
        for item in playlist.get('tracks', []):
            # More robust checking for playable tracks
            video_id = item.get('videoId')
            if video_id and video_id != 'None' and video_id.strip():
                # Additional validation
                is_available = item.get('isAvailable', True)
                if is_available or is_available is None:  # None often means available
                    tracks.append({
                        "title": item.get("title", "Unknown"),
                        "artist": item.get("artists", [{"name": "Unknown"}])[0].get("name", "Unknown"),
                        "videoId": video_id,
                        "thumbnail": item.get("thumbnails", [{}])[-1].get("url", "")
                    })
        
        return tracks
    except Exception as e:
        # Log the error for debugging (you might want to remove this in production)
        print(f"Playlist fetching error: {e}")
        return []
