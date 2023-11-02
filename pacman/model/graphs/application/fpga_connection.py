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
from __future__ import annotations
from typing import NamedTuple, Optional
from spinn_utilities.typing.coords import XY

#: The range of FPGA ids
FPGA_IDS = range(0, 3)

#: The range of FPGA link ids
FPGA_LINK_IDS = range(0, 16)


class FPGAConnection(NamedTuple):
    """
    A connection from or to an FPGA.
    """

    #: The ID of the FPGA on the board (0, 1 or 2)
    fpga_id: int

    #: The ID of the link of the FPGA (0-15)
    fpga_link_id: int

    #: The IP address of the board with the FPGA, or None for the default board
    #: or if using chip_coords
    board_address: Optional[str]

    #: The coordinates of the chip connected to the FPGA, or None for the
    #: default board or if using board_address
    chip_coords: Optional[XY]
