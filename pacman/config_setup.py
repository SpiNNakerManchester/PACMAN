# Copyright (c) 2017 The University of Manchester
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

import os
from spinn_utilities.config_holder import (
    add_default_cfg, clear_cfg_files)
from spinn_machine.config_setup import add_spinn_machine_cfg
from pacman.data.pacman_data_writer import PacmanDataWriter

BASE_CONFIG_FILE = "pacman.cfg"


def unittest_setup():
    """
    Resets the configs so only the local default config is included.

    .. note::
        This file should only be called from PACMAN/unittests

    """
    clear_cfg_files(True)
    add_pacman_cfg()
    PacmanDataWriter.mock()


def add_pacman_cfg():
    """
    Add the local cfg and all dependent cfg files.
    """
    add_spinn_machine_cfg()  # This add its dependencies too
    add_default_cfg(os.path.join(os.path.dirname(__file__), BASE_CONFIG_FILE))
