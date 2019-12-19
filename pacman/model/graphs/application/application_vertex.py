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
from spinn_utilities.abstract_base import (
    abstractmethod, abstractproperty, AbstractBase)
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint)
from pacman.model.graphs import AbstractVertex


@add_metaclass(AbstractBase)
class ApplicationVertex(AbstractVertex):
    """ A vertex that can be broken down into a number of smaller vertices
        based on the resources that the vertex requires.
    """

    __slots__ = []

    def __init__(self, label=None, constraints=None,
                 max_atoms_per_core=sys.maxsize):
        """
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: iterable(AbstractConstraint)
        :param max_atoms_per_core: the max number of atoms that can be\
            placed on a core, used in partitioning
        :type max_atoms_per_core: int
        :raise PacmanInvalidParameterException:\
            * If one of the constraints is not valid
        """

        super(ApplicationVertex, self).__init__(label, constraints)

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

        :param vertex_slice: the low value of atoms to calculate resources from
        :type vertex_slice: ~pacman.model.graphs.common.Slice
        :return: a Resource container that contains a \
            CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: ~pacman.model.resources.ResourceContainer
        :raise None: this method does not raise any known exception
        """

    @abstractmethod
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        """ Create a machine vertex from this application vertex

        :param vertex_slice:\
            The slice of atoms that the machine vertex will cover
        :type vertex_slice: ~pacman.model.graphs.common.Slice
        :param resources_required: the resources used by the machine vertex
        :type resources_required: ~pacman.model.resources.ResourceContainer
        :param label: human readable label for the machine vertex
        :type label: str or None
        :param constraints: Constraints to be passed on to the machine vertex
        :type constraints: \
            iterable(~pacman.model.constraints.AbstractConstraint)
        """

    @abstractproperty
    def n_atoms(self):
        """ The number of atoms in the vertex

        :rtype: int
        """

    def get_max_atoms_per_core(self):
        for constraint in self.constraints:
            if isinstance(constraint, MaxVertexAtomsConstraint):
                return constraint.size
        return self.n_atoms

    def timesteps_in_us(self):
        """ The timesteps of this vertex in us

        Typically will be a singleton list of timestep set by the users.

        Vertexes which do not use timestep may return an empty list.

        If the machine vertexes have different timestemps this method will all
        the different ones.

        :rtype: set(int)
        """
