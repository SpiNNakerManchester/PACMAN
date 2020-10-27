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

import sys
from six import add_metaclass
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint)
from pacman.model.graphs import AbstractVertex
from pacman.exceptions import (
    PacmanAlreadyExistsException, PacmanConfigurationException)
from spinn_utilities.overrides import overrides


@add_metaclass(AbstractBase)
class ApplicationVertex(AbstractVertex):
    """ A vertex that can be broken down into a number of smaller vertices
        based on the resources that the vertex requires.
    """

    __slots__ = [
        # list of machine verts associated with this app vertex
        "_machine_vertices",

        # the splitter object associated with this app vertex
        "_splitter"]

    SETTING_SPLITTER_ERROR_MSG = (
        "The splitter object on {} has already been set, it cannot be "
        "reset. Please fix and try again. ")

    def __init__(self, label=None, constraints=None,
                 max_atoms_per_core=sys.maxsize, splitter=None):
        """
        :param str label: The optional name of the vertex.
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex.
        :param int max_atoms_per_core: The max number of atoms that can be
            placed on a core, used in partitioning.
        :param splitter: The splitter object needed for this vertex.
            Leave as None to delegate the choice of splitter to the selector.
        :type splitter None or AbstractSplitterCommon
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        """
        # Need to set to None temporarily as add_constraint checks splitter
        self._splitter = None
        super(ApplicationVertex, self).__init__(label, constraints)
        self._machine_vertices = OrderedSet()

        # Use setter as there is extra work to do
        self.splitter = splitter

        # add a constraint for max partitioning
        self.add_constraint(
            MaxVertexAtomsConstraint(max_atoms_per_core))

    def __str__(self):
        return self.label

    def __repr__(self):
        return "ApplicationVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @property
    def splitter(self):
        """
        :rtype: ~pacman.model.partitioner_interfaces.AbstractSplitterCommon
        """
        return self._splitter

    @splitter.setter
    def splitter(self, new_value):
        """ sets the splitter object. Does not allow repeated settings.

        :param SplitterObjectCommon new_value: the new splitter object
        :rtype: None
        """
        if self._splitter == new_value:
            return
        if self._splitter is not None:
            raise PacmanConfigurationException(
                self.SETTING_SPLITTER_ERROR_MSG.format(self._label))
        self._splitter = new_value
        self._splitter.set_governed_app_vertex(self)
        self._splitter.check_supported_constraints()

    @overrides(AbstractVertex.add_constraint)
    def add_constraint(self, constraint):
        AbstractVertex.add_constraint(self, constraint)
        if self._splitter is not None:
            self._splitter.check_supported_constraints()

    def remember_machine_vertex(self, machine_vertex):
        """
        Adds the Machine vertex the iterable returned by machine_vertices

        This method will be called by MachineVertex.app_vertex
        No other place should call it.

        :param machine_vertex: A pointer to a machine_vertex.
            This vertex may not be fully initialized but will have a slice
        :raises PacmanValueError: If the slice of the machine_vertex is too big
        """

        machine_vertex.index = len(self._machine_vertices)

        if machine_vertex in self._machine_vertices:
            raise PacmanAlreadyExistsException(
                str(machine_vertex), machine_vertex)
        self._machine_vertices.add(machine_vertex)

    @abstractproperty
    def n_atoms(self):
        """ The number of atoms in the vertex

        :rtype: int
        """

    @property
    def machine_vertices(self):
        """ The machine vertices that this application vertex maps to.
            Will be the same length as :py:meth:`vertex_slices`.

        :rtype: iterable(MachineVertex)
        """
        return self._machine_vertices

    @property
    def vertex_slices(self):
        """ The slices of this vertex that each machine vertex manages.
            Will be the same length as :py:meth:`machine_vertices`.

        :rtype: iterable(Slice)
        """
        return list(map(lambda x: x.vertex_slice, self._machine_vertices))

    def get_max_atoms_per_core(self):
        """ Gets the maximum number of atoms per core, which is either the\
            number of atoms required across the whole application vertex,\
            or a lower value if a constraint lowers it.

        :rtype: int
        """
        for constraint in self.constraints:
            if isinstance(constraint, MaxVertexAtomsConstraint):
                return constraint.size

    def forget_machine_vertices(self):
        """ Arrange to forget all machine vertices that this application
            vertex maps to.
        """
        self._machine_vertices = OrderedSet()
        if self._splitter is not None:
            self._splitter.reset_called()
