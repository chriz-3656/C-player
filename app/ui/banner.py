from textual.widgets import Static
from textual.containers import Horizontal
import pyfiglet

class BannerLogo(Static):
    pass

class BannerControls(Static):
    pass

class BannerInfo(Static):
    pass

class Banner(Static):
    def compose(self):
        with Horizontal():
            yield BannerLogo(id="banner-logo")
            yield BannerControls(id="banner-controls")
            yield BannerInfo(id="banner-info")
    
    def on_mount(self):
        fig = pyfiglet.Figlet(font="slant")
        text = fig.renderText("C-PLAYER")
        
        logo_widget = self.query_one("#banner-logo", BannerLogo)
        logo_widget.update(f"[#818cf8]{text}[/#818cf8]\n[dim]YouTube Music Terminal Player[/dim]")
        
        controls_widget = self.query_one("#banner-controls", BannerControls)
        controls_widget.update(
            "[b #818cf8]⌨ Controls[/b #818cf8]\n\n"
            "[b]Enter[/b]   : Play Track\n"
            "[b]Space[/b]   : Pause/Resume\n"
            "[b]n / p[/b]   : Next/Previous\n"
            "[b]+ / -[/b]   : Volume Up/Down\n"
            "[b]Ctrl+Q[/b] : Quit"
        )
        
        info_widget = self.query_one("#banner-info", BannerInfo)
        info_widget.update(
            "[b #818cf8]      C-PLAYER v1.0[/b #818cf8]\n"
            "[b]Creator:[/b]  Chris\n"
            "[b]GitHub:[/b]   chriz-3656\n"
            "[dim]https://github.com/chriz-3656[/dim]"
        )
        
        self.styles.height = 9
