import sys
import termios
import time

import pyperclip
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from .audio import AudioDeviceHandler
from .config import Config
from .listener import Listener


class App:
    def __init__(self):
        self.console = Console()
        self.config = Config.load()
        self.config.parse_args()

        if self.config.copy_to_clipboard:
            self.console.print("transcript will be copied to clipboard upon completion")
        if self.config.write_to_file:
            self.console.print("transcript will be saved to {self.config.output_path} upon completion")

        self.console.print("configuring audio devices")
        self.audio_handler = AudioDeviceHandler(self.config)
        loopback_device_index = self.audio_handler.setup_loopback()

        self.console.print("loading speech-to-text model")
        self.listener = Listener(self.config, loopback_device_index)

        self.transcript = [""]
        self.running = True

        # turn off terminal echo
        self.stdin_fd = sys.stdin.fileno()
        self.stdin = termios.tcgetattr(self.stdin_fd)
        self.stdn_silent = termios.tcgetattr(self.stdin_fd)
        self.stdn_silent[3] = self.stdn_silent[3] & ~termios.ECHO
        termios.tcsetattr(self.stdin_fd, termios.TCSADRAIN, self.stdn_silent)

    def stop(self, *_):
        self.running = False
        self.listener.stop()

    def print_transcript(self):
        return Panel("\n".join(self.transcript))

    def run(self):
        # Cue the user that we're ready to go.
        self.console.print("now listeining, press ctrl-c to stop")
        with Live(
            self.print_transcript(),
            console=self.console,
            auto_refresh=False,
        ) as live:  # update 4 times a second to feel fluid
            for utterance, utterance_complete in self.listener:
                # If we detected a pause between recordings, add a new item to our transcripion.
                # Otherwise edit the existing one.
                if utterance_complete:
                    self.transcript.append(utterance)
                else:
                    self.transcript[-1] = utterance

                live.update(self.print_transcript(), refresh=True)

                # Infinite loops are bad for processors, must sleep.
                time.sleep(0.1)

                if not self.running:
                    live.stop()
                    break
        self.finish()

    def finish(self):
        # turn on terminal echo
        termios.tcsetattr(self.stdin_fd, termios.TCSADRAIN, self.stdin)
        self.audio_handler.revert()
        if self.config.copy_to_clipboard:
            pyperclip.copy("\n".join(self.transcript))
            self.console.print("transcript copied to clipboard")
        if self.config.write_to_file:
            with self.config.output_path.open("w") as f:
                f.write("\n".join(self.transcript))
            self.console.print("transcript written to file")
