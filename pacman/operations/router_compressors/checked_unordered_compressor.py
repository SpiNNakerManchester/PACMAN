from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanElementAllocationException
from .unordered_compressor import UnorderedCompressor

MAX_SUPPORTED_LENGTH = 1023


class CheckedUnorderedCompressor(UnorderedCompressor):
    __slots__ = []

    def __call__(self, router_tables, target_length=None):
        if target_length is None:
            # Stop when enought
            self._target_length = MAX_SUPPORTED_LENGTH
        else:
            self._target_length = target_length
        # create progress bar
        progress = ProgressBar(
            router_tables.routing_tables, "Compressing routing Tables")
        compressed = self.compress_tables(router_tables, progress)
        self.verify_lengths(compressed)
        return compressed

    def verify_lengths(self, compressed):
        problems = ""
        for table in compressed:
            if table.number_of_entries > self._target_length:
                problems += "(x:{},y:{})={} ".format(
                    table.x, table.y, table.number_of_entries)
        if len(problems) > 0:
            raise PacmanElementAllocationException(
                "The routing table after compression will still not fit"
                " within the machines router: {}".format(problems))
