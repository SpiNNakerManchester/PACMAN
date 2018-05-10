from .abstract_resource import AbstractResource
from .core_resource import CoreResource
from .cpu_cycles_per_tick_resource import CPUCyclesPerTickResource
from .dtcm_resource import DTCMResource
from .element_free_space import ElementFreeSpace
from .iptag_resource import IPtagResource
from .pre_allocated_resource_container import PreAllocatedResourceContainer
from .resource_container import ResourceContainer
from .reverse_iptag_resource import ReverseIPtagResource
from .sdram_resource import SDRAMResource
from .specific_board_iptag_resource import (
    SpecificBoardTagResource as
    SpecificBoardIPtagResource)
from .specific_board_reverse_iptag_resource import (
    ReverseIPtagResource as
    SpecificBoardReverseIPtagResource)
from .specific_chip_sdram_resource import SpecificChipSDRAMResource
from .specific_core_resource import SpecificCoreResource

__all__ = ["AbstractResource", "CPUCyclesPerTickResource", "DTCMResource",
           "ElementFreeSpace", "IPtagResource", "ResourceContainer",
           "ReverseIPtagResource", "SDRAMResource", "CoreResource",
           "PreAllocatedResourceContainer", "SpecificChipSDRAMResource",
           "SpecificCoreResource", "SpecificBoardIPtagResource",
           "SpecificBoardReverseIPtagResource"]
