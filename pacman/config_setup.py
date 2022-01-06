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
