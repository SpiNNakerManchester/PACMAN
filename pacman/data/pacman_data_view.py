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
from spinn_machine.data import MachineDataView
from pacman.exceptions import PacmanNotPlacedError
from pacman.model.graphs.application import ApplicationGraph

logger = FormatAdapter(logging.getLogger(__name__))
# pylint: disable=protected-access


class _PacmanDataModel(object):
    """
    Singleton data model

    This class should not be accessed directly please use the DataView and
    DataWriter classes.
    Accessing or editing the data held here directly is NOT SUPPORTED

    There may be other DataModel classes which sit next to this one and hold
    additional data. The DataView and DataWriter classes will combine these
    as needed.

    What data is held where and how can change without notice.
    """

    __singleton = None

    __slots__ = [
        # Data values cached
        "_graph",
        "_placements",
        "_plan_n_timesteps",
        "_precompressed",
        "_routing_infos",
        "_routing_table_by_partition",
        "_runtime_graph",
        "_tags",
        "_uncompressed",
        "_vertices_or_edges_added",
    ]

    def __new__(cls):
        if cls.__singleton:
            return cls.__singleton
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        cls.__singleton = obj
        obj._clear()
        return obj

    def _clear(self):
        """
        Clears out all data
        """
        self._graph = None
        # set at the start of every run
        self._plan_n_timesteps = None
        self._vertices_or_edges_added = False
        self._hard_reset()

    def _hard_reset(self):
        """
        Clears out all data that should change after a reset and graph change
        """
        self._placements = None
        self._precompressed = None
        self._uncompressed = None
        self._runtime_graph = None
        self._routing_infos = None
        self._routing_table_by_partition = None
        self._tags = None
        self._soft_reset()

    def _soft_reset(self):
        """
        Clears timing and other data that should changed every reset
        """
        # Holder for any later additions


