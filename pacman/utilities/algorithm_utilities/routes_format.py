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

import logging
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger(__name__))


def _reduce_route_value(processors_ids, link_ids):
    """
    :param iterable(int) processors_ids:
    :param iterable(int) link_ids:
    :rtype: int
    """
    value = 0
    for link in link_ids:
        value += 1 << link
    for processor in processors_ids:
        value += 1 << (processor + 6)
    return value


def _expand_route_value(processors_ids, link_ids):
    """
    Convert a 32-bit route word into a string which lists the target cores
    and links.

    :param iterable(int) processors_ids:
    :param iterable(int) link_ids:
    :rtype: str
    """

    # Convert processor targets to readable values:
    route_string = "["
    separator = ""
    for processor in processors_ids:
        route_string += f"{separator}{processor}"
        separator = ", "

    route_string += "] ["

    # Convert link targets to readable values:
    link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}

    separator = ""
    for link in link_ids:
        route_string += f"{separator}{link_labels[link]}"
        separator = ", "
    route_string += "]"
    return route_string


def format_route(entry):
    """ How to render a single routing entry.

    :param ~spinn_machine.MulticastRoutingEntry entry:
    :rtype: str
    """
    line_format = "0x{:08X} 0x{:08X} 0x{:08X} {: <7s} {}"

    key = entry.routing_entry_key
    mask = entry.mask
    route = _reduce_route_value(entry.processor_ids, entry.link_ids)
    route_txt = _expand_route_value(entry.processor_ids, entry.link_ids)
    return line_format.format(key, mask, route, str(entry.defaultable),
                              route_txt)
