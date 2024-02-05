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

from dataclasses import dataclass
import platform
from typing import (
    Any, Callable, ContextManager, Dict, List, NewType, Union, Tuple)
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
    png_context_manager: Callable[[str, int, int], ContextManager[_Context]]
    aspect_ratio: Callable[[int, int], float]
    draw: Callable[
        [_Context, int, int, int, int, _Boards, Dict[Any, Any],
         Dict[XY, Colour], List[XY]], None]
    create_torus: Callable[[int, int], _Boards]

    @staticmethod
    def import_api() -> 'Spinner':
        """
        Loads the required imports and returns a Spinner

        :rtype: Spinner
        :raises ImportError: if on Windows
        """
        # spinner as graphical library so
        # pylint: disable=import-error,import-outside-toplevel

        # Depends on Cairo, which is virtually never there on Windows.
        # We could catch the OSError, but that's very noisy in this case
        if platform.platform().lower().startswith("windows"):
            raise ImportError("SpiNNer not supported on Windows")

        from spinner.scripts.contexts import (  # type: ignore
            PNGContextManager)
        from spinner.diagrams.machine_map import (  # type: ignore
            get_machine_map_aspect_ratio, draw_machine_map)
        from spinner.board import create_torus  # type: ignore
        return Spinner(PNGContextManager, get_machine_map_aspect_ratio,
                       draw_machine_map, create_torus)


#: Either we get the API to SpiNNer, or we have an error
spinner_api: Union[Spinner, ImportError]

try:
    spinner_api = Spinner.import_api()
except ImportError as _e:
    spinner_api = _e
