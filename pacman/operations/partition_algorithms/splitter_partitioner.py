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

from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint)
from pacman.model.partitioner_interfaces import AbstractSplitterPartitioner
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls as utils
from pacman.utilities.utility_objs.chip_counter import ChipCounter


class SplitterPartitioner(AbstractSplitterPartitioner):
    """ Partitioner which hands the partitioning work to application vertices'\
        splitter objects.
    """

    __slots__ = []

    # inherited from AbstractPartitionAlgorithm
    def __call__(self, app_graph, plan_n_time_steps):
        """
        :param ApplicationGraph app_graph: The application_graph to partition
        :param plan_n_time_steps: the number of time steps to plan to run for
        :return:
            the estimated number of chips needed to satisfy this partitioning.
        :rtype: int
        :raise PacmanPartitionException:
            If something goes wrong with the partitioning
        """

        vertices = app_graph.vertices
        progress = ProgressBar(len(vertices), "Partitioning Graph")

        self.__set_max_atoms_to_splitters(app_graph)

        # Partition one vertex at a time
        chip_counter = ChipCounter(plan_n_time_steps)
        for vertex in progress.over(vertices):
            vertex.splitter.create_machine_vertices(chip_counter)

        return chip_counter.n_chips

    @staticmethod
    def __set_max_atoms_to_splitters(app_graph):
        """ get the constraints sorted out.

        :param ApplicationGraph app_graph: the app graph
        """
        for vertex in app_graph.vertices:
            for constraint in utils.locate_constraints_of_type(
                    vertex.constraints, MaxVertexAtomsConstraint):
                vertex.splitter.set_max_atoms_per_core(
                    constraint.size, False)
            for constraint in utils.locate_constraints_of_type(
                    vertex.constraints, FixedVertexAtomsConstraint):
                vertex.splitter.set_max_atoms_per_core(
                    constraint.size, True)
