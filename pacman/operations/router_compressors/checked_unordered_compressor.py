# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.progress_bar import ProgressBar
from pacman.exceptions import PacmanElementAllocationException
from .unordered_compressor import UnorderedCompressor


class CheckedUnorderedCompressor(UnorderedCompressor):
    __slots__ = []

    def __call__(self, router_tables, target_length=None):
        if target_length is None:
            # Stop when enought
            self._target_length = self.MAX_SUPPORTED_LENGTH
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
            if table.number_of_entries > self.MAX_SUPPORTED_LENGTH:
                problems += "(x:{},y:{})={} ".format(
                    table.x, table.y, table.number_of_entries)
        if len(problems) > 0:
            raise PacmanElementAllocationException(
                "The routing table after compression will still not fit"
                " within the machines router: {}".format(problems))
