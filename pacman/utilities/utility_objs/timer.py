import datetime


class Timer(object):
    """
    A timer used for performance measurements
    """

    __slots__ = [
        # The start time when the timer was set off
        "_start_time"
    ]

    def __init__(self):
        self._start_time = None

    def start_timing(self):
        self._start_time = datetime.datetime.now()

    def take_sample(self):
        time_now = datetime.datetime.now()
        diff = time_now - self._start_time
        return diff
