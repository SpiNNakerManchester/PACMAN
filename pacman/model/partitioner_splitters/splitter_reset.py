# Copyright (c) 2020-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pacman.data import PacmanDataView


def splitter_reset():
    """ Performs resetting of splitters to indicate a new phase of operation
    """
    for vertex in PacmanDataView.iterate_vertices():
        if vertex.splitter is not None:
            vertex.splitter.reset_called()
