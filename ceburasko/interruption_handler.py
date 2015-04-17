import signal


class InterruptionHandler(object):
    def __init__(self, signum=signal.SIGINT):
        self.old_handler = signal.getsignal(signum)
        signal.signal(signum, self)

    def __call__(self, signum, frame):
        self.on_signal(signum)
        self.old_handler(signum, frame)

    def on_signal(self, signum):
        pass
