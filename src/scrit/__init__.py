import signal

from .app import App


def main():
    app = App()
    signal.signal(signal.SIGINT, app.stop)
    app.run()
