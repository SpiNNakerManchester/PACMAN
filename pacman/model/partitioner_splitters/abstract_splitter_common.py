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
from typing import (
    Iterable, Generic, Optional, Sequence, Tuple, TypeVar)
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.utilities.utility_objs import ChipCounter
from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import (
    MachineVertex, MulticastEdgePartition, AbstractSDRAMPartition)
from pacman.model.resources import AbstractSDRAM

#: The type of vertex that we split.
#: :meta private:
V = TypeVar("V", bound=ApplicationVertex)


class AbstractSplitterCommon(Generic[V], metaclass=AbstractBase):
    """
    Common base class for vertex splitters, defining some utility methods.
    """

    __slots__ = (
        # the app vertex this splitter governs.
        "__governed_app_vertex", )

    def __init__(self) -> None:
        self.__governed_app_vertex: Optional[V] = None

    def __str__(self) -> str:
        try:
            if self.__governed_app_vertex is None:
                return (
                    f"{type(self).__name__} without an app vertex")
            return (
                f"{type(self).__name__} on {self.__governed_app_vertex.label}")
        except AttributeError:
            return f"{type(self).__name__} has no governed_app_vertex"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def governed_app_vertex(self) -> V:
        """
        The app vertex to be governed by this splitter object.

        :raises PacmanConfigurationException:
            if the app vertex has not been been set.
        """
        if self.__governed_app_vertex is None:
            raise PacmanConfigurationException(
                "This splitter has no governing app vertex set")
        return self.__governed_app_vertex

    def set_governed_app_vertex(self, app_vertex: V) -> None:
        """
        Sets a application vertex to be governed by this splitter object.
        Once set it can't be reset.

        :param app_vertex:
            the app vertex to govern
        :raises PacmanConfigurationException:
            if the app vertex has already been set.
        """
        if self.__governed_app_vertex == app_vertex:
            return
        if self.__governed_app_vertex is not None:
            raise PacmanConfigurationException(
                f"The app vertex {self.__governed_app_vertex} is already"
                f" governed by this splitter. ")
        self.__governed_app_vertex = app_vertex
        app_vertex.splitter = self

    @abstractmethod
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        """
        Method for specific splitter objects to override.

        :param chip_counter: counter of used chips
        """
        raise NotImplementedError

    @abstractmethod
    def get_out_going_slices(self) -> Sequence[Slice]:
        """
        The slices of the output vertices.

        :return: list of Slices
        """
        raise NotImplementedError

    @abstractmethod
    def get_in_coming_slices(self) -> Sequence[Slice]:
        """
        The slices of the input vertices.

        :return: list of Slices
        """
        raise NotImplementedError

    @abstractmethod
    def get_out_going_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        """
        Get machine pre-vertices.

        The output vertices are the ones that will serve as source vertices
        for external edges.

        :param partition_id: The identifier of the outgoing partition
        :returns:  machine pre-vertices for this partition
        """
        raise NotImplementedError

    @abstractmethod
    def get_in_coming_vertices(
            self, partition_id: str) -> Sequence[MachineVertex]:
        """
        Get machine post-vertices for a given partition.

        The input vertices are the ones that will serve as target vertices
        for external edges.

        .. note::
            This method returns all that could be used
            for any source machine vertex in the given partition.

        :param partition_id: The identifier of the incoming partition
        :returns: machine post-vertices for a given partition
        """
        raise NotImplementedError

    def get_source_specific_in_coming_vertices(
            self, source_vertex: ApplicationVertex,
            partition_id: str) -> Sequence[Tuple[
                MachineVertex, Sequence[AbstractVertex]]]:
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
        :param partition_id: The identifier of the incoming partition
        :return: A list of tuples of (target machine vertex, list of source
            machine or application vertices that should hit the target)
        """
        return [(m_vertex, [source_vertex])
                for m_vertex in self.get_in_coming_vertices(partition_id)]

    @abstractmethod
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Iterable[MachineVertex]:
        """
        Gets the machine vertices which are recording this variable.

        :param variable_to_record:
            the variable to get machine vertices for.
        :return: list of machine vertices
        """
        raise NotImplementedError

    @abstractmethod
    def reset_called(self) -> None:
        """
        Reset the splitter to be as if it has not operated a splitting yet.
        """
        raise NotImplementedError

    def get_same_chip_groups(self) -> Sequence[
            Tuple[Sequence[MachineVertex], AbstractSDRAM]]:
        """
        Get a list of lists of vertices and SDRAM which must be
        allocated on the same chip.

        By default this returns a list of each
        machine vertex and its SDRAM; override if there are groups of
        machine vertices on the same chip.

        :returns: A list of vertices and
           the SDRAM cost that should be counted for that Vertex.
        """
        return [([v], v.sdram_required)
                for v in self.governed_app_vertex.machine_vertices]

    def get_internal_multicast_partitions(
            self) -> Sequence[MulticastEdgePartition]:
        """
        Get edge partitions between machine vertices that are to be
        handled by Multicast.

        Returns empty by default,
        override if there are Multicast connections between internal vertices

        :returns: Only the partitions (if any) handled by Multicast
        """
        return []

    def get_internal_sdram_partitions(
            self) -> Sequence[AbstractSDRAMPartition]:
        """
        Get edge partitions between machine vertices that are to be
        handled by SDRAM.

        Returns empty by default, override if there
        are SDRAM connections between internal vertices

        :returns: Only the partitions (if any) handled by SDRAM
        """
        return []
