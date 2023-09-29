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

"""
Basic implementations of a selection of splitters. Splitters are
responsible for taking an application vertex and creating one or more machine
vertices that implement the functionality, together with the edges to
internally connect those vertices up (if needed).
"""

from .abstract_splitter_common import AbstractSplitterCommon
from .splitter_one_app_one_machine import SplitterOneAppOneMachine
from .splitter_fixed_legacy import SplitterFixedLegacy
from .splitter_one_to_one_legacy import SplitterOneToOneLegacy
from .splitter_external_device import SplitterExternalDevice

__all__ = [
    'AbstractSplitterCommon',
    'SplitterOneAppOneMachine', 'SplitterOneToOneLegacy',
    'SplitterFixedLegacy', 'SplitterExternalDevice']
