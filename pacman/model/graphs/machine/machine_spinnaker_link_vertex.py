# Copyright (c) 2017-2012 The University of Manchester
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

from spinn_utilities.overrides import overrides
from pacman.model.resources import ConstantSDRAM
from .machine_vertex import MachineVertex
from pacman.model.graphs import (
    AbstractVirtual, AbstractSpiNNakerLink)


class MachineSpiNNakerLinkVertex(MachineVertex, AbstractSpiNNakerLink):
    """ A virtual vertex on a SpiNNaker Link.
    """

    __slots__ = [
        "_spinnaker_link_id",
        "_board_address"]

    def __init__(
            self, spinnaker_link_id, board_address=None, label=None,
            constraints=None, app_vertex=None, vertex_slice=None):
        super().__init__(
            label=label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self._spinnaker_link_id = spinnaker_link_id
        self._board_address = board_address

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self):
        return ConstantSDRAM(0)

    @property
    @overrides(AbstractSpiNNakerLink.spinnaker_link_id)
    def spinnaker_link_id(self):
        return self._spinnaker_link_id

    @property
    @overrides(AbstractVirtual.board_address)
    def board_address(self):
        return self._board_address
