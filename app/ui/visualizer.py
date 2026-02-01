import random
from textual.widgets import Static

class Visualizer(Static):
    def __init__(self):
        super().__init__()
        self.player = None
        self.styles.width = 24
        self.styles.height = 6

    def attach_player(self, player):
        self.player = player
        self.set_interval(0.15, self.tick)

    def tick(self):
        if not self.player or not self.player.running:
            self.update("▁" * 22)
            return
        self.update("".join(random.choice("▁▂▃▄▅▆▇█") for _ in range(22)))
