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
from spinn_utilities.data.data_status import Data_Status
from spinn_utilities.log import FormatAdapter
from spinn_utilities.exceptions import DataLocked
from spinn_machine.data import MachineDataView
from pacman.exceptions import PacmanNotPlacedError
from pacman.model.routing_info import (
    DictBasedMachinePartitionNKeysMap)

logger = FormatAdapter(logging.getLogger(__name__))


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
        "_machine_graph",
        "_machine_partition_n_keys_map",
        "_placements",
        "_router_tables",
        "_routing_infos",
        "_runtime_graph",
        "_runtime_machine_graph",
        "_tags"
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
        self._machine_graph = None
        self._hard_reset()

    def _hard_reset(self):
        """
        Clears out all data that should change after a reset and graaph change
        """
        self._placements = None
        self._router_tables = None
        self._runtime_graph = None
        self._runtime_machine_graph = None
        self._routing_infos = None
        self._machine_partition_n_keys_map = None
        self._tags = None
        self._soft_reset()

    def _soft_reset(self):
        """
        Clears timing and other data that should changed every reset
        """
        # Holder for any later additions


class PacmanDataView(MachineDataView):
    """
    A read only view of the data available at Pacman level

    The objects accessed this way should not be changed or added to.
    Changing or adding to any object accessed if unsupported as bypasses any
    check or updates done in the writer(s).
    Objects returned could be changed to immutable versions without notice!

    The get methods will return either the value if known or a None.
    This is the faster way to access the data but lacks the safety.

    The property methods will either return a valid value or
    raise an Exception if the data is currently not available.
    These are typically semantic sugar around the get methods.

    The has methods will return True is the value is known and False if not.
    Semantically the are the same as checking if the get returns a None.
    They may be faster if the object needs to be generated on the fly or
    protected to be made immutable.

    While how and where the underpinning DataModel(s) store data can change
    without notice, methods in this class can be considered a supported API
    """

    __pacman_data = _PacmanDataModel()
    __slots__ = []

    # graph methods

    @classmethod
    def get_graph(cls):
        """
        The user level application graph

        This is the version of the graph which is created by the user / script
        Previously known as asb._original_application_graph.

        Changes to this graph will only affect the next run

        :rtype: ApplicationGraph
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the graph is currently unavailable, or if this method
            is used during run
        """
        if cls.__pacman_data._graph is None:
            raise cls._exception("graph")
        # The writer overrides this method without this safety
        if cls.get_status() in [Data_Status.IN_RUN, Data_Status.STOPPING]:
            raise DataLocked("graph", cls.get_status())
        return cls.__pacman_data._graph

    @classmethod
    def get_machine_graph(cls):
        """
        The user level machine graph

        Previously known as asb._original_machine_graph.

       Changes to this graph will only affect the next run

        :rtype: MachineGraph
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the machine_graph is currently unavailable, or if this method
            is used during run
        """
        if cls.__pacman_data._machine_graph is None:
            raise cls._exception("machine_graph")
        # The writer overrides this method without this safety
        if cls.get_status() in [Data_Status.IN_RUN, Data_Status.STOPPING]:
            raise DataLocked("machine_graph", cls.get_status())
        return cls.__pacman_data._machine_graph

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
            The graph returned by this method may be immutable depending on
            when it is called

        :rtype: ApplicationGraph
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the runtime_graph is currently unavailable, or if this method
            is used except during run
        """
        if cls.__pacman_data._runtime_graph is None:
            raise cls._exception("runtime_graph")
        if cls.get_status() not in [
                Data_Status.IN_RUN, Data_Status.MOCKED, Data_Status.STOPPING]:
            if cls.get_status() == Data_Status.FINISHED:
                logger.warning(
                    "The runtime_graph is from the previous run and "
                    "may change during the next run")
            else:
                raise DataLocked("runtime_graph", cls.get_status())
        return cls.__pacman_data._runtime_graph

    @classmethod
    def get_runtime_machine_graph(cls):
        """
        The runtime machine graph

        This is the run time version of the graph which is created by the
        simulator to add system vertices.

        Changes to this graph by anything except the insert algorithms is not
        supported.

         .. note::
            The graph returned by this method may be immutable depending on
            when it is called

        :rtype: MachineGraph
        :raises SpiNNUtilsException:
            If the runtime_graph is currently unavailable, or if this method
            is used except during run
        """
        if cls.__pacman_data._runtime_machine_graph is None:
            raise cls._exception("runtime_machine_graph")
        if cls.get_status() not in [
                Data_Status.IN_RUN, Data_Status.MOCKED, Data_Status.STOPPING]:
            if cls.get_status() == Data_Status.FINISHED:
                logger.warning(
                    "The runtime_machine_graph is from the previous run and "
                    "may change during the next run")
            else:
                raise DataLocked("runtime_machine_graph", cls.get_status())
        return cls.__pacman_data._runtime_machine_graph

    @classmethod
    def get_runtime_n_machine_vertices(cls):
        """
        The number of machine vertices in the runtime graph(s)

         .. note::
            This method can still exists without a machine_graph

        :rtype: int
        """
        return cls.get_runtime_machine_graph().n_vertices

    @classmethod
    def get_runtime_n_machine_vertices2(cls):
        return sum(len(vertex.machine_vertices)
                   for vertex in cls.get_runtime_graph().vertices)

    @classmethod
    def get_runtime_machine_vertices(cls):
        """
        The machine vertices in the runtime graph(s)

         .. note::
            This method can still exists without a machine_graph

        :rtype: iterator(MachineVertex)
        """
        return cls.get_runtime_machine_graph().vertices

    @classmethod
    def get_runtime_machine_vertices2(cls):
        for app_vertex in cls.get_runtime_graph().vertices:
            yield from app_vertex.machine_vertices

    @classmethod
    def get_runtime_best_graph(cls):
        """
        The runtime application graph unless it is empty and the
        machine graph one is not

        This is the run time version of the graph which is created by the
        simulator to add system vertices.

        Changes to this graph by anything except the insert algorithms is not
        supported.

         .. note::
            The graph returned by this method may be immutable depending on
            when it is called

        :rtype: ApplicationGraph or MachineGraph
        :raises ~spinn_utilities.exceptions.SpiNNUtilsException:
            If the runtime_graph is currently unavailable, or if this method
            is used except during run
        """
        try:
            runtime_graph = cls.get_runtime_graph()
            if runtime_graph.n_vertices:
                return runtime_graph
        except Exception:
            # In mocked there may only be a machine_graph
            if cls.get_status() != Data_Status.MOCKED:
                raise
        runtime_machine_graph = cls.get_runtime_machine_graph()
        if runtime_machine_graph.n_vertices:
            return runtime_machine_graph
        # both empty for return the application level
        return cls.get_runtime_graph()

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

    # MachinePartitionNKeysMap

    @classmethod
    def get_machine_partition_n_keys_map(cls):
        if cls.__pacman_data._machine_partition_n_keys_map is None:
            if cls.get_status() == Data_Status.MOCKED:
                cls.__pacman_data._machine_partition_n_keys_map = \
                    DictBasedMachinePartitionNKeysMap()
            else:
                raise cls._exception("machine_partition_n_keys_map")
        return cls.__pacman_data._machine_partition_n_keys_map

    # RoutingTables

    @classmethod
    def get_router_tables(cls):
        if cls.__pacman_data._router_tables is None:
            raise cls._exception("router_tables")
        return cls.__pacman_data._router_tables
