# Copyright (c) 2019-2020 The University of Manchester
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

from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class SplitterByAtoms(object):

    @abstractmethod
    def get_resources_used_by_atoms(self, vertex_slice):
        """ Get the separate resource requirements for a range of atoms

        :param vertex_slice: the low value of atoms to calculate resources from
        :type vertex_slice: :py:class:`pacman.model.graphs.common.Slice`
        :return: a Resource container that contains a \
            CPUCyclesPerTickResource, DTCMResource and SDRAMResource
        :rtype: :py:class:`pacman.model.resources.ResourceContainer`
        :raise None: this method does not raise any known exception
        """

    @abstractmethod
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        """ Create a machine vertex from this application vertex

        :param vertex_slice:\
            The slice of atoms that the machine vertex will cover
        :param resources_required: the resources used by the machine vertex
        :param label: the label for the machine vertex to add to.
        :param constraints: Constraints to be passed on to the machine vertex
        """

    @abstractproperty
    def n_atoms(self):
        """ The number of atoms in the vertex

        :return: The number of atoms
        :rtype: int
        """
