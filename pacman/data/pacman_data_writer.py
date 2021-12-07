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

import logging
from spinn_utilities.log import FormatAdapter
from spinn_machine.data.machine_data_writer import MachineDataWriter
from pacman.model.graphs.application import ApplicationGraph
from pacman.model.graphs.machine import MachineGraph
from pacman.exceptions import PacmanConfigurationException
from .pacman_data_view import PacmanDataView, _PacmanDataModel

logger = FormatAdapter(logging.getLogger(__name__))
__temp_dir = None

REPORTS_DIRNAME = "reports"


class PacmanDataWriter(MachineDataWriter, PacmanDataView):
    """
    Writer class for the Fec Data

    """
    __pacman_data = _PacmanDataModel()
    __slots__ = []

    def mock(self):
        """
        Clears out all data and adds mock values where needed.

        This should set the most likely defaults values.
        But be aware that what is considered the most likely default could
        change over time.

        Unittests that depend on any valid value being set should be able to
        depend on Mock.

        Unittest that depend on a specific value should call mock and then
        set that value.
        """
        MachineDataWriter.mock(self)
        self.__pacman_data._clear()

    def setup(self):
        """
        Puts all data back into the state expected at sim.setup time

        """
        MachineDataWriter.setup(self)
        self.__pacman_data._clear()

    def hard_reset(self):
        MachineDataWriter.hard_reset(self)
        self.__pacman_data._hard_reset()

    def soft_reset(self):
        MachineDataWriter.soft_reset(self)
        self.__pacman_data._soft_reset()

    def get_graph(self):
        return self.__pacman_data._graph

    def get_machine_graph(self):
        return self.__pacman_data._machine_graph

    def create_graphs(self, graph_label):
        """
        Creates the user/ original graphs based on the label

        :param str graph_label:
        """
        # update graph label if needed
        if graph_label is None:
            graph_label = "Application_graph"
        else:
            graph_label = graph_label

        self.__pacman_data._graph = ApplicationGraph(label=graph_label)
        self.__pacman_data._machine_graph = MachineGraph(
            label=graph_label,
            application_graph=self.__pacman_data._graph)

    def clone_graphs(self):
        """
        Clones the user/ original grapgs and creates runtime ones

        """
        if self.__pacman_data._graph.n_vertices:
            if self.__pacman_data._machine_graph.n_vertices:
                raise PacmanConfigurationException(
                    "Illegal state where both original_application and "
                    "original machine graph have vertices in them")

        self.__pacman_data._runtime_graph = self.__pacman_data._graph.clone()
        self.__pacman_data._runtime_machine_graph = \
            self.__pacman_data._machine_graph.clone()

    def _set_runtime_graph(self, graph):
        """
        Only used in unittests
        """
        self.__pacman_data._runtime_graph = graph

    def set_runtime_machine_graph(self, runtime_machine_graph):
        """
        Set the runtime machine graph

        :param MachineGraph runtime_machine_graph:
        """
        if not isinstance(runtime_machine_graph, MachineGraph):
            raise TypeError("runtime_machine_graph should be a MachineGraph")
        self.__pacman_data._runtime_machine_graph = runtime_machine_graph
