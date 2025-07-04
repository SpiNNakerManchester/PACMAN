# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
import logging
from typing import Optional
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_machine.data.machine_data_writer import MachineDataWriter
from pacman.model.graphs.application import ApplicationEdge, ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
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
    See :py:class:`spinn_utilities.data.UtilsDataWriter`.

    This class is designed to only be used directly within the PACMAN
    repository unit tests as all methods are available to subclasses.
    """
    __pacman_data: _PacmanDataModel = _PacmanDataModel()
    __slots__ = ()

    @overrides(MachineDataWriter._mock)
    def _mock(self) -> None:
        MachineDataWriter._mock(self)
        self.__pacman_data._clear()

    @overrides(MachineDataWriter._setup)
    def _setup(self) -> None:
        MachineDataWriter._setup(self)
        self.__pacman_data._clear()

    @overrides(MachineDataWriter._hard_reset)
    def _hard_reset(self) -> None:
        MachineDataWriter._hard_reset(self)
        self.__pacman_data._hard_reset()

    @overrides(MachineDataWriter._soft_reset)
    def _soft_reset(self) -> None:
        MachineDataWriter._soft_reset(self)
        self.__pacman_data._soft_reset()

    def set_placements(self, placements: Placements) -> None:
        """
        Set the placements.

        :param placements:
        :raises TypeError: if the placements is not a Placements
        """
        if not isinstance(placements, Placements):
            raise TypeError("placements should be a Placements")
        self.__pacman_data._placements = placements

    def set_routing_infos(self, routing_infos: RoutingInfo) -> None:
        """
        Set the routing_infos.

        :param routing_infos:
        :raises TypeError: if the routing_infos is not a RoutingInfo
        """
        if not isinstance(routing_infos, RoutingInfo):
            raise TypeError("routing_infos should be a RoutingInfo")
        self.__pacman_data._routing_infos = routing_infos

    def set_tags(self, tags: Tags) -> None:
        """
        Set the tags.

        :param tags:
        :raises TypeError: if the tags is not a Tags
        """
        if not isinstance(tags, Tags):
            raise TypeError("tags should be a Tags")
        self.__pacman_data._tags = tags

    def set_uncompressed(self, router_tables: MulticastRoutingTables) -> None:
        """
        Sets the uncompressed `router_tables` value.

        :param router_tables: new value
        :raises TypeError:
            if the router_tables is not a MulticastRoutingTables
        """
        if not isinstance(router_tables, MulticastRoutingTables):
            raise TypeError(
                "router_tables should be a MulticastRoutingTables")
        self.__pacman_data._uncompressed = router_tables

    def set_precompressed(
            self, router_tables: MulticastRoutingTables) -> None:
        """
        Sets the precompressed `router_tables` value.

        :param router_tables: new value
        :raises TypeError:
            if the router_tables is not a MulticastRoutingTables
        """
        if not isinstance(router_tables, MulticastRoutingTables):
            raise TypeError(
                "router_tables should be a MulticastRoutingTables")
        self.__pacman_data._precompressed = router_tables

    def set_plan_n_timesteps(self, plan_n_timesteps: Optional[int]) -> None:
        """
        Sets the `plan_n_timestep`. Use `None` for run forever.

        :param plan_n_timesteps:
        :raises TypeError: if the plan_n_timesteps are not an int or `None`
        :raises PacmanConfigurationException: On a negative plan_n_timesteps
        """
        if plan_n_timesteps is not None:
            if not isinstance(plan_n_timesteps, int):
                raise TypeError("plan_n_timesteps should be an int")
            if plan_n_timesteps < 0:
                raise PacmanConfigurationException(
                    f"plan_n_timesteps {plan_n_timesteps} "
                    f"must not be negative")
        self.__pacman_data._plan_n_timesteps = plan_n_timesteps

    def set_routing_table_by_partition(
            self, routing_table_by_partition:
            MulticastRoutingTableByPartition) -> None:
        """
        Sets the `_routing_table_by_partition`.

        :param routing_table_by_partition:
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
    def add_vertex(cls, vertex: ApplicationVertex) -> None:
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        if not cls.get_requires_mapping():
            raise PacmanConfigurationException(
                "This call is only expected if requires mapping is True")
        cls.__pacman_data._graph.add_vertex(vertex)

    @classmethod
    def add_edge(cls, edge: ApplicationEdge,
                 outgoing_edge_partition_name: str) -> None:
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        if not cls.get_requires_mapping():
            raise PacmanConfigurationException(
                "This call is only expected if requires mapping is True")
        cls.__pacman_data._graph.add_edge(edge, outgoing_edge_partition_name)

    def add_sample_monitor_vertex(
            self, vertex: MachineVertex, all_chips: bool) -> None:
        """
        Accepts a simple of the monitor cores to be added.

        Should be called once for each monitor added to all (Ethernet) chips.

        Only affect is to change the numbers reported by the
        get_all/ethernet_monitor methods.

        :param vertex:
            One of the vertices added to each core, assumed to be typical of
            all.
        :param all_chips:
            If True assumes that this Vertex will be placed on all chips
            including Ethernet ones.
            If False assumes that this Vertex type will only be placed on
            Ethernet Vertices
        """
        self.add_monitor_core(all_chips)
        self.__pacman_data._ethernet_monitor_vertices.append(vertex)
        if all_chips:
            self.__pacman_data._all_monitor_vertices.append(vertex)

    def set_n_required(self, n_boards_required: Optional[int],
                       n_chips_required: Optional[int]) -> None:
        """
        Sets (if not `None`) the number of boards/chips requested by the user.

        :param n_boards_required:
            `None` or the number of boards requested by the user
        :param n_chips_required:
            `None` or the number of chips requested by the user
        """
        if n_boards_required is None:
            if n_chips_required is None:
                return
            elif not isinstance(n_chips_required, int):
                raise TypeError("n_chips_required must be an int (or None)")
            if n_chips_required <= 0:
                raise ValueError(
                    "n_chips_required must be positive and not "
                    f"{n_chips_required}")
        else:
            if n_chips_required is not None:
                raise ValueError(
                    "Illegal call with both both param provided as "
                    f"{n_boards_required}, {n_chips_required}")
            if not isinstance(n_boards_required, int):
                raise TypeError("n_boards_required must be an int (or None)")
            if n_boards_required <= 0:
                raise ValueError(
                    "n_boards_required must be positive and not "
                    f"{n_boards_required}")
        if self.__pacman_data._n_boards_required is not None or \
                self.__pacman_data._n_chips_required is not None:
            raise ValueError(
                "Illegal second call to set_n_required")
        self.__pacman_data._n_boards_required = n_boards_required
        self.__pacman_data._n_chips_required = n_chips_required

    def set_n_chips_in_graph(self, n_chips_in_graph: int) -> None:
        """
        Sets the number of chips needed by the graph.
        """
        if not isinstance(n_chips_in_graph, int):
            raise TypeError("n_chips_in_graph must be an int (or None)")
        if n_chips_in_graph <= 0:
            raise ValueError(
                "n_chips_in_graph must be positive and not "
                f"{n_chips_in_graph}")
        self.__pacman_data._n_chips_in_graph = n_chips_in_graph
