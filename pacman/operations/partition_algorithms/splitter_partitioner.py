# Copyright (c) 2020-2021 The University of Manchester
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

from pacman.data import PacmanDataView
from pacman.model.partitioner_interfaces import AbstractSplitterPartitioner
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.utility_objs.chip_counter import ChipCounter


def splitter_partitioner():
    """
     :return:
         The number of chips needed to satisfy this partitioning.
     :rtype: int
     :raise PacmanPartitionException:
         If something goes wrong with the partitioning
     """
    partitioner = _SplitterPartitioner()
    # pylint:disable=protected-access
    return partitioner._run()


class _SplitterPartitioner(AbstractSplitterPartitioner):
    """ Partitioner which hands the partitioning work to application vertices'\
        splitter objects.
    """

    __slots__ = []

    # inherited from AbstractPartitionAlgorithm
    def _run(self):
        """
        :rtype: int
        :raise PacmanPartitionException:
            If something goes wrong with the partitioning
        """
        vertices = PacmanDataView.get_runtime_graph().vertices
        progress = ProgressBar(len(vertices), "Partitioning Graph")

        # Partition one vertex at a time
        chip_counter = ChipCounter()
        for vertex in progress.over(vertices):
            vertex.splitter.create_machine_vertices(chip_counter)

        return chip_counter.n_chips
