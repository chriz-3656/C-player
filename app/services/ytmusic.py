from ytmusicapi import YTMusic
ytmusic = YTMusic()

def search_tracks(query):
    try:
        results = ytmusic.search(query, filter="songs")
        tracks = []
        for r in results[:20]:
            tracks.append({
                "title": r["title"],
                "artist": r["artists"][0]["name"],
                "videoId": r["videoId"]
            })
        return tracks
    except Exception:
        return []
