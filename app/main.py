from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, ListView, ListItem, Label, ProgressBar
from textual.containers import Horizontal, Vertical
from textual import events

from app.ui.banner import Banner
from app.ui.visualizer import Visualizer
from app.ui.panels import MetadataPanel
from app.controller.player import Player
from app.controller.queue import Queue
from app.services.ytmusic import search_tracks


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
        min-height: 10;
        background: #1a1a2e;
    }
    
    MetadataPanel #progress {
        margin: 1 0 0 0;
        height: 1;
    }
    
    Visualizer {
        border: solid #6366f1;
        padding: 1;
        width: 30;
        min-width: 26;
        height: 100%;
        background: #1a1a2e;
    }
    
    #status {
        text-align: center;
        background: #1a1a2e;
        color: #818cf8;
        padding: 0 1;
        height: 1;
        margin: 0 1 1 1;
        border: solid #6366f1;
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
        yield Input(placeholder="Search YouTube Music…")

        with Horizontal(classes="main-container"):
            yield ListView(id="results")
            yield Vertical(classes="spacer")

            with Vertical(classes="side-panels"):
                self.meta = MetadataPanel()
                yield self.meta

            yield Vertical(classes="spacer")
            self.visualizer = Visualizer()
            yield self.visualizer

        yield Label("Ready", id="status")
        yield Footer()

    def on_mount(self):
        self.player = Player(self.on_track_end)
        self.queue = Queue(self.player)
        self.visualizer.attach_player(self.player)
        self.set_interval(0.3, self.update_progress)

    def on_unmount(self):
        self.player.stop()

    async def on_input_submitted(self, event):
        lv = self.query_one("#results", ListView)
        lv.clear()
        
        self.query_one("#status", Label).update("Searching...")

        tracks = search_tracks(event.value)
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
        else:
            self.query_one("#status", Label).update("✖ Failed to load track")

    def update_progress(self):
        pb = self.query_one("#progress", ProgressBar)
        pb.total = int(self.player.duration)
        pb.progress = int(self.player.time_pos)

    def on_track_end(self):
        self.query_one("#status", Label).update("■ Ended")

    async def on_key(self, event: events.Key):
        if event.key == "space":
            self.player.toggle_pause()
        elif event.key == "n":
            success = self.queue.next()
            if success:
                track = self.queue.tracks[self.queue.index]
                self.meta.update_track(track)
                self.query_one("#status", Label).update("▶ Playing")
            else:
                self.query_one("#status", Label).update("✖ Failed to load track")
        elif event.key == "p":
            success = self.queue.previous()
            if success:
                track = self.queue.tracks[self.queue.index]
                self.meta.update_track(track)
                self.query_one("#status", Label).update("▶ Playing")
            else:
                self.query_one("#status", Label).update("✖ Failed to load track")
        elif event.key in ("+", "="):
            self.player.volume_up()
        elif event.key == "-":
            self.player.volume_down()
        elif event.key == "ctrl+q":
            self.player.stop()
            await self.action_quit()


if __name__ == "__main__":
    CPlayer().run()
