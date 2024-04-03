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
from typing import (Iterable, List, Optional, Sequence, Type, TypeVar,
                    TYPE_CHECKING)

from spinn_utilities.log import FormatAdapter
from spinn_utilities.typing.coords import XY

from spinn_machine.data import MachineDataView

from pacman.exceptions import PacmanNotPlacedError
from pacman.model.graphs.application import ApplicationGraph
from pacman.model.resources import AbstractSDRAM, ConstantSDRAM

if TYPE_CHECKING:
    from pacman.model.graphs import AbstractEdgePartition
    from pacman.model.graphs.application import (
        ApplicationEdge, ApplicationEdgePartition, ApplicationVertex)
    from pacman.model.graphs.machine import MachineVertex
    from pacman.model.placements import Placement, Placements
    from pacman.model.tags import Tags
    from pacman.model.routing_info import RoutingInfo
    from pacman.model.routing_tables import MulticastRoutingTables
    from pacman.model.routing_table_by_partition import (
        MulticastRoutingTableByPartition)

    #: Type of a vertex. Can't be constrained for messy reasons.
    #: :meta private:
    VTX = TypeVar("VTX")

logger = FormatAdapter(logging.getLogger(__name__))
# pylint: disable=protected-access


class _PacmanDataModel(object):
    """
    Singleton data model.

    This class should not be accessed directly please use the DataView and
    DataWriter classes.
    Accessing or editing the data held here directly is *not supported!*

    There may be other DataModel classes which sit next to this one and hold
    additional data. The DataView and DataWriter classes will combine these
    as needed.

    What data is held where and how can change without notice.
    """

    __singleton: Optional[_PacmanDataModel] = None

    __slots__ = (
        # Data values cached
        "_graph",
        "_placements",
        "_plan_n_timesteps",
        "_precompressed",
        "_all_monitor_vertices",
        "_all_monitor_cores",
        "_ethernet_monitor_vertices",
        "_ethernet_monitor_cores",
        "_routing_infos",
        "_routing_table_by_partition",
        "_tags",
        "_uncompressed")

    def __new__(cls) -> _PacmanDataModel:
        if cls.__singleton is not None:
            return cls.__singleton
        obj = object.__new__(cls)
        cls.__singleton = obj
        obj._clear()
        return obj

    def _clear(self) -> None:
        """
        Clears out all data.
        """
        self._graph = ApplicationGraph()
        # set at the start of every run
        self._plan_n_timesteps: Optional[int] = None
        self._hard_reset()

    def _hard_reset(self) -> None:
        """
        Clears out all data that should change after a reset and graph change.
        """
        if self._graph:
            self._graph.reset()
        self._placements: Optional[Placements] = None
        self._precompressed: Optional[MulticastRoutingTables] = None
        self._all_monitor_vertices: List[MachineVertex] = []
        self._all_monitor_cores: int = 0
        self._ethernet_monitor_vertices: List[MachineVertex] = []
        self._ethernet_monitor_cores: int = 0
        self._uncompressed: Optional[MulticastRoutingTables] = None
        self._routing_infos: Optional[RoutingInfo] = None
        self._routing_table_by_partition: Optional[
            MulticastRoutingTableByPartition] = None
        self._tags: Optional[Tags] = None
        self._soft_reset()

    def _soft_reset(self) -> None:
        """
        Clears timing and other data that should changed every reset.
        """
        # Holder for any later additions


