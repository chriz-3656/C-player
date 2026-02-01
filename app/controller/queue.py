class Queue:
    def __init__(self, player):
        self.player = player
        self.tracks = []
        self.index = -1

    def load(self, tracks):
        self.tracks = tracks
        self.index = -1

    def play_single(self, track):
        # Find the track index in the queue
        for i, t in enumerate(self.tracks):
            if t.get('videoId') == track.get('videoId'):
                self.index = i
                break
        return self.player.play(track)

    def next(self):
        if not self.tracks:
            return False
        self.index = (self.index + 1) % len(self.tracks)
        return self.player.play(self.tracks[self.index])

    def previous(self):
        if not self.tracks:
            return False
        self.index = (self.index - 1) % len(self.tracks)
        return self.player.play(self.tracks[self.index])
