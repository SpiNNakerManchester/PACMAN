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
    processors = ", ".join(
        f"{processor}" for processor in processors_ids)

    # Convert link targets to readable values:
    link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}
    links = ", ".join(link_labels[link] for link in link_ids)

    return f"[{processors}] [{links}]"


def format_route(entry):
    """
    How to render a single routing entry.

    :param ~spinn_machine.MulticastRoutingEntry entry:
    :rtype: str
    """
    key = entry.routing_entry_key
    mask = entry.mask
    route = _reduce_route_value(entry.processor_ids, entry.link_ids)
    return (f"0x{key:08X} 0x{mask:08X} 0x{route:08X} {entry.defaultable:<7s} "
            f"{_expand_route_value(entry.processor_ids, entry.link_ids)}")
