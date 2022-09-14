# Copyright (c) 2021-2022 The University of Manchester
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
from pacman.model.placements import Placements
from pacman.model.routing_info import RoutingInfo
from pacman.model.routing_table_by_partition import (
    MulticastRoutingTableByPartition)
from pacman.model.routing_tables import MulticastRoutingTables
from pacman.model.tags import Tags
from pacman.exceptions import PacmanConfigurationException
from .pacman_data_view import PacmanDataView, _PacmanDataModel

logger = FormatAdapter(logging.getLogger(__name__))
__temp_dir = None

REPORTS_DIRNAME = "reports"
# pylint: disable=protected-access


class PacmanDataWriter(MachineDataWriter, PacmanDataView):
    """
    See UtilsDataWriter

    This class is designed to only be used directly within the PACMAN
    repository unittests as all methods are available to subclasses

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

    @overrides(MachineDataWriter._hard_reset)
    def _hard_reset(self):
        MachineDataWriter._hard_reset(self)
        self.__pacman_data._hard_reset()

    @overrides(MachineDataWriter._soft_reset)
    def _soft_reset(self):
        MachineDataWriter._soft_reset(self)
        self.__pacman_data._soft_reset()

    def set_placements(self, placements):
        """
        Set the placements

        :param Placements placements:
        :raises TypeError: if the placements is not a Placements
        """
        if not isinstance(placements, Placements):
            raise TypeError("placements should be a Placements")
        self.__pacman_data._placements = placements

    def set_routing_infos(self, routing_infos):
        """
        Set the routing_infos

        :param RoutingInfo routing_infos:
        :raises TypeError: if the routing_infos is not a RoutingInfo
        """
        if not isinstance(routing_infos, RoutingInfo):
            raise TypeError("routing_infos should be a RoutingInfo")
        self.__pacman_data._routing_infos = routing_infos

    def set_tags(self, tags):
        """
        Set the tags

        :param Tags tags:
        :raises TypeError: if the tags is not a Tags
        """
        if not isinstance(tags, Tags):
            raise TypeError("tags should be a Tags")
        self.__pacman_data._tags = tags

    def set_uncompressed(self, router_tables):
        """
        Sets the uncompressed router_tables value

        :param MulticastRoutingTables router_tables: new value
        :raises TypeError:
        if the router_tables is not a MulticastRoutingTables
        """
        if not isinstance(router_tables, MulticastRoutingTables):
            raise TypeError(
                "router_tables should be a MulticastRoutingTables")
        self.__pacman_data._uncompressed = router_tables

    def set_precompressed(self, router_tables):
        """
        Sets the precompressed router_tables value

        :param MulticastRoutingTables router_tables: new value
        :raises TypeError:
        if the router_tables is not a MulticastRoutingTables
        """
        if not isinstance(router_tables, MulticastRoutingTables):
            raise TypeError(
                "router_tables should be a MulticastRoutingTables")
        self.__pacman_data._precompressed = router_tables

    def set_plan_n_timesteps(self, plan_n_timesteps):
        """
        Sets the plan_n_timestep. Use None for run forever

        :param plan_n_timesteps:
        :type plan_n_timesteps: int or None
        :raises TypeError: if the plan_n_timesteps are not an int or None
        :raises PacmanConfigurationException: On a megative plan_n_timesteps
        """
        if plan_n_timesteps is not None:
            if not isinstance(plan_n_timesteps, int):
                raise TypeError("plan_n_timesteps should be an int")
            if plan_n_timesteps < 0:
                raise PacmanConfigurationException(
                    f"plan_n_timesteps {plan_n_timesteps} "
                    f"must not be negative")
        self.__pacman_data._plan_n_timesteps = plan_n_timesteps

    def set_routing_table_by_partition(self, routing_table_by_partition):
        """
        Sets the _routing_table_by_partition

        :param MulticastRoutingTableByPartition routing_table_by_partition:
        raises TypeError: if routing_table_by_partition is no a
        MulticastRoutingTableByPartition
        """
        if not isinstance(
                routing_table_by_partition, MulticastRoutingTableByPartition):
            raise TypeError(
                "routing_table_by_partition should be a "
                "MulticastRoutingTableByPartition")
        self.__pacman_data._routing_table_by_partition = \
            routing_table_by_partition

    @classmethod
    def add_vertex(cls, vertex):
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        if not cls.get_requires_mapping():
            raise PacmanConfigurationException(
                "This call is only expected if requires mapping is True")
        cls.__pacman_data._graph.add_vertex(vertex)

    @classmethod
    def add_edge(cls, edge, outgoing_edge_partition_name):
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        if not cls.get_requires_mapping():
            raise PacmanConfigurationException(
                "This call is only expected if requires mapping is True")
        cls.__pacman_data._graph.add_edge(edge, outgoing_edge_partition_name)
