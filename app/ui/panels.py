from textual.widgets import Static, ProgressBar

class MetadataPanel(Static):
    def compose(self):
        yield ProgressBar(id="progress")
    
    def on_mount(self):
        self.update(
            "[b #818cf8]♪ Now Playing[/b #818cf8]\n\n"
            "[dim]No track selected[/dim]"
        )
    
    def update_track(self, track):
        video_id = track.get('videoId', 'N/A')
        album = track.get('album', 'Unknown Album')
        duration = track.get('duration', 'N/A')
        
        self.update(
            f"[b #818cf8]♪ Now Playing[/b #818cf8]\n\n"
            f"[b]Title[/b]  : {track['title']}\n"
            f"[b]Artist[/b] : {track['artist']}\n"
            f"[b]Album[/b]  : {album}\n"
            f"[dim]ID: {video_id}[/dim]"
        )


