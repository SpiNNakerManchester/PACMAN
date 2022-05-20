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
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.exceptions import PacmanConfigurationException
from pacman.model.constraints.partitioner_constraints import (
    AbstractPartitionerConstraint)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)


class AbstractSplitterCommon(object, metaclass=AbstractBase):

    __slots__ = [
        # the app vertex this splitter governs.
        "_governed_app_vertex",

        # the name of this splitter object, for human readability.
        "_splitter_name",

        # bool flag that says that the constraint is fixed or soft.
        "_is_fixed_atoms_per_core"
    ]

    SETTING_SPLITTER_ERROR_MSG = (
        "The app vertex {} is already governed by this {}. "
        "And so cannot govern app vertex {}. Please fix and try again.")

    STR_MESSAGE = "{} governing app vertex {}"

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
        self._is_fixed_atoms_per_core = False
        self._governed_app_vertex = None

    def __str__(self):
        return self.STR_MESSAGE.format(
            self._splitter_name, self._governed_app_vertex)

    def __repr__(self):
        return self.__str__()

    def _get_map(self, edge_types):
        """ builds map of machine vertex to edge type

        :param edge_types: the type of edges to add to the dict.
        :return: dict of vertex as key, edge types as list in value
        :rtype: dict(MachineVertex, EdgeType)
        """
        result = dict()
        for vertex in self._governed_app_vertex.machine_vertices:
            result[vertex] = edge_types
        return result

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
                self.SETTING_SPLITTER_ERROR_MSG.format(
                    self._governed_app_vertex, self._splitter_name,
                    app_vertex))
        self._governed_app_vertex = app_vertex
        self.check_supported_constraints()
        app_vertex.splitter = self

    def check_supported_constraints(self):
        """
        :raise PacmanInvalidParameterException:
            When partitioner constraints are used.
        """
        check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[],
            abstract_constraint_type=AbstractPartitionerConstraint)

    def split(self, resource_tracker, machine_graph):
        """ executes splitting

        :param ~pacman.utilities.utility_objs.ResourceTracker resource_tracker:
            machine resources
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            machine graph
        :return: true if successful, false otherwise
        :rtype: bool
        """
        return self.create_machine_vertices(resource_tracker, machine_graph)

    @abstractmethod
    def create_machine_vertices(self, resource_tracker, machine_graph):
        """ method for specific splitter objects to use.

        :param ~pacman.utilities.utility_objs.ResourceTracker resource_tracker:
            machine resources
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            machine graph
        :return: true if successful, false otherwise
        :rtype: bool
        """

    @abstractmethod
    def get_out_going_slices(self):
        """ A best effort prediction of the slices of the output vertices.

        If this method is called after create_machine_vertices the splitter
        should return the actual slices of the output vertices.
        The second value returned is then always ``True``

        If this method is called before create_machine_vertices the splitter
        will have to make an estimate unless the actual slices it will use are
        already known. The second value returned is ``True`` if and only if
        the slices will not be changed.

        The output vertices are the ones that will serve as source vertices
        for external edges.  If more than one set of vertices match this
        description the splitter should use the ones used by the most general
        edge type/down-stream splitter.

        :return: list of Slices and bool of estimate or not
        :rtype: tuple(list(~pacman.model.graphs.common.Slice), bool)
        """

    @abstractmethod
    def get_in_coming_slices(self):
        """ A best effort prediction of the slices of the input vertices.

        If this method is called after create_machine_vertices the splitter
        should return the actual slices of the input vertices.
        The second value returned is then always ``True``

        If this method is called before create_machine_vertices the splitter
        will have to make an estimate unless the actual slices it will use are
        already known. The second value returned is ``True`` if and only if
        the slices will not be changed.

        The output vertices are the ones that will serve as source vertices
        for external edges.  If more than one set of vertices match this
        description the splitter should use the ones used by the most general
        edge type/ down stream splitter.

        :return: the slices incoming to this vertex, bool if estimate or exact
        :rtype: tuple(list(~pacman.model.graphs.common.Slice), bool)
        """

    @abstractmethod
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        """ gets pre vertices and their acceptable edge types

        The output vertices are the ones that will serve as source vertices
        for external edges.  If more than one set of vertices match this
        description the splitter should use the ones used by the most general
        edge type/ down stream splitter.

        :param ~pacman.model.graphs.application.ApplicationEdge edge: app edge
        :param outgoing_edge_partition: outgoing edge partition
        :type outgoing_edge_partition:
            ~pacman.model.graphs.OutgoingEdgePartition
        :return: dict of keys being machine vertices and values are a list
            of acceptable edge types.
        :rtype: dict(~pacman.model.graphs.machine.MachineVertex,list(class))
        """

    @abstractmethod
    def get_in_coming_vertices(self, edge, outgoing_edge_partition,
                               src_machine_vertex):
        """ gets incoming vertices and their acceptable edge types

        The input vertices are the ones that will serve as dest vertices
        for external edges.  If more than one set of vertices match this
        description the splitter should use the ones used by the most general
        edge type/ down stream splitter.

        :param ~pacman.model.graphs.application.ApplicationEdge edge: app edge
        :param outgoing_edge_partition: outgoing edge partition
        :type outgoing_edge_partition:
            ~pacman.model.graphs.OutgoingEdgePartition
        :param ~pacman.model.graphs.machine.MachineVertex src_machine_vertex:
            the src machine vertex
        :return: dict of keys being machine vertices and values are a list
            of acceptable edge types.
        :rtype: dict(~pacman.model.graphs.machine.MachineVertex,list(class))
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
