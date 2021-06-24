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

from .application_vertex import ApplicationVertex
from spinn_utilities.overrides import overrides


class ApplicationSpiNNakerLinkVertex(ApplicationVertex):
    """ A virtual application vertex on a SpiNNaker Link.
    """

    __slots__ = [
        "_n_atoms",
        "_spinnaker_link_id",
        "_board_address"]

    def __init__(
            self, n_atoms, spinnaker_link_id, board_address=None, label=None,
            constraints=None):
        super().__init__(label=label, constraints=constraints)
        self._n_atoms = self.round_n_atoms(n_atoms)
        self._spinnaker_link_id = spinnaker_link_id
        self._board_address = board_address

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @property
    def spinnaker_link_id(self):
        """ The SpiNNaker link to which this device is connected

        :rtype: int
        """
        return self._spinnaker_link_id

    @property
    def board_address(self):
        """ The board to which this device is connected, or None for the
            default board

        :rtype: str or None
        """
        return self._board_address
