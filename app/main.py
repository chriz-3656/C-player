from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, ListView, ListItem, Label, ProgressBar
from textual.containers import Horizontal, Vertical
from textual import events

from app.ui.banner import Banner
from app.ui.visualizer import Visualizer
from app.ui.panels import MetadataPanel, format_time
from app.controller.player import Player
from app.controller.queue import Queue
from app.services.ytmusic import search_tracks, get_random_songs, get_playlist_songs
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
        width: 2fr;
    }
    
    #banner-controls {
        width: 2fr;
        padding: 1;
        text-align: center;
    }
    
    #banner-info {
        width: 1fr;
        text-align: right;
        padding: 1;
    }
    
    .spacer { 
        width: 1;
        height: 0;
    }
    
    MetadataPanel {
        border: solid #6366f1;
        padding: 1;
        height: auto;
        min-height: 12;
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
    
    #status {
        text-align: left;
        background: #1a1a2e;
        color: #818cf8;
        padding: 0 1;
        height: auto;
        min-height: 1;
        border: solid #6366f1;
        border-top: none;
    }
    
    #volume_display {
        text-align: right;
        background: #1a1a2e;
        color: #fbbf24;
        padding: 0 1;
        height: auto;
        min-height: 1;
        border: solid #6366f1;
        border-top: none;
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
                self.meta = MetadataPanel()
                yield self.meta

            yield Vertical(classes="spacer")
            
            with Vertical(id="visualizer-container"):
                self.visualizer = Visualizer()
                yield self.visualizer
                yield Label("Ready", id="status")
                yield Label("", id="volume_display")

        yield Footer()

    def on_mount(self):
        self.player = Player(self.on_track_end)
        self.queue = Queue(self.player)
        self.visualizer.attach_player(self.player)
        self.set_interval(0.3, self.update_progress)
        self.volume_display_timer = None
        self.search_history = []
        self.history_index = -1
        
        # Load random songs on startup
        self.load_random_songs()
    
    def load_random_songs(self):
        """Load random/trending songs into the list on startup"""
        lv = self.query_one("#results", ListView)
        status_label = self.query_one("#status", Label)
        
        status_label.update("Loading trending songs...")
        
        tracks = get_random_songs()
        if tracks:
            self.queue.load(tracks)
            for t in tracks:
                item = ListItem(Label(f"{t['title']} — {t['artist']}"))
                item.track = t
                lv.append(item)
            status_label.update(f"Ready - {len(tracks)} trending songs loaded")
        else:
            status_label.update("Ready - Failed to load trending songs")

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
                    self.query_one("#status", Label).update(f"✓ Playlist '{playlist_name}' saved")
                else:
                    self.query_one("#status", Label).update("✖ Failed to save playlist")
            else:
                self.query_one("#status", Label).update("✖ Invalid playlist name or empty queue")
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
                self.query_one("#status", Label).update(f"✓ Loaded playlist '{playlist_name}' ({len(tracks)} songs)")
            else:
                self.query_one("#status", Label).update(f"✖ Playlist '{playlist_name}' not found")
            return
        
        elif input_value == ":playlists":
            # Show available playlists
            playlists = list_playlists()
            if playlists:
                self.query_one("#status", Label).update(f"Saved playlists: {', '.join(playlists)}")
            else:
                self.query_one("#status", Label).update("No saved playlists")
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
                self.query_one("#status", Label).update(f"✓ Loaded {len(tracks)} tracks from history")
            else:
                self.query_one("#status", Label).update("No playback history")
            return
        
        # Add to search history
        if input_value and (not self.search_history or self.search_history[-1] != input_value):
            self.search_history.append(input_value)
        self.history_index = len(self.search_history)
        
        # Check if input is a playlist URL
        if "list=" in input_value or "playlist" in input_value:
            self.query_one("#status", Label).update("Loading playlist...")
            tracks = get_playlist_songs(input_value)
            if not tracks:
                self.query_one("#status", Label).update("✖ Failed to load playlist")
                return
            self.query_one("#status", Label).update(f"Ready - {len(tracks)} songs from playlist")
        else:
            # Regular search
            self.query_one("#status", Label).update("Searching...")
            tracks = search_tracks(input_value)
            if not tracks:
                self.query_one("#status", Label).update("✖ Search failed or no results")
                return
            self.query_one("#status", Label).update("Ready")

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
            self.query_one("#status", Label).update("▶ Playing")
            self.highlight_current_track()
            add_to_history(track)  # Add to playback history
        else:
            self.query_one("#status", Label).update("✖ Failed to load track")
    
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
                self.query_one("#status", Label).update("▶ Playing")
                self.highlight_current_track()
                add_to_history(track)  # Add to playback history
            else:
                self.query_one("#status", Label).update("✖ Failed to load next track")
        else:
            self.query_one("#status", Label).update("■ Queue Ended")

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
                self.query_one("#status", Label).update("▶ Playing")
                self.highlight_current_track()
                add_to_history(track)  # Add to playback history
            else:
                self.query_one("#status", Label).update("✖ Failed to load track")
        elif event.key == "p":
            success = self.queue.previous()
            if success:
                track = self.queue.tracks[self.queue.index]
                self.meta.update_track(track)
                self.query_one("#status", Label).update("▶ Playing")
                self.highlight_current_track()
                add_to_history(track)  # Add to playback history
            else:
                self.query_one("#status", Label).update("✖ Failed to load track")
        elif event.key in ("+", "="):
            self.player.volume_up()
            self.show_volume()
        elif event.key == "-":
            self.player.volume_down()
            self.show_volume()
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
