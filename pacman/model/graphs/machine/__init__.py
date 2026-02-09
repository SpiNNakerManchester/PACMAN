# Copyright (c) 2015 The University of Manchester
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

from .machine_edge import MachineEdge
from .machine_fpga_vertex import MachineFPGAVertex
from .machine_sdram_edge import SDRAMMachineEdge
from .machine_spinnaker_link_vertex import MachineSpiNNakerLinkVertex
from .machine_vertex import MachineVertex
from .simple_machine_vertex import SimpleMachineVertex
from .abstract_sdram_partition import AbstractSDRAMPartition
from .constant_sdram_machine_partition import ConstantSDRAMMachinePartition
from .destination_segmented_sdram_machine_partition import (
    DestinationSegmentedSDRAMMachinePartition)
from .multicast_edge_partition import MulticastEdgePartition
from .source_segmented_sdram_machine_partition import (
    SourceSegmentedSDRAMMachinePartition)
from .machine_sysram_edge import SysRAMMachineEdge
from .abstract_sysram_partition import AbstractSysRAMPartition
from .constant_sysram_machine_partition import ConstantSysRAMMachinePartition
from .source_segmented_sysram_machine_partition import (
    SourceSegmentedSysRAMMachinePartition)
from .destination_segmented_sysram_machine_partition import (
    DestinationSegmentedSysRAMMachinePartition)

__all__ = [
    "AbstractSDRAMPartition", "ConstantSDRAMMachinePartition",
    "DestinationSegmentedSDRAMMachinePartition",
    "MachineEdge", "MachineFPGAVertex",
    "MachineSpiNNakerLinkVertex", "MachineVertex", "MulticastEdgePartition",
    "SDRAMMachineEdge", "SimpleMachineVertex",
    "SourceSegmentedSDRAMMachinePartition", "SysRAMMachineEdge",
    "AbstractSysRAMPartition", "ConstantSysRAMMachinePartition",
    "SourceSegmentedSysRAMMachinePartition",
    "DestinationSegmentedSysRAMMachinePartition"]
