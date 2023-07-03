# Copyright (c) 2023 The University of Manchester
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

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, NewType, Union, Tuple
from spinn_utilities.typing.coords import XY

# Don't know or care what these next two types are; they're SpiNNer's
_Boards = NewType("_Boards", list)
_Context = NewType("_Context", int)
#: The type of colours. RGBA
Colour = Tuple[float, float, float, float]


@dataclass
class Spinner:
    """
    Typed version of the API from SpiNNer that we actually use.
    """
    #: Open a drawing surface as a context
    png_context_manager: Callable[
        [str, int, int], AbstractContextManager[_Context]]
    aspect_ratio: Callable[[int, int], float]
    draw: Callable[
        [_Context, int, int, int, int, _Boards, Dict[Any, Any],
         Dict[XY, Colour], List[XY]], None]
    create_torus: Callable[[int, int], _Boards]


#: Either we get the API to SpiNNer, or we have an error
spinner_api: Union[Spinner, ImportError]

try:
    # spinner as graphical library so
    # pylint: disable=import-error
    from spinner.scripts.contexts import PNGContextManager as _PCM
    from spinner.diagrams.machine_map import (
        get_machine_map_aspect_ratio as _ar, draw_machine_map as _draw)
    from spinner.board import create_torus as _ct
    _spinner_api = Spinner(_PCM, _ar, _draw, _ct)
except ImportError as _e:
    spinner_api = _e
