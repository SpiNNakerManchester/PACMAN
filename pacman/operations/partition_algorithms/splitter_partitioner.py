# Copyright (c) 2020 The University of Manchester
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

from pacman.data import PacmanDataView
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.utility_objs.chip_counter import ChipCounter


def splitter_partitioner():
    """
    Call the splitter of each application vertex to create the machine vertices
    needed.

    :return: The number of chips needed to satisfy this partitioning.
    :rtype: int
    :raise PacmanPartitionException:
        If something goes wrong with the partitioning
    """
    progress = ProgressBar(
        PacmanDataView.get_n_vertices(), "Partitioning Graph")

    # Partition one vertex at a time
    chip_counter = ChipCounter()
    for vertex in progress.over(PacmanDataView.iterate_vertices()):
        vertex.splitter.create_machine_vertices(chip_counter)

    return chip_counter.n_chips
