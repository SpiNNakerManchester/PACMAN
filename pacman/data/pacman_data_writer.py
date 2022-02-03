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
from spinn_utilities.overrides import overrides
from spinn_machine.data.machine_data_writer import MachineDataWriter
from pacman.model.graphs.application import ApplicationGraph
from pacman.model.graphs.machine import MachineGraph
from pacman.model.placements import Placements
from pacman.model.routing_info import (
    DictBasedMachinePartitionNKeysMap, RoutingInfo)
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.model.tags import Tags
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

    @overrides(MachineDataWriter._mock)
    def _mock(self):
        MachineDataWriter._mock(self)
        self.__pacman_data._clear()

    @overrides(MachineDataWriter._setup)
    def _setup(self):
        MachineDataWriter._setup(self)
        self.__pacman_data._clear()

    def hard_reset(self):
        MachineDataWriter.hard_reset(self)
        self.__pacman_data._hard_reset()

    def soft_reset(self):
        MachineDataWriter.soft_reset(self)
        self.__pacman_data._soft_reset()

    def get_graph(self):
        """
        The user level application graph

        This removes the safety check so ASB can access the graph during run

        :rtype: ApplicationGraph
        """
        return self.__pacman_data._graph

    def get_machine_graph(self):
        """
        The user level machine graph

        Previously known as asb._original_machine_graph.

        Changes to this graph will only affect the next run

        This removes the safety check so ASB can access the graph during run

        :rtype: MachineGraph
        """
        return self.__pacman_data._machine_graph

    def get_runtime_graph(self):
        return self.__pacman_data._runtime_graph

    def get_runtime_machine_graph(self):
        return self.__pacman_data._runtime_machine_graph

    def create_graphs(self, graph_label):
        """
        Creates the user/ original graphs based on the label

        :param str graph_label:
        """
        # update graph label if needed
        if graph_label is None:
            graph_label = "Application_graph"

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

    def set_placements(self, placements):
        """
        Set the placements

        :param Placements placements:
        """
        if not isinstance(placements, Placements):
            raise TypeError("placements should be a Placements")
        self.__pacman_data._placements = placements

    def set_routing_infos(self, routing_infos):
        """
        Set the routing_infos

        :param RoutingInfo routing_infos:
        """
        if not isinstance(routing_infos, RoutingInfo):
            raise TypeError("routing_infos should be a RoutingInfo")
        self.__pacman_data._routing_infos = routing_infos

    def set_tags(self, tags):
        """
        Set the tags

        :param Tags tags:
        """
        if not isinstance(tags, Tags):
            raise TypeError("tags should be a Tags")
        self.__pacman_data._tags = tags

    def set_machine_partition_n_keys_map(self, machine_partition_n_keys_map):
        """
        Sets the machine_partition_n_keys_map value

        :param DictBasedMachinePartitionNKeysMap machine_partition_n_keys_map:
            new value
        """
        if not isinstance(machine_partition_n_keys_map,
                          DictBasedMachinePartitionNKeysMap):
            raise TypeError(
                "machine_partition_n_keys_map should be a"
                " DictBasedMachinePartitionNKeysMap")
        self.__pacman_data._machine_partition_n_keys_map = \
            machine_partition_n_keys_map

    def set_router_tables(self, router_tables):
        """
        Sets the router_tables value

        :param MulticastRoutingTables router_tables: new value
        """
        if not isinstance(router_tables, MulticastRoutingTables):
            raise TypeError(
                "router_tables should be a MulticastRoutingTables")
        self.__pacman_data._router_tables = router_tables
