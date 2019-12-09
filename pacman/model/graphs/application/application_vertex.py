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
from spinn_utilities.abstract_base import (
    abstractmethod, abstractproperty, AbstractBase)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint)
from pacman.model.graphs import AbstractVertex
from pacman.exceptions import PacmanValueError


@add_metaclass(AbstractBase)
class ApplicationVertex(AbstractVertex):
    """ A vertex that can be broken down into a number of smaller vertices
        based on the resources that the vertex requires.
    """

    __slots__ = ["_machine_vertices", "_slices"]

    def __init__(self, label=None, constraints=None,
                 max_atoms_per_core=sys.maxsize):
        """
        :param str label: The optional name of the vertex
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex
        :param int max_atoms_per_core: the max number of atoms that can be\
            placed on a core, used in partitioning
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        """

        super(ApplicationVertex, self).__init__(label, constraints)
        self._machine_vertices = OrderedSet()
        self._slices = list()

        # add a constraint for max partitioning
        self.add_constraint(
            MaxVertexAtomsConstraint(max_atoms_per_core))

    def __str__(self):
        return self.label

    def __repr__(self):
        return "ApplicationVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @abstractmethod
    def get_resources_used_by_atoms(self, vertex_slice):
        """ Get the separate resource requirements for a range of atoms

        :param Slice vertex_slice:
            the low value of atoms to calculate resources from
        :return: a Resource container that contains a \
            CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: ResourceContainer
        """

    @abstractmethod
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        """ Create a machine vertex from this application vertex

        :param Slice vertex_slice:
            The slice of atoms that the machine vertex will cover
        :param ResourceContainer resources_required:
            the resources used by the machine vertex
        :param label: human readable label for the machine vertex
        :type label: str or None
        :param iterable(AbstractConstraint) constraints:
            Constraints to be passed on to the machine vertex
        """

    def remember_associated_machine_vertex(self, machine_vertex):
        if machine_vertex.vertex_slice.hi_atom >= self.n_atoms:
            raise PacmanValueError(
                "hi_atom {:d} >= maximum {:d}".format(
                    machine_vertex.vertex_slice.hi_atom, self.n_atoms))

        machine_vertex.index = len(self._machine_vertices)
        self._machine_vertices.add(machine_vertex)
        self._slices.append(machine_vertex.vertex_slice)

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
        return self._slices

    def get_max_atoms_per_core(self):
        """
        :rtype: int
        """
        for constraint in self.constraints:
            if isinstance(constraint, MaxVertexAtomsConstraint):
                return constraint.size
        return self.n_atoms

    def forget_machine_vertices(self):
        """ Arrange to forget all machine vertices that this application
            vertex maps to.
        """
        self._machine_vertices = OrderedSet()
        self._slices = list()
