import subprocess, socket, json, os, threading, time, signal
from app.services.resolver import resolve_audio

SOCKET = "/tmp/cplayer.sock"

class Player:
    def __init__(self, on_end):
        self.proc = None
        self.sock = None
        self.on_end = on_end
        self.running = False
        self.time_pos = 0
        self.duration = 1

    def play(self, track):
        self.stop()
        url = resolve_audio(track["videoId"])

        if not url:
            return False

        if os.path.exists(SOCKET):
            os.remove(SOCKET)

        self.proc = subprocess.Popen(
            ["mpv", url, "--no-video", "--quiet", f"--input-ipc-server={SOCKET}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )

        self.running = True
        threading.Thread(target=self._ipc_loop, daemon=True).start()
        return True

    def _ipc_loop(self):
        for _ in range(40):
            if os.path.exists(SOCKET):
                break
            time.sleep(0.1)

        try:
            self.sock = socket.socket(socket.AF_UNIX)
            self.sock.connect(SOCKET)

            self._send(["observe_property", 1, "time-pos"])
            self._send(["observe_property", 2, "duration"])

            while self.running:
                data = self.sock.recv(4096)
                for line in data.splitlines():
                    msg = json.loads(line.decode())
                    if msg.get("name") == "time-pos":
                        self.time_pos = msg.get("data") or 0
                    elif msg.get("name") == "duration":
                        self.duration = msg.get("data") or 1
                    elif msg.get("event") == "end-file":
                        self.on_end()
        except Exception:
            pass

    def _send(self, cmd):
        if self.sock:
            self.sock.sendall((json.dumps({"command": cmd}) + "\n").encode())

    def toggle_pause(self):
        self._send(["cycle", "pause"])

    def volume_up(self):
        self._send(["add", "volume", 5])

    def volume_down(self):
        self._send(["add", "volume", -5])

    def stop(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        try:
            if self.proc:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except:
            pass
        self.proc = None
