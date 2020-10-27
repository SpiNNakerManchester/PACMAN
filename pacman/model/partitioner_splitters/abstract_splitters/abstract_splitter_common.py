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
from collections import OrderedDict

from six import add_metaclass
from pacman.exceptions import PacmanConfigurationException
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint, FixedVertexAtomsConstraint,
    AbstractPartitionerConstraint)
from pacman.utilities import utility_calls
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSplitterCommon(object):

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

    SETTING_SPLITTER_ERROR_MSG = (
        "The app vertex {} is already governed by this "
        "{}. And so cannot govern app vertex {}."
        " Please fix and try again.")

    STR_MESSAGE = "{} governing app vertex {}"

    FIX_ATOMS_RESET = (
        "Illegal attempt to set fixed atoms per core to {} "
        "as it was already set to {}")

    MAX_BELOW_FIXED = (
        "Illegal attempt to set max atoms per core to {} "
        "as that is lower than the previously set fixed of {}")

    FIXED_ABOVE_MAX = (
        "Illegal attempt to set fixed atoms per core to {} "
        "as that is abve a previously set max atoms of {}")

    DEFAULT_SPLITTER_NAME = "AbstractSplitterCommon"

    def __init__(self, splitter_name=None):
        if splitter_name is None:
            splitter_name = self.DEFAULT_SPLITTER_NAME
        self._splitter_name = splitter_name
        self._max_atoms_per_core = sys.maxsize
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
        """
        result = OrderedDict()
        for vertex in self._governed_app_vertex.machine_vertices:
            result[vertex] = edge_types
        return result

    def set_max_atoms_per_core(self, max_atoms_per_core, is_fixed_atoms):
        """ sets max atoms per core for this splitter object

        :param max_atoms_per_core: max atoms per core for this splitter.
        :param is_fixed_atoms: is this a hard constraint or soft.
        :rtype: None
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
        return self._governed_app_vertex

    def set_governed_app_vertex(self, app_vertex):
        """ sets a app vertex to be governed by this splitter object.
        Once set it cant be reset

        :param app_vertex: the app vertex to govern
        :rtype: None
        :raises PacmanConfigurationException if the app vertex has already\
            been set.
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
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=[self._governed_app_vertex],
            supported_constraints=[
                MaxVertexAtomsConstraint, FixedVertexAtomsConstraint],
            abstract_constraint_type=AbstractPartitionerConstraint)

    def split(self, resource_tracker, machine_graph):
        """ executes splitting

        :param ResourceTracker resource_tracker: machine resources
        :param MachineGraph machine_graph: machine graph
        :return: bool true if successful, false otherwise
        """
        return self.create_machine_vertices(resource_tracker, machine_graph)

    @abstractmethod
    def create_machine_vertices(self, resource_tracker, machine_graph):
        """ method for specific splitter objects to use.

        :param resource_tracker:
        :param machine_graph:
        :return: bool true if successful, false otherwise
        """

    @abstractmethod
    def get_out_going_slices(self):
        """ allows a application vertex to control the set of slices for \
        outgoing application edges
        :return: list of Slices and bool of estimate or not
        :rtype: tuple(list(Slice), bool
        """

    @abstractmethod
    def get_in_coming_slices(self):
        """ allows a application vertex to control the set of slices for \
        incoming application edges
        :return: the slices incoming to this vertex, bool if estimate or exact
        :rtype: tuple(list(Slice), bool
        """

    @abstractmethod
    def get_pre_vertices(self, edge, outgoing_edge_partition):
        """ gets pre vertices and their acceptable edge types
        :param ApplicationEdge edge: app edge
        :param OutgoingEdgePartition outgoing_edge_partition: \
            outgoing edge partition
        :return: dict of keys being machine vertices and values are a list
        of acceptable edge types.
        """

    @abstractmethod
    def get_post_vertices(self, edge, outgoing_edge_partition,
                          src_machine_vertex):
        """ gets incoming vertices and their acceptable edge types
        :param ApplicationEdge edge: app edge
        :param OutgoingEdgePartition outgoing_edge_partition: \
            outgoing edge partition
        :param MachineVertex src_machine_vertex: the src machine vertex
        :return: dict of keys being machine vertices and values are a list
        of acceptable edge types.
        """

    @abstractmethod
    def machine_vertices_for_recording(self, variable_to_record):
        """ returns the machine vertices which are recording this variable.

        :param variable_to_record: the variable to get machine verts for.
        :return: list of machine vertices
        :rtype iterable of <MachineVertex>
        """

    @abstractmethod
    def reset_called(self):
        """ reset the splitter as if it has not operated a splitting yet.

        :rtype: None
        """
