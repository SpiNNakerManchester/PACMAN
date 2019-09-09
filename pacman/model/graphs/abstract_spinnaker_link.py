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

from spinn_utilities.abstract_base import abstractproperty
from .abstract_virtual import AbstractVirtual


class AbstractSpiNNakerLink(AbstractVirtual):
    """ A An Object (most likely a vertex)  connected to a SpiNNaker Link.

        Note: It is expected that everything that is an instance of
        AbstractSpiNNakerLink is also an instance of AbstractVertex,
        This is not enforced to avoid diamond inheritance.
    """

    __slots__ = ()

    @abstractproperty
    def spinnaker_link_id(self):
        """ The SpiNNaker Link that the vertex is connected to.
        """
        return self._spinnaker_link_id
