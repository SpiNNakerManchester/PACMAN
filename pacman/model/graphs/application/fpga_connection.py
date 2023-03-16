# Copyright (c) 2021 The University of Manchester
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

from typing import NamedTuple

#: The range of FPGA ids
FPGA_IDS = range(0, 3)

#: The range of FPGA link ids
FPGA_LINK_IDS = range(0, 16)


class FPGAConnection(NamedTuple):
    """
    A connection from or to an FPGA.
    """

    #: The ID of the FPGA on the board (0, 1 or 2), or None for all of them
    fpga_id: int

    #: The ID of the link of the FPGA (0-15), or None for all of them
    fpga_link_id: int

    #: The IP address of the board with the FPGA, or None for the default board
    #: or if using chip_coords
    board_address: str

    #: The coordinates of the chip connected to the FPGA, or None for the
    #: default board or if using board_address
    chip_coords: tuple

    @property
    def is_concrete(self):
        """
        Determine if the connection has the FPGA id and link id set.

        :rtype: bool
        """
        return self.fpga_id is not None and self.fpga_link_id is not None

    @property
    def expanded(self):
        """
        Get a list of concrete FPGA connections,
        where fpga_id and fpga_link_id are not `None`.

        :rtype: iter(FPGAConnection)
        """
        ids = [self.fpga_id] if self.fpga_id is not None else FPGA_IDS
        links = ([self.fpga_link_id] if self.fpga_link_id is not None
                 else FPGA_LINK_IDS)
        for i in ids:
            for lnk in links:
                yield FPGAConnection(
                    i, lnk, self.board_address, self.chip_coords)
