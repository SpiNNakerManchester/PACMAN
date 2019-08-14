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

from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from pacman.model.graphs import AbstractVertex


@add_metaclass(AbstractBase)
class MachineVertex(AbstractVertex):
    """ A machine graph vertex.
    """

    __slots__ = []

    def __init__(self, label=None, constraints=None):
        """
        :param label: The optional name of the vertex
        :type label: str
        :param constraints: The optional initial constraints of the vertex
        :type constraints: \
            iterable(:py:class:`pacman.model.constraints.AbstractConstraint`)
        :raise pacman.exceptions.PacmanInvalidParameterException:
            * If one of the constraints is not valid
        """
        if label is None:
            label = str(type(self))
        super(MachineVertex, self).__init__(label, constraints)
        self._added_to_graph = False

    def __str__(self):
        _l = self.label
        return self.__repr__() if _l is None else _l

    def __repr__(self):
        return "MachineVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @abstractproperty
    def resources_required(self):
        """ The resources required by the vertex

        :rtype: :py:class:`pacman.model.resources.ResourceContainer`
        """
