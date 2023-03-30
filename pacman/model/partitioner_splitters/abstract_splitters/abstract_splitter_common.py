# Copyright (c) 2020 The University of Manchester
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
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.exceptions import PacmanConfigurationException


class AbstractSplitterCommon(object, metaclass=AbstractBase):
    """
    Common base class for vertex splitters, defining some utility methods.
    """

    __slots__ = [
        # the app vertex this splitter governs.
        "_governed_app_vertex",
    ]

    FIX_ATOMS_RESET = (
        "Illegal attempt to set fixed atoms per core to {} "
        "as it was already set to {}")

    MAX_BELOW_FIXED = (
        "Illegal attempt to set max atoms per core to {} "
        "as that is lower than the previously set fixed of {}")

    FIXED_ABOVE_MAX = (
        "Illegal attempt to set fixed atoms per core to {} "
        "as that is above a previously set max atoms of {}")

    def __init__(self):
        self._governed_app_vertex = None

    def __str__(self):
        try:
            return (
                f"{type(self).__name__} on {self._governed_app_vertex.label}")
        except AttributeError:
            return f"{type(self).__name__} has no governed_app_vertex"

    def __repr__(self):
        return self.__str__()

    @property
    def governed_app_vertex(self):
        """
        The app vertex to be governed by this splitter object.
        If `None`, not yet set.

        :rtype: ~pacman.model.graphs.application.ApplicationVertex
        """
        return self._governed_app_vertex

    def set_governed_app_vertex(self, app_vertex):
        """
        Sets a app vertex to be governed by this splitter object.
        Once set it can't be reset.

        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            the app vertex to govern
        :raises PacmanConfigurationException:
            if the app vertex has already been set.
        """
        if self._governed_app_vertex == app_vertex:
            return
        if self._governed_app_vertex is not None:
            raise PacmanConfigurationException(
                f"The app vertex {self._governed_app_vertex} is already"
                f" governed by this splitter. ")
        self._governed_app_vertex = app_vertex
        app_vertex.splitter = self

    @abstractmethod
    def create_machine_vertices(self, chip_counter):
        """
        Method for specific splitter objects to override.

        :param ~pacman.utilities.utility_objs.ChipCounter chip_counter:
            counter of used chips
        """

    @abstractmethod
    def get_out_going_slices(self):
        """
        The slices of the output vertices.

        :return: list of Slices
        :rtype: list(~pacman.model.graphs.common.Slice)
        """

    @abstractmethod
    def get_in_coming_slices(self):
        """
        The slices of the input vertices.

        :return: list of Slices
        :rtype: list(~pacman.model.graphs.common.Slice)
        """

    @abstractmethod
    def get_out_going_vertices(self, partition_id):
        """
        Get machine pre-vertices.

        The output vertices are the ones that will serve as source vertices
        for external edges.

        :param str partition_id: The identifier of the outgoing partition
        :rtype: list(~pacman.model.graphs.machine.MachineVertex)
        """

    @abstractmethod
    def get_in_coming_vertices(self, partition_id):
        """
        Get machine post-vertices for a given partition.

        The input vertices are the ones that will serve as target vertices
        for external edges.

        .. note::
            This method returns all that could be used
            for any source machine vertex in the given partition.

        :param str partition_id: The identifier of the incoming partition
        :rtype: list(~pacman.model.graphs.machine.MachineVertex)
        """

    def get_source_specific_in_coming_vertices(
            self, source_vertex, partition_id):
        """
        Get machine post-vertices for a given source.

        The input vertices are the ones that will serve as target vertices
        for external edges.

        .. note::
            This method allows filtering of the targets
            for a specific source machine vertex.

        This default method makes every machine vertex a target for the source.
        This should be overridden if there are specific machine vertices for
        any given source vertex.

        :param source_vertex: The source to get incoming vertices for
        :type source_vertex: ~pacman.model.graphs.application.ApplicationVertex
        :param str partition_id: The identifier of the incoming partition
        :return: A list of tuples of (target machine vertex, list of source
            machine or application vertices that should hit the target)
        :rtype: list(tuple(~pacman.model.graphs.machine.MachineVertex,
            list(~pacman.model.graphs.machine.MachineVertex or
            ~pacman.model.graphs.application.ApplicationVertex)))
        """
        return [(m_vertex, [source_vertex])
                for m_vertex in self.get_in_coming_vertices(partition_id)]

    @abstractmethod
    def machine_vertices_for_recording(self, variable_to_record):
        """
        Gets the machine vertices which are recording this variable.

        :param str variable_to_record: the variable to get machine verts for.
        :return: list of machine vertices
        :rtype: iterable(~pacman.model.graphs.machine.MachineVertex)
        """

    @abstractmethod
    def reset_called(self):
        """
        Reset the splitter to be as if it has not operated a splitting yet.
        """

    def get_same_chip_groups(self):
        """
        Get a list of lists of vertices and sdram which must be
        allocated on the same chip.  By default this returns a list of each
        machine vertex and its SDRAM; override if there are groups of
        machine vertices on the same chip.

        :rtype: list(list(~pacman.model.graphs.machine.MachineVertex),
            ~pacman.model.resources.AbstractSDRAM)
        """
        return [([v], v.sdram_required)
                for v in self._governed_app_vertex.machine_vertices]

    def get_internal_multicast_partitions(self):
        """
        Get edge partitions between machine vertices that are to be
        handled by Multicast.  Returns empty by default, override if there
        are Multicast connections between internal vertices

        :rtype: list(~pacman.model.graphs.machine.MulticastEdgePartition)
        """
        return []

    def get_internal_sdram_partitions(self):
        """
        Get edge partitions between machine vertices that are to be
        handled by SDRAM.  Returns empty by default, override if there
        are SDRAM connections between internal vertices

        :rtype: list(~pacman.model.graphs.machine.AbstractSDRAMPartition)
        """
        return []
