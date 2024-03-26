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
import random
from typing import Dict, Optional
from spinn_utilities.log import FormatAdapter
from spinn_utilities.typing.coords import XY
from pacman.data import PacmanDataView
from pacman.model.graphs import AbstractVertex
from pacman.model.placements import Placements
from ._spinner_api import spinner_api, Colour

logger = FormatAdapter(logging.getLogger(__name__))


def _next_colour() -> Colour:
    """
    Get the next (random) RGBA colour to use for a vertex for placement
    drawings.

    :rtype: tuple(float, float, float, float)
    """
    return (
        random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1.0)


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
    if isinstance(spinner_api, ImportError):
        logger.exception(
            "Unable to draw placements as no spinner install found",
            exc_info=spinner_api)
        return
    report_file = os.path.join(PacmanDataView.get_run_dir_path(), filename)

    # Colour the boards by placements
    unused: Colour = (0.5, 0.5, 0.5, 1.0)
    vertex_colours: Dict[Optional[AbstractVertex], Colour] = defaultdict(
        _next_colour)
    vertex_colours[None] = unused
    board_colours: Dict[XY, Colour] = dict()
    machine = PacmanDataView.get_machine()
    for xy in machine.chip_coordinates:
        if (placements.n_placements_on_chip(xy) ==
                system_placements.n_placements_on_chip(xy)):
            board_colours[xy] = unused
            continue
        for placement in placements.placements_on_chip(xy):
            if not system_placements.is_vertex_placed(placement.vertex):
                board_colours[xy] = \
                    vertex_colours[placement.vertex.app_vertex]
                break
    include_boards = [
        (chip.x, chip.y) for chip in machine.ethernet_connected_chips]

    # Compute dimensions
    w = math.ceil(machine.width / 12)
    h = math.ceil(machine.height / 12)
    aspect_ratio = spinner_api.aspect_ratio(w, h)
    image_width = 10000
    image_height = int(image_width * aspect_ratio)

    hex_boards = spinner_api.create_torus(w, h)
    with spinner_api.png_context_manager(
            report_file, image_width, image_height) as ctx:
        spinner_api.draw(
            ctx, image_width, image_height, machine.width, machine.height,
            hex_boards, {}, board_colours, include_boards)
