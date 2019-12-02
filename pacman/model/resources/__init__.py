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

from .abstract_sdram import AbstractSDRAM
from .constant_sdram import ConstantSDRAM
from .core_resource import CoreResource
from .cpu_cycles_per_tick_resource import CPUCyclesPerTickResource
from .dtcm_resource import DTCMResource
from .element_free_space import ElementFreeSpace
from .iptag_resource import IPtagResource
from .pre_allocated_resource_container import PreAllocatedResourceContainer
from .resource_container import ResourceContainer
from .reverse_iptag_resource import ReverseIPtagResource
from .specific_board_iptag_resource import (
    SpecificBoardTagResource as
    SpecificBoardIPtagResource)
from .specific_board_reverse_iptag_resource import (
    ReverseIPtagResource as
    SpecificBoardReverseIPtagResource)
from .specific_chip_sdram_resource import SpecificChipSDRAMResource
from .specific_core_resource import SpecificCoreResource
from .time_based_sdram import TimeBasedSDRAM
from .variable_sdram import VariableSDRAM


__all__ = ["AbstractSDRAM", "ConstantSDRAM", "CoreResource",
           "CPUCyclesPerTickResource", "DTCMResource",
           "ElementFreeSpace", "IPtagResource", "ResourceContainer",
           "ReverseIPtagResource",
           "PreAllocatedResourceContainer", "SpecificChipSDRAMResource",
           "SpecificCoreResource", "SpecificBoardIPtagResource",
           "SpecificBoardReverseIPtagResource", "TimeBasedSDRAM",
           "VariableSDRAM"]
