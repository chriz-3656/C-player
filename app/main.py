from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, ListView, ListItem, Label, ProgressBar
from textual.containers import Horizontal, Vertical
from textual import events

from app.ui.banner import Banner
from app.ui.visualizer import Visualizer
from app.ui.panels import MetadataPanel, format_time
from app.controller.player import Player
from app.controller.queue import Queue
from app.services.ytmusic import search_tracks, get_random_songs, get_playlist_songs, get_watch_song
from app.services.playlist_manager import save_playlist, load_playlist, list_playlists
from app.services.history_manager import add_to_history, get_recent_tracks


class CPlayer(App):
    CSS = """
    Screen { 
        background: #0d0d0d; 
        color: #e0e0e0; 
    }
    
    Input { 
        border: solid #6366f1; 
        margin: 0 1 1 1;
        padding: 0 1;
        height: 3;
        background: #1a1a2e;
        color: #ffffff;
    }
    
    Input:focus {
        border: solid #818cf8;
    }
    
    ListView { 
        border: solid #6366f1; 
        padding: 1;
        height: 1fr;
        background: #16162a;
    }
    
    ListView:focus {
        border: solid #818cf8;
    }
    
    ListItem:hover {
        background: #1e1e3f;
    }
    
    ListItem.--playing {
        background: #2d2d5f;
        color: #fbbf24;
    }
    
    ListItem.--playing:hover {
        background: #3a3a7f;
    }
    
    .main-container {
        height: 1fr;
    }
    
    .side-panels {
        width: 35;
        min-width: 30;
    }
    
    #banner-logo {
        width: 3fr;
        padding: 0 1 0 0;
        text-align: left;
    }
    
    #banner-controls {
        width: 2fr;
        padding: 1 1;
        text-align: center;
    }
    
    #banner-info {
        width: 2fr;
        text-align: right;
        padding: 1 0 1 1;
    }
    
    .spacer { 
        width: 1;
        height: 0;
    }
    
    MetadataPanel {
        border: solid #6366f1;
        padding: 1;
        height: auto;
        min-height: 16;
        background: #1a1a2e;
    }
    
    MetadataPanel Vertical {
        height: auto;
    }
    
    MetadataPanel #track_info {
        height: auto;
        margin: 0 0 1 0;
    }
    
    MetadataPanel #time_label {
        text-align: center;
        color: #818cf8;
        margin: 0 0 1 0;
        height: 1;
    }
    
    MetadataPanel #progress {
        height: 1;
    }
    
    #status-display {
        text-align: center;
        color: #6366f1;
        margin: 1 0 0 0;
        height: 1;
        min-height: 1;
    }
    
    #volume-display {
        text-align: center;
        color: #fbbf24;
        margin: 0 0 1 0;
        height: 1;
        min-height: 1;
    }
    
    Visualizer {
        border: solid #6366f1;
        padding: 1;
        width: 30;
        min-width: 26;
        height: 1fr;
        background: #1a1a2e;
    }
    
    #visualizer-container {
        width: 30;
        min-width: 26;
        height: 100%;
    }
    
    #status-panel {
        background: #1a1a2e;
        border: solid #6366f1;
        border-top: none;
        padding: 1;
        height: 3;
        min-height: 3;
    }
    
    #status-container {
        height: 100%;
        width: 100%;
    }
    
    #status-main {
        text-align: left;
        color: #818cf8;
        height: 1;
    }
    
    #status-secondary {
        text-align: right;
        color: #fbbf24;
        height: 1;
        margin-top: 1;
    }
    
    #status-icon {
        color: #6366f1;
        margin-right: 1;
    }
    
    #volume-icon {
        color: #fbbf24;
        margin-left: 1;
    }
    
    ProgressBar > .bar--indeterminate {
        color: #6366f1;
    }
    
    ProgressBar > .bar--bar {
        color: #818cf8;
    }
    
    ProgressBar > .bar--complete {
        color: #6366f1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Banner()
        yield Input(placeholder="Search YouTube Music… (Commands: :save <name>, :load <name>, :playlists, :history)")

        with Horizontal(classes="main-container"):
            yield ListView(id="results")
            yield Vertical(classes="spacer")

            with Vertical(classes="side-panels"):
                self.meta = MetadataPanel(id="metadata_panel")
                yield self.meta

            yield Vertical(classes="spacer")
            
            with Vertical(id="visualizer-container"):
                self.visualizer = Visualizer()
                yield self.visualizer

        yield Footer()

    def on_mount(self):
        self.player = Player(self.on_track_end)
        self.queue = Queue(self.player)
        self.visualizer.attach_player(self.player)
        self.set_interval(0.3, self.update_progress)
        self.volume_display_timer = None
        self.search_history = []
        self.history_index = -1
        self.current_icon = "○"  # Default icon
        
        # Initialize integrated status display
        self.update_status("Ready")
        self.update_volume_display(100)
        
        # Load random songs on startup
        self.load_random_songs()
    
    def update_status(self, main_message, secondary_message="", icon=None):
        """Update the integrated status display in metadata panel"""
        if icon:
            self.current_icon = icon
        
        status_display = self.query_one("#metadata_panel").query_one("#status-display", Label)
        
        # Add icon to main message
        main_with_icon = f"{self.current_icon} {main_message}"
        status_display.update(f"[dim]Status: {main_with_icon}[/dim]")
    
    def update_volume_display(self, volume):
        """Update volume display in metadata panel"""
        volume_display = self.query_one("#metadata_panel").query_one("#volume-display", Label)
        volume_display.update(f"[dim]Volume: {volume}%[/dim]")
    
    def show_volume_temporarily(self):
        """Show volume indicator temporarily in metadata panel"""
        if self.volume_display_timer:
            self.volume_display_timer.cancel()
        self.volume_display_timer = self.set_timer(2.0, lambda: self.update_volume_display(self.player.volume))
    
    def load_random_songs(self):
        """Load random/trending songs into the list on startup"""
        lv = self.query_one("#results", ListView)
        
        self.update_status("Loading trending songs...", "Please wait...")
        
        tracks = get_random_songs()
        if tracks:
            self.queue.load(tracks)
            for t in tracks:
                item = ListItem(Label(f"{t['title']} — {t['artist']}"))
                item.track = t
                lv.append(item)
            self.update_status(f"Ready - {len(tracks)} songs", f"Volume: {self.player.volume}%")
        else:
            self.update_status("Ready", "Failed to load trending songs")

    def on_unmount(self):
        self.player.stop()

    async def on_input_submitted(self, event):
        lv = self.query_one("#results", ListView)
        lv.clear()
        
        input_value = event.value.strip()
        
        # Check for special commands
        if input_value.startswith(":save "):
            # Save current queue as playlist
            playlist_name = input_value[6:].strip()
            if playlist_name and self.queue.tracks:
                if save_playlist(playlist_name, self.queue.tracks):
                    self.update_status(f"Playlist '{playlist_name}' saved", f"Volume: {self.player.volume}%")
                else:
                    self.update_status("Error", "Failed to save playlist")
            else:
                self.update_status("Error", "Invalid playlist name or empty queue")
            return
        
        elif input_value.startswith(":load "):
            # Load a saved playlist
            playlist_name = input_value[6:].strip()
            tracks = load_playlist(playlist_name)
            if tracks:
                self.queue.load(tracks)
                for t in tracks:
                    item = ListItem(Label(f"{t['title']} — {t['artist']}"))
                    item.track = t
                    lv.append(item)
                self.update_status(f"Loaded '{playlist_name}'", f"{len(tracks)} songs")
            else:
                self.update_status("Error", f"Playlist '{playlist_name}' not found")
            return
        
        elif input_value == ":playlists":
            # Show available playlists
            playlists = list_playlists()
            if playlists:
                self.update_status("Playlists", f"{', '.join(playlists)}")
            else:
                self.update_status("Playlists", "No saved playlists")
            return
        
        elif input_value == ":history":
            # Load playback history
            tracks = get_recent_tracks(20)
            if tracks:
                self.queue.load(tracks)
                for t in tracks:
                    item = ListItem(Label(f"{t['title']} — {t['artist']}"))
                    item.track = t
                    lv.append(item)
                self.update_status("History loaded", f"{len(tracks)} tracks")
            else:
                self.update_status("History", "No playback history")
            return
        
        # Add to search history
        if input_value and (not self.search_history or self.search_history[-1] != input_value):
            self.search_history.append(input_value)
        self.history_index = len(self.search_history)
        
        # Check if input is a playlist URL
        if "list=" in input_value or "playlist" in input_value:
            self.update_status("Loading playlist...", "Please wait...")
            tracks = get_playlist_songs(input_value)
            if not tracks:
                # Provide more specific error messages
                if "RDCLAK" in input_value or "mix" in input_value.lower():
                    self.update_status("Error", "Mix playlists not supported")
                elif len(input_value) < 10:
                    self.update_status("Error", "Invalid playlist ID")
                else:
                    self.update_status("Error", "Failed to load playlist")
                return
            self.update_status(f"Loaded {len(tracks)} songs", f"Volume: {self.player.volume}%")
        
        # Check if input is a watch URL (individual video)
        elif "watch?v=" in input_value or "youtu.be/" in input_value:
            self.update_status("Loading video...", "Please wait...")
            song = get_watch_song(input_value)
            if not song:
                self.update_status("Error", "Failed to load video")
                return
            
            # Create a single-item queue with this song
            tracks = [song]
            self.queue.load(tracks)
            
            # Clear and populate the list view
            lv = self.query_one("#results", ListView)
            lv.clear()
            item = ListItem(Label(f"{song['title']} — {song['artist']}"))
            item.track = song
            lv.append(item)
            
            self.update_status(f"Loaded: {song['title']}", f"Volume: {self.player.volume}%")
        else:
            # Regular search
            self.update_status("Searching...", "Please wait...")
            tracks = search_tracks(input_value)
            if not tracks:
                self.update_status("Search", "No results found")
                return
            self.update_status("Ready", f"Found {len(tracks)} tracks")

        self.queue.load(tracks)

        for t in tracks:
            item = ListItem(Label(f"{t['title']} — {t['artist']}"))
            item.track = t
            lv.append(item)

    async def on_list_view_selected(self, event):
        track = event.item.track
        success = self.queue.play_single(track)
        if success:
            self.meta.update_track(track)
            self.update_status("▶ Playing", track['title'][:30] + "..." if len(track['title']) > 30 else track['title'])
            self.highlight_current_track()
            add_to_history(track)  # Add to playback history
        else:
            self.update_status("Error", "Failed to load track")
    
    def highlight_current_track(self):
        """Highlight the currently playing track in the list"""
        lv = self.query_one("#results", ListView)
        
        # Remove highlight from all items
        for item in lv.children:
            item.remove_class("--playing")
        
        # Add highlight to current track
        if self.queue.current_track:
            for item in lv.children:
                if hasattr(item, 'track') and item.track.get('videoId') == self.queue.current_track.get('videoId'):
                    item.add_class("--playing")
                    break

    def update_progress(self):
        pb = self.query_one("#progress", ProgressBar)
        pb.total = int(self.player.duration)
        pb.progress = int(self.player.time_pos)
        
        # Update time label
        time_label = self.query_one("#time_label", Label)
        current_time = format_time(self.player.time_pos)
        total_time = format_time(self.player.duration)
        time_label.update(f"{current_time} / {total_time}")

    def on_track_end(self):
        # Try to play the next song automatically
        if self.queue.tracks and self.queue.index < len(self.queue.tracks) - 1:
            success = self.queue.next()
            if success:
                track = self.queue.tracks[self.queue.index]
                self.meta.update_track(track)
                self.update_status("▶ Playing", track['title'][:30] + "..." if len(track['title']) > 30 else track['title'])
                self.highlight_current_track()
                add_to_history(track)  # Add to playback history
            else:
                self.update_status("Error", "Failed to load next track")
        else:
            self.update_status("Queue Ended", "No more tracks")

    async def on_key(self, event: events.Key):
        # Handle search history navigation
        search_input = self.query_one(Input)
        if search_input.has_focus:
            if event.key == "up":
                if self.search_history and self.history_index > 0:
                    self.history_index -= 1
                    search_input.value = self.search_history[self.history_index]
                    search_input.cursor_position = len(search_input.value)
                    event.prevent_default()
                return
            elif event.key == "down":
                if self.search_history and self.history_index < len(self.search_history) - 1:
                    self.history_index += 1
                    search_input.value = self.search_history[self.history_index]
                    search_input.cursor_position = len(search_input.value)
                    event.prevent_default()
                elif self.history_index >= len(self.search_history) - 1:
                    self.history_index = len(self.search_history)
                    search_input.value = ""
                    event.prevent_default()
                return
        
        # Regular key handlers
        if event.key == "space":
            self.player.toggle_pause()
        elif event.key == "n":
            success = self.queue.next()
            if success:
                track = self.queue.tracks[self.queue.index]
                self.meta.update_track(track)
                self.update_status("▶ Playing", track['title'][:30] + "..." if len(track['title']) > 30 else track['title'])
                self.highlight_current_track()
                add_to_history(track)  # Add to playback history
            else:
                self.update_status("Error", "No next track")
        elif event.key == "p":
            success = self.queue.previous()
            if success:
                track = self.queue.tracks[self.queue.index]
                self.meta.update_track(track)
                self.update_status("▶ Playing", track['title'][:30] + "..." if len(track['title']) > 30 else track['title'])
                self.highlight_current_track()
                add_to_history(track)  # Add to playback history
            else:
                self.update_status("Error", "No previous track")
        elif event.key in ("+", "="):
            self.player.volume_up()
            self.update_volume_display(self.player.volume)
        elif event.key == "-":
            self.player.volume_down()
            self.update_volume_display(self.player.volume)
        elif event.key == "ctrl+q":
            self.player.stop()
            await self.action_quit()
    
    def show_volume(self):
        """Display volume indicator temporarily"""
        volume_label = self.query_one("#volume_display", Label)
        volume_label.update(f"🔊 Volume: {self.player.volume}%")
        
        # Cancel previous timer if exists
        if self.volume_display_timer:
            self.volume_display_timer.cancel()
        
        # Hide volume display after 2 seconds
        self.volume_display_timer = self.set_timer(2.0, lambda: volume_label.update(""))


if __name__ == "__main__":
    CPlayer().run()
