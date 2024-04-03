# Copyright (c) 2016 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractVirtual
from pacman.model.resources import ConstantSDRAM
from .machine_vertex import MachineVertex
if TYPE_CHECKING:
    from spinn_utilities.typing.coords import XY
    from spinn_machine import Machine
    from spinn_machine.link_data_objects import FPGALinkData
    from pacman.model.graphs.application import ApplicationVertex
    from pacman.model.graphs.common import Slice
    from pacman.model.routing_info import BaseKeyAndMask


class MachineFPGAVertex(MachineVertex, AbstractVirtual):
    """
    A virtual vertex on an FPGA link.
    """

    __slots__ = (
        "_fpga_id",
        "_fpga_link_id",
        "_board_address",
        "_linked_chip_coordinates",
        "_outgoing_keys_and_masks",
        "_incoming",
        "_outgoing")

    def __init__(
            self, fpga_id: int, fpga_link_id: int,
            board_address: Optional[str] = None,
            linked_chip_coordinates: Optional[XY] = None,
            label: Optional[str] = None,
            app_vertex: Optional[ApplicationVertex] = None,
            vertex_slice: Optional[Slice] = None,
            outgoing_keys_and_masks: Optional[List[BaseKeyAndMask]] = None,
            incoming: bool = True, outgoing: bool = False):
        super().__init__(
            label=label, app_vertex=app_vertex, vertex_slice=vertex_slice)

        self._fpga_id = fpga_id
        self._fpga_link_id = fpga_link_id
        self._board_address = board_address
        self._linked_chip_coordinates = linked_chip_coordinates
        self._outgoing_keys_and_masks = outgoing_keys_and_masks
        self._incoming = incoming
        self._outgoing = outgoing

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> ConstantSDRAM:
        return ConstantSDRAM(0)

    @property
    def fpga_id(self) -> int:
        """
        The Field Programmable Gate Arrays id provided top the init.

        :rtype: int
        """
        return self._fpga_id

    @property
    def fpga_link_id(self) -> int:
        """
        The Field Programmable Gate Arrays link id provided to the init.

        :rtype: int
        """
        return self._fpga_link_id

    @property
    @overrides(AbstractVirtual.board_address)
    def board_address(self) -> Optional[str]:
        return self._board_address

    @property
    @overrides(AbstractVirtual.linked_chip_coordinates)
    def linked_chip_coordinates(self) -> Optional[XY]:
        return self._linked_chip_coordinates

    @overrides(AbstractVirtual.outgoing_keys_and_masks)
    def outgoing_keys_and_masks(self) -> Optional[List[BaseKeyAndMask]]:
        return self._outgoing_keys_and_masks

    @property
    @overrides(AbstractVirtual.incoming)
    def incoming(self) -> bool:
        return self._incoming

    @property
    @overrides(AbstractVirtual.outgoing)
    def outgoing(self) -> bool:
        return self._outgoing

    @overrides(AbstractVirtual.get_link_data)
    def get_link_data(self, machine: Machine) -> FPGALinkData:
        return machine.get_fpga_link_with_id(
            self._fpga_id, self._fpga_link_id, self._board_address,
            self._linked_chip_coordinates)
