"""
ProgressBar
"""
from __future__ import print_function
import logging
import sys
import math

logger = logging.getLogger(__name__)


class ProgressBar(object):
    """ Progress bar for telling the user where a task is up to
    """
    MAX_LENGTH_IN_CHARS = 60

    def __init__(self, total_number_of_things_to_do,
                 string_describing_what_being_progressed):
        self._total_number_of_things_to_do = total_number_of_things_to_do
        self._currently_completed = 0
        self._chars_per_thing = None
        self._last_update = 0
        self._chars_done = 0
        self._string = string_describing_what_being_progressed

        self._create_initial_progress_bar(
            string_describing_what_being_progressed)

    def update(self, amount_to_add=1):
        """ Update the progress bar by a given amount
        :param amount_to_add:
        :return:
        """
        self._currently_completed += amount_to_add
        self._check_differences()

    def _create_initial_progress_bar(self,
                                     string_describing_what_being_progressed):
        if self._total_number_of_things_to_do == 0:
            self._chars_per_thing = ProgressBar.MAX_LENGTH_IN_CHARS
        else:
            self._chars_per_thing = (float(ProgressBar.MAX_LENGTH_IN_CHARS) /
                                     float(self._total_number_of_things_to_do))
        print(string_describing_what_being_progressed, file=sys.stderr)
        print("|0                           50%                         100%|",
              file=sys.stderr)
        print(" ", end="", file=sys.stderr)
        self._check_differences()

    def _check_differences(self):
        expected_chars_done = math.floor(self._currently_completed *
                                         self._chars_per_thing)
        if self._currently_completed == self._total_number_of_things_to_do:
            expected_chars_done = ProgressBar.MAX_LENGTH_IN_CHARS
        while self._chars_done < expected_chars_done:
            print("=", end='', file=sys.stderr)
            self._chars_done += 1
        sys.stderr.flush()

    def end(self):
        """ Close the progress bar, updating whatever is left if needed
        :return:
        """
        difference = \
            self._total_number_of_things_to_do - self._currently_completed
        self._currently_completed += difference
        self._check_differences()
        print("", file=sys.stderr)

    def __repr__(self):
        return "progress bar for {}".format(self._string)
