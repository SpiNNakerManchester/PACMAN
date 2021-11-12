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
import sys
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.exceptions import PacmanConfigurationException
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
    AbstractPartitionerConstraint)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)


class AbstractSplitterCommon(object, metaclass=AbstractBase):

    __slots__ = [
        # the app vertex this splitter governs.
        "_governed_app_vertex",

        # the name of this splitter object, for human readability.
        "_splitter_name",

        # the max atoms per core demanded by the tools. interpretation of
        # this is at the splitter objects discretion.
        "_max_atoms_per_core",

        # bool flag that says that the constraint is fixed or soft.
        "_is_fixed_atoms_per_core"
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

    DEFAULT_SPLITTER_NAME = "AbstractSplitterCommon"

    def __init__(self, splitter_name=None):
        """
        :param str splitter_name:
        """
        if splitter_name is None:
            splitter_name = self.DEFAULT_SPLITTER_NAME
        self._splitter_name = splitter_name
        self._max_atoms_per_core = sys.maxsize
        self._is_fixed_atoms_per_core = False
        self._governed_app_vertex = None

    def __str__(self):
        return (
            f"{self._splitter_name} governing app vertex"
            f" {self._governed_app_vertex}")

    def __repr__(self):
        return self.__str__()

    def set_max_atoms_per_core(self, max_atoms_per_core, is_fixed_atoms):
        """ sets max atoms per core for this splitter object

        :param int max_atoms_per_core: max atoms per core for this splitter.
        :param bool is_fixed_atoms: is this a hard constraint or soft.
        :raises PacmanConfigurationException:
            If the new setting clash with a previous setting
        """
        if self._is_fixed_atoms_per_core:
            # Already fixed so
            if is_fixed_atoms:
                # as new also fixed they must be the same
                if max_atoms_per_core != self._max_atoms_per_core:
                    raise PacmanConfigurationException(
                        self.FIX_ATOMS_RESET.format(
                            max_atoms_per_core, self._max_atoms_per_core))
                else:
                    return  # No change
            else:
                # as new a max make sure it is not lower than current fixed
                if max_atoms_per_core < self._max_atoms_per_core:
                    raise PacmanConfigurationException(
                        self.MAX_BELOW_FIXED.format(
                            max_atoms_per_core, self._max_atoms_per_core))
                else:
                    return  # OK to ignore the max above the fixed
        else:
            # Currently on a max so
            if is_fixed_atoms:
                # As new is fixed max sure it is not higher than max
                if max_atoms_per_core > self._max_atoms_per_core:
                    raise PacmanConfigurationException(
                        self.FIXED_ABOVE_MAX.format(
                            max_atoms_per_core, self._max_atoms_per_core))
                else:  # Set the new fixed
                    self._max_atoms_per_core = max_atoms_per_core
                    self._is_fixed_atoms_per_core = True
            else:
                # Both max so only change if new max if lower
                if max_atoms_per_core < self._max_atoms_per_core:
                    # Set the new max but leave fixed false
                    self._max_atoms_per_core = max_atoms_per_core
                else:
                    return  # Ok to Ignore a higher or same max

    @property
    def governed_app_vertex(self):
        """
        :rtype: ApplicationVertex
        """
        return self._governed_app_vertex

    def set_governed_app_vertex(self, app_vertex):
        """ Sets a app vertex to be governed by this splitter object. \
            Once set it can't be reset

        :param ApplicationVertex app_vertex: the app vertex to govern
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
        self.check_supported_constraints()
        app_vertex.splitter = self

    def check_supported_constraints(self):
        """
        :raise PacmanInvalidParameterException:
            When partitioner constraints other than
            :py:class:`MaxVertexAtomsConstraint` and
            :py:class:`FixedVertexAtomsConstraint` are used.
        """
        check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)

    @abstractmethod
    def create_machine_vertices(self, chip_counter):
        """ Method for specific splitter objects to override.

        :param ChipCounter chip_counter: counter of used chips
        """

    @abstractmethod
    def get_out_going_slices(self):
        """ The slices of the output vertices.

        :return: list of Slices
        :rtype: list(~pacman.model.graphs.common.Slice)
        """

    @abstractmethod
    def get_in_coming_slices(self):
        """ The slices of the input vertices.

        :return: list of Slices
        :rtype: list(~pacman.model.graphs.common.Slice)
        """

    @abstractmethod
    def get_out_going_vertices(self, outgoing_edge_partition):
        """ Get machine pre vertices

        The output vertices are the ones that will serve as source vertices
        for external edges.

        :param outgoing_edge_partition: outgoing edge partition
        :type outgoing_edge_partition:
            ~pacman.model.graphs.OutgoingEdgePartition
        :rtype: list(MachineVertex)
        """

    @abstractmethod
    def get_in_coming_vertices(self, outgoing_edge_partition):
        """ Get machine post vertices

        The input vertices are the ones that will serve as dest vertices
        for external edges.

        :param outgoing_edge_partition: outgoing edge partition
        :type outgoing_edge_partition:
            ~pacman.model.graphs.OutgoingEdgePartition
        :rtype: list(MachineVertex)
        """

    @abstractmethod
    def machine_vertices_for_recording(self, variable_to_record):
        """ Gets the machine vertices which are recording this variable.

        :param str variable_to_record: the variable to get machine verts for.
        :return: list of machine vertices
        :rtype: iterable(~pacman.model.graphs.machine.MachineVertex)
        """

    @abstractmethod
    def reset_called(self):
        """ reset the splitter to be as if it has not operated a splitting yet.
        """

    def get_same_chip_groups(self):
        """ Get a list of lists of vertices and sdram which must be
            allocated on the same chip.  By default this returns a list of each
            machine vertex and its SDRAM; override if there are groups of
            machine vertices on the same chip.

        :rtype: list(list(MachineVertex), AbstractSDRAM)
        """
        return [([v], v.resources_required.sdram)
                for v in self._governed_app_vertex.machine_vertices]

    def get_internal_multicast_partitions(self):
        """ Get edge partitions between machine vertices that are to be
            handled by Multicast.  Returns empty by default, override if there
            are Multicast connections between internal vertices

        :rtype: list(MulticastEdgePartition)
        """
        return []

    def get_internal_sdram_partitions(self):
        """ Get edge partitions between machine vertices that are to be
            handled by SDRAM.  Returns empty by default, override if there
            are SDRAM connections between internal vertices

        :rtype: list(AbstractSDRAMPartition)
        """
        return []
