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

from collections import defaultdict
import math
import os
import logging
import numpy
from typing import Any, Dict, Optional
from spinn_utilities.log import FormatAdapter
from pacman.data import PacmanDataView
from pacman.model.placements import Placements
logger = FormatAdapter(logging.getLogger(__name__))
_exception: Optional[ImportError] = None
try:
    # spinner as graphical library so
    # pylint: disable=import-error
    from spinner.scripts.contexts import PNGContextManager
    from spinner.diagrams.machine_map import (
        get_machine_map_aspect_ratio, draw_machine_map)
    from spinner import board
except ImportError as _e:
    PNGContextManager = None
    get_machine_map_aspect_ratio, draw_machine_map = None, None
    board = None
    _exception = _e


def _next_colour():
    """
    Get the next (random) RGBA colour to use for a vertex for placement
    drawings.

    :rtype: tuple(float, float, float, float)
    """
    return tuple(numpy.concatenate(
        (numpy.random.choice(range(256), size=3) / 256, [1.0])))


def draw_placements(
        placements: Placements, system_placements: Placements,
        filename: str = "placements_error.png"):
    """
    Draw the placements as a PNG in the specified file.

    :param Placements placements:
        The application placements. Includes the system placements.
    :param Placements system_placements:
        The system placements.
    :param str filename:
        Name of file to make. Should have a ``.png`` suffix by convention.
    """
    if _exception:
        logger.exception(
            "Unable to draw placements as no spinner install found",
            exc_info=_exception)
        return
    report_file = os.path.join(PacmanDataView.get_run_dir_path(), filename)

    # Colour the boards by placements
    unused = (0.5, 0.5, 0.5, 1.0)
    vertex_colours: Dict[Any, Any] = defaultdict(_next_colour)
    board_colours: Dict[Any, Any] = dict()
    machine = PacmanDataView.get_machine()
    for x, y in machine.chip_coordinates:
        if (placements.n_placements_on_chip(x, y) ==
                system_placements.n_placements_on_chip(x, y)):
            board_colours[x, y] = unused
            continue
        for placement in placements.placements_on_chip(x, y):
            if not system_placements.is_vertex_placed(placement.vertex):
                board_colours[x, y] = \
                    vertex_colours[placement.vertex.app_vertex]
                break
    include_boards = [
        (chip.x, chip.y) for chip in machine.ethernet_connected_chips]

    # Compute dimensions
    w = math.ceil(machine.width / 12)
    h = math.ceil(machine.height / 12)
    aspect_ratio = get_machine_map_aspect_ratio(w, h)
    image_width = 10000
    image_height = int(image_width * aspect_ratio)

    hex_boards = board.create_torus(w, h)
    with PNGContextManager(report_file, image_width, image_height) as ctx:
        draw_machine_map(
            ctx, image_width, image_height, machine.width, machine.height,
            hex_boards, dict(), board_colours, include_boards)
