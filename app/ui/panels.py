from textual.widgets import Static, ProgressBar, Label
from textual.containers import Vertical

def format_time(seconds):
    """Format seconds into MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

class MetadataPanel(Static):
    def compose(self):
        with Vertical():
            yield Label("", id="track_info")
            yield Label("00:00 / 00:00", id="time_label")
            yield ProgressBar(id="progress")
    
    def on_mount(self):
        track_info = self.query_one("#track_info", Label)
        track_info.update(
            "[b #818cf8]♪ Now Playing[/b #818cf8]\n\n"
            "[dim]No track selected[/dim]"
        )
    
    def update_track(self, track):
        video_id = track.get('videoId', 'N/A')
        album = track.get('album', 'Unknown Album')
        duration = track.get('duration', 'N/A')
        
        track_info = self.query_one("#track_info", Label)
        track_info.update(
            f"[b #818cf8]♪ Now Playing[/b #818cf8]\n\n"
            f"[b]Title[/b]  : {track['title']}\n"
            f"[b]Artist[/b] : {track['artist']}\n"
            f"[b]Album[/b]  : {album}\n"
            f"[dim]ID: {video_id}[/dim]"
        )