class PacmanDataView(MachineDataView):
    """
    Adds the extra Methods to the View for PACMAN level.

    See :py:class:`~spinn_utilities.data.UtilsDataView` for a more detailed
    description.

    This class is designed to only be used directly within the PACMAN
    repository as all methods are available to subclasses
    """

    __pacman_data = _PacmanDataModel()
    __slots__ = ()

    # graph methods

    @classmethod
    def add_vertex(cls, vertex: ApplicationVertex):
        """
        Adds an Application vertex to the user graph.

        Syntactic sugar for `get_graph().add_vertex()`

        :param ~pacman.model.graphs.application.ApplicationVertex vertex:
            The vertex to add to the graph
        :raises PacmanConfigurationException:
            when both graphs contain vertices
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        :raises SimulatorNotSetupException: If called before `sim.setup`
        :raises SimulatorShutdownException: If called after `sim.end`
        """
        cls.check_valid_simulator()
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        cls.set_requires_mapping()
        cls.__pacman_data._graph.add_vertex(vertex)

    @classmethod
    def add_edge(
            cls, edge: ApplicationEdge, outgoing_edge_partition_name: str):
        """
        Adds an Application edge to the user graph.

        Syntactic sugar for `get_graph().add_edge()`

        :param AbstractEdge edge: The edge to add
        :param str outgoing_edge_partition_name:
            The name of the edge partition to add the edge to; each edge
            partition is the partition of edges that start at the same vertex
        :raises PacmanConfigurationException:
            when both graphs contain vertices
        :raises PacmanInvalidParameterException:
            If the edge is not of a valid type or if edges have already been
            added to this partition that start at a different vertex to this
            one
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        :raises SimulatorNotSetupException: If called before `sim.setup`
        :raises SimulatorShutdownException: If called after `sim.end`
        """
        cls.check_valid_simulator()
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        cls.set_requires_mapping()
        cls.__pacman_data._graph.add_edge(edge, outgoing_edge_partition_name)

    @classmethod
    def iterate_vertices(cls) -> Iterable[ApplicationVertex]:
        """
        The vertices in the user application graph.

        Syntactic sugar for `get_graph().vertices` except that the result is an
        iterable and not a list.

        :rtype: iterable(AbstractVertex)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        return iter(cls.__pacman_data._graph.vertices)

    @classmethod
    def get_vertices_by_type(
            cls, vertex_type: Type[VTX]) -> Iterable[VTX]:
        """
        The application vertices in the graph of the specific type.

        Syntactic sugar for::

            for vertex in get_graph().vertices
                if isinstance(vertex, vertex_type)
                    ...

        .. note::
            The result is a generator so can only be used in a single loop

        :param vertex_type: The type(s) to filter the vertices on
            (can be anything acceptable to the `isinstance` built-in).
        :type vertex_type: type or iterable(type)
        :rtype: iterable(AbstractVertex)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        for vertex in cls.__pacman_data._graph.vertices:
            if isinstance(vertex, vertex_type):
                yield vertex

    @classmethod
    def get_graph(cls) -> ApplicationGraph:
        return cls.__pacman_data._graph
    @classmethod
    def get_n_vertices(cls) -> int:
        """
        The number of vertices in the user application graph.

        Syntactic sugar for `get_graph().n_vertices`

        :rtype: int
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        return cls.__pacman_data._graph.n_vertices

    @classmethod
    def iterate_partitions(cls) -> Iterable[ApplicationEdgePartition]:
        """
        The partitions in the user application graphs as an iterator.

        Syntactic sugar for `get_graph().outgoing_edge_partitions`

        :rtype: iterable(ApplicationEdgePartition)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        return iter(cls.__pacman_data._graph.outgoing_edge_partitions)

    @classmethod
    def get_n_partitions(cls) -> int:
        """
        The partitions in the user application graph.

        Syntactic sugar for `get_graph().n_outgoing_edge_partitions`

        :rtype: int
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        return cls.__pacman_data._graph.n_outgoing_edge_partitions

    @classmethod
    def get_outgoing_edge_partitions_starting_at_vertex(
            cls, vertex: ApplicationVertex) -> Iterable[AbstractEdgePartition]:
        """
        Get all the edge partitions that start at the given vertex.

        Syntactic sugar for
        `get_graph().get_outgoing_edge_partitions_starting_at_vertex()`

        :param AbstractVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(AbstractEdgePartition)
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        return cls.__pacman_data._graph.\
            get_outgoing_edge_partitions_starting_at_vertex(vertex)

    @classmethod
    def get_edges(cls) -> Sequence[ApplicationEdge]:
        """
        Get all the edges in the graph.

        Syntactic sugar for `get_graph().edges`

        :rtype: list(AbstractEdge)
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        return cls.__pacman_data._graph.edges

    @classmethod
    def get_n_machine_vertices(cls) -> int:
        """
        Gets the number of machine vertices via the application graph.

        :rtype: int
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        return sum(len(vertex.machine_vertices)
                   for vertex in cls.__pacman_data._graph.vertices)

    @classmethod
    def iterate_machine_vertices(cls) -> Iterable[MachineVertex]:
        """
        Iterate over the Machine vertices via the application graph.

        :rtype: iterable(MachineVertex)
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        for app_vertex in cls.__pacman_data._graph.vertices:
            yield from app_vertex.machine_vertices

    # placements

    @classmethod
    def iterate_placemements(cls) -> Iterable[Placement]:
        """
        Iterates over the Placement objects.

        Syntactic sugar for `get_placements().placements`

        :rtype: iterable(Placement)
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.placements

    @classmethod
    def iterate_placements_by_vertex_type(
            cls, vertex_type: Type[VTX]) -> Iterable[Placement]:
        """
        Iterate over placements on any chip with this vertex_type.

        :param type vertex_type: Class of vertex to find
        :rtype: iterable(Placement)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the placements are currently unavailable
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.\
            iterate_placements_by_vertex_type(vertex_type)

    @classmethod
    def iterate_placements_on_core(cls, xy: XY) -> Iterable[Placement]:
        """
        Iterate over placements with this x and y.

        :param tuple(int, int) xy: x and y coordinates to find placements for.
        :rtype: iterable(Placement)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the placements are currently unavailable
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.iterate_placements_on_core(xy)

    @classmethod
    def iterate_placements_by_xy_and_type(
            cls, xy: XY, vertex_type: Type[VTX]) -> Iterable[Placement]:
        """
        Iterate over placements with this x, y and type.

        :param tuple(int, int) xy: x and y coordinates to find placements for.
        :param type vertex_type: Class of vertex to find
        :rtype: iterable(Placement)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the placements are currently unavailable
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.\
            iterate_placements_by_xy_and_type(xy, vertex_type)

    @classmethod
    def get_n_placements(cls) -> int:
        """
        The number of placements.

        :rtype: int
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the placements are currently unavailable
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.n_placements

    @classmethod
    def get_placement_of_vertex(cls, vertex: MachineVertex) -> Placement:
        """
        Return the placement information for a vertex.

        Syntactic sugar for `get_placements().get_placement_of_vertex(vertex)`.
        Optimised for speed

        :param MachineVertex vertex: The vertex to find the placement of
        :return: The placement
        :rtype: Placement
        :raise PacmanNotPlacedError: If the vertex has not been placed.
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the placements is currently unavailable
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        try:
            return cls.__pacman_data._placements._machine_vertices[vertex]
        except KeyError as e:
            raise PacmanNotPlacedError(vertex) from e

    @classmethod
    def get_placement_on_processor(
            cls, x: int, y: int, p: int) -> Placement:
        """
        Get the vertex on a specific processor, or raise an exception
        if the processor has not been allocated.

        :param int x: the X coordinate of the chip
        :param int y: the Y coordinate of the chip
        :param int p: the processor on the chip
        :return: the vertex placed on the given processor
        :rtype: MachineVertex
        :raise PacmanProcessorNotOccupiedError:
            If the processor is not occupied
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the placements are currently unavailable
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.get_placement_on_processor(
            x, y, p)

    # routing_infos

    @classmethod
    def get_routing_infos(cls) -> RoutingInfo:
        """
        The routing information, if known.

        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the routing_infos is currently unavailable
        """
        if cls.__pacman_data._routing_infos is None:
            raise cls._exception("routing_infos")
        return cls.__pacman_data._routing_infos

    # tags

    @classmethod
    def get_tags(cls) -> Tags:
        """
        The Tags object if known.

        :rtype: ~pacman.model.tags.Tags
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the tags is currently unavailable
        """
        if cls.__pacman_data._tags is None:
            raise cls._exception("tags")
        return cls.__pacman_data._tags

    # RoutingTables

    @classmethod
    def get_uncompressed(cls) -> MulticastRoutingTables:
        """
        Get the uncompressed routing tables.

        :rtype: MulticastRoutingTables
        :return: The original routing tables
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the tables is currently unavailable
        """
        if cls.__pacman_data._uncompressed is None:
            raise cls._exception("router_tables")
        return cls.__pacman_data._uncompressed

    @classmethod
    def get_precompressed(cls) -> MulticastRoutingTables:
        """
        Get the pre-compressed routing tables.

        This may be the same object as the uncompressed ones if
        precompression is skipped or determined to be not needed.

        :rtype: MulticastRoutingTables
        :return: The routing tables after the range compressor
            or if not to be run the original tables
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the tables is currently unavailable
        """
        if cls.__pacman_data._precompressed is None:
            raise cls._exception("precompressed_router_tables")
        return cls.__pacman_data._precompressed

    @classmethod
    def get_plan_n_timestep(cls) -> Optional[int]:
        """
        The number of timesteps to plan for in an auto-pause-resume cycle.

        Use by partitioners and such, but not to reserve data regions.

        :rtype: int or None
        :return: The planned number of timesteps, or `None` if run forever.
        """
        return cls.__pacman_data._plan_n_timesteps

    @classmethod
    def get_routing_table_by_partition(
            cls) -> MulticastRoutingTableByPartition:
        """
        The MulticastRoutingTableByPartition, if it has been set.

        :rtype: MulticastRoutingTableByPartition
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the tables is currently unavailable
        """
        if cls.__pacman_data._routing_table_by_partition is None:
            raise cls._exception("routing_table_by_partition")
        return cls.__pacman_data._routing_table_by_partition

    @classmethod
    def get_all_monitor_cores(cls) -> int:
        """
        The number of cores on every chip reported to be used by \
        monitor vertices.

        Ethernet-enabled chips may have more.

        Does not include the system core reserved by the machine/ scamp.

        :rtype: int
        """
        return cls.__pacman_data._all_monitor_cores

    @classmethod
    def get_all_monitor_sdram(cls) -> AbstractSDRAM:
        """
        The amount of SDRAM on every chip reported to be used by \
        monitor vertices.

        Ethernet-enabled chips may have more.

        Does not include the system SDRAM reserved by the machine/scamp.

        :rtype: AbstractSDRAM
        """
        # Note the sdram can not be calculated in advance as some Vertices
        # require the hardware time step not available until simulator run
        sdram = ConstantSDRAM(0)
        for vertex in cls.__pacman_data._all_monitor_vertices:
            sdram += vertex.sdram_required
        return sdram

    @classmethod
    def get_ethernet_monitor_cores(cls) -> int:
        """
        The number of cores on every Ethernet chip reported to be used by \
        monitor vertices.

        This includes the one returned by get_all_monitor_cores unless for
        some reason these are not on Ethernet chips.

        Does not include the system core reserved by the machine/ scamp.

        :rtype: int
        """
        return cls.__pacman_data._ethernet_monitor_cores

    @classmethod
    def get_ethernet_monitor_sdram(cls) -> AbstractSDRAM:
        """
        The amount of SDRAM on every Ethernet chip reported to be used by \
        monitor vertices.

        This includes the SDRAM returned by get_all_monitor_sdram unless for
        some reason these are not on Ethernet chips.

        Does not include the system SDRAM reserved by the machine/scamp.

        :rtype: AbstractSDRAM
        """
        sdram = ConstantSDRAM(0)
        for vertex in cls.__pacman_data._ethernet_monitor_vertices:
            sdram += vertex.sdram_required
        return sdram