class PacmanDataView(MachineDataView):
    """
    Adds the extra Methods to the View for pacman level.

    See UtilsDataView for a more detailed description.

    This class is designed to only be used directly within the PACMAN
    repository as all methods are available to subclasses
    """

    __pacman_data = _PacmanDataModel()
    __slots__ = []

    # graph methods

    @classmethod
    def has_application_vertices(cls):
        """
        Reports if the user level graph has application vertices.

        Semantic sugar for get_graph().n_vertices

        :return: True if and only if the Application Graph has vertices.
        :rtype: bool
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        return cls.__pacman_data._graph.n_vertices > 0

    @classmethod
    def get_edges_ending_at_vertex(cls, vertex):
        """ Get all the edges that end at the given vertex in the user graph

        Semantic sugar for get_graph().get_edges_ending_at_vertex

        :param AbstractVertex vertex:
            The vertex at which the edges to get end
        :rtype: iterable(AbstractEdge)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        return cls.__pacman_data._graph.get_edges_ending_at_vertex(vertex)

    @classmethod
    def add_vertex(cls, vertex):
        """
        Adds an Application vertex to the user graph

        Semantic sugar for get_graph().add_vertex

        :param ~pacman.model.graphs.application.ApplicationVertex vertex:
            The vertex to add to the graph
        :raises PacmanConfigurationException:
            when both graphs contain vertices
        :raises PacmanConfigurationException:
            If there is an attempt to add the same vertex more than once
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        :raises SimulatorRunningException: If sim.run is currently running
        :raises SimulatorNotSetupException: If called before sim.setup
        :raises SimulatorShutdownException: If called after sim.end
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        cls.check_user_can_act()
        cls.__pacman_data._graph.add_vertex(vertex)
        cls.__pacman_data._vertices_or_edges_added = True

    @classmethod
    def add_edge(cls, edge, outgoing_edge_partition_name):
        """
        Adds an Application edge to the user graph

        Semantic sugar for get_graph().add_edge

        :param AbstractEdge edge: The edge to add
        :param str outgoing_edge_partition_name:
            The name of the edge partition to add the edge to; each edge
            partition is the partition of edges that start at the same vertex
        :rtype: AbstractEdgePartition
        :raises PacmanConfigurationException:
            when both graphs contain vertices
        :raises PacmanInvalidParameterException:
            If the edge is not of a valid type or if edges have already been
            added to this partition that start at a different vertex to this
            one
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        :raises SimulatorRunningException: If sim.run is currently running
        :raises SimulatorNotSetupException: If called before sim.setup
        :raises SimulatorShutdownException: If called after sim.end
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        cls.check_user_can_act()
        cls.__pacman_data._graph.add_edge(edge, outgoing_edge_partition_name)
        cls.__pacman_data._vertices_or_edges_added = True

    @classmethod
    def iterate_vertices(cls):
        """ The vertices in the user application graph.

        Semantic sugar for get_graph().vertices except that the result is an
        iterable and not a list

        :rtype: iterable(AbstractVertex)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        return iter(cls.__pacman_data._graph.vertices)

    @classmethod
    def get_n_vertices(cls):
        """ The number of vertices in the user application graph.

        Semantic sugar for get_graph().n_vertices

        :rtype: int
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        return cls.__pacman_data._graph.n_vertices

    @classmethod
    def iterate_partitions(cls):
        """ The partitions in the user application graph.

        Semantic sugar for get_graph().outgoing_edge_partitions

        :rtype: iterable(ApplicationEdgePartition)
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        return cls.__pacman_data._graph.outgoing_edge_partitions

    @classmethod
    def get_n_partitions(cls):
        """ The partitions in the user application graph.

        Semantic sugar for get_graph().n_outgoing_edge_partitions

        :rtype: int
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        return cls.__pacman_data._graph.n_outgoing_edge_partitions

    @classmethod
    def get_outgoing_edge_partitions_starting_at_vertex(cls, vertex):
        """ Get all the edge partitions that start at the given vertex.

        Semantic sugar for get_graph().
        get_outgoing_edge_partitions_starting_at_vertex

        :param AbstractVertex vertex:
            The vertex at which the edge partitions to find starts
        :rtype: iterable(AbstractEdgePartition)
        """
        if cls.__pacman_data._graph is None:
            if cls._is_mocked():
                cls.__pacman_data._graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("graph")
        return cls.__pacman_data._graph.\
            get_outgoing_edge_partitions_starting_at_vertex(vertex)

    @classmethod
    def get_runtime_graph(cls):
        """
        The runtime application graph

        This is the run time version of the graph which is created by the
        simulator to add system vertices.
        Previously known as asb.application_graph.

        Changes to this graph by anything except the insert algorithms is not
        supported.

         .. note::
            This method is likely to be removed by another PR.
            If not it will be replaced with add and iterate methods.

        :rtype: ApplicationGraph
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the runtime_graph is currently unavailable, or if this method
            is used except during run
        """
        if cls.__pacman_data._runtime_graph is None:
            if cls._is_mocked():
                if cls.__pacman_data._graph is None:
                    raise cls._exception("graph")
                cls.__pacman_data._runtime_graph = cls.__pacman_data._graph
            else:
                raise cls._exception("runtime_graph")
        return cls.__pacman_data._runtime_graph

    @classmethod
    def get_runtime_n_machine_vertices(cls):
        """
        Gets the number of machine vertices via the application graph
        """
        if cls.__pacman_data._runtime_graph is None:
            if cls._is_mocked():
                cls.__pacman_data._runtime_graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("runtime_graph")
        return sum(len(vertex.machine_vertices)
                   for vertex in cls.get_runtime_graph().vertices)

    @classmethod
    def get_runtime_machine_vertices(cls):
        """
        Gets the Machine vertioces viua the application graph

        :return:
        """
        if cls.__pacman_data._runtime_graph is None:
            if cls._is_mocked():
                cls.__pacman_data._runtime_graph = ApplicationGraph("Mocked")
            else:
                raise cls._exception("runtime_graph")
        for app_vertex in cls.get_runtime_graph().vertices:
            yield from app_vertex.machine_vertices

    @classmethod
    def get_vertices_or_edges_added(cls):
        """
        Detects if any vertex of edge has been added since the last run

        If this methods returns True a hard reset is guranteed to be needed.
        However as there are other reasons to require a hard reset a
        False does not imply one is not needed.

        :rtype: bool
        """
        return cls.__pacman_data._vertices_or_edges_added

    # placements

    @classmethod
    def get_placements(cls):
        """
        The placements if known

        :rtype: ~pacman.model.placements.Placements
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the placements is currently unavailable
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements

    @classmethod
    def iterate_placemements(cls):
        """
        Iterates over the Placement objects

        Semantic sugar for get_placement_placements

        :return:
        """
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.placements

    @classmethod
    def get_n_placements(cls):
        if cls.__pacman_data._placements is None:
            raise cls._exception("placements")
        return cls.__pacman_data._placements.n_placements

    @classmethod
    def get_placement_of_vertex(cls, vertex):
        """ Return the placement information for a vertex

        Semantic sugar for get_placements().get_placement_of_vertex(vertex)
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

    # routing_infos

    @classmethod
    def get_routing_infos(cls):
        """
        The routing_infos if known

        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the routing_infos is currently unavailable
        """
        if cls.__pacman_data._routing_infos is None:
            raise cls._exception("routing_infos")
        return cls.__pacman_data._routing_infos

    # tags

    @classmethod
    def get_tags(cls):
        """
        The Tags object of known

        :rtype: ~pacman.model.tags.Tags
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the tags is currently unavailable
        """
        if cls.__pacman_data._tags is None:
            raise cls._exception("tags")
        return cls.__pacman_data._tags

    # RoutingTables

    @classmethod
    def get_uncompressed(cls):
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
    def get_precompressed(cls):
        """
        Get the pre compressed routing tables.

        This may be the same object as the uncompressed ones if
        precompression is skip or determined not needed.

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
    def get_plan_n_timestep(cls):
        """
        The number of timesets to plan for.

        Use by partitioners and such but not to reserve data regions

        :rtype: int or None
        :return: The plan n timesteps for None if run forever
        """
        return cls.__pacman_data._plan_n_timesteps

    @classmethod
    def get_routing_table_by_partition(cls):
        """
        The MulticastRoutingTableByPartition if it has been set

        :rtype: MulticastRoutingTableByPartition
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the tables is currently unavailable
        """
        if cls.__pacman_data._routing_table_by_partition is None:
            raise cls._exception("routing_table_by_partition")
        return cls.__pacman_data._routing_table_by_partition
