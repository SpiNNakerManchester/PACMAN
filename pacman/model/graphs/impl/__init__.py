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

from .graph import Graph
from .outgoing_edge_partition import OutgoingEdgePartition
from .constant_sdram_machine_partition import ConstantSDRAMMachinePartition
from .destination_segmented_sdram_machine_partition import \
    DestinationSegmentedSDRAMMachinePartition
from .both_segmented_sdram_machine_partition import \
    BothSegmentedSDRAMMachinePartition
from .source_segmented_sdram_machine_partition import \
    SourceSegmentedSDRAMMachinePartition

__all__ = [
    "Graph",
    "OutgoingEdgePartition",
    "ConstantSDRAMMachinePartition",
    "DestinationSegmentedSDRAMMachinePartition",
    "SourceSegmentedSDRAMMachinePartition",
    "BothSegmentedSDRAMMachinePartition"]
