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

import sys
from pacman.utilities import constants
from spinn_machine import SDRAM, Chip, Link, Router


def create_virtual_chip(machine, link_data, virtual_chip_x, virtual_chip_y):
    """ Create a virtual chip on a real machine.

    :param ~spinn_machine.Machine machine:
    :param ~spinn_machine.link_data_objects.AbstractLinkData link_data:
        Describes the link from the real machine.
    :param int virtual_chip_x: Virtual chip coordinate
    :param int virtual_chip_y: Virtual chip coordinate
    """

    # If the chip already exists, return the data
    if machine.is_chip_at(virtual_chip_x, virtual_chip_y):
        if not machine.get_chip_at(virtual_chip_x, virtual_chip_y).virtual:
            raise Exception(
                "Attempting to add virtual chip in place of a real chip")
        return

    # Create link to the virtual chip from the real chip
    virtual_link_id = (link_data.connected_link + 3) % 6
    to_virtual_chip_link = Link(
        destination_x=virtual_chip_x,
        destination_y=virtual_chip_y,
        source_x=link_data.connected_chip_x,
        source_y=link_data.connected_chip_y,
        source_link_id=link_data.connected_link)

    # Create link to the real chip from the virtual chip
    from_virtual_chip_link = Link(
        destination_x=link_data.connected_chip_x,
        destination_y=link_data.connected_chip_y,
        source_x=virtual_chip_x,
        source_y=virtual_chip_y,
        source_link_id=virtual_link_id)

    # create the router
    links = [from_virtual_chip_link]
    router_object = Router(
        links=links, emergency_routing_enabled=False,
        n_available_multicast_entries=sys.maxsize)

    # connect the real chip with the virtual one
    connected_chip = machine.get_chip_at(
        link_data.connected_chip_x,
        link_data.connected_chip_y)
    connected_chip.router.add_link(to_virtual_chip_link)

    machine.add_virtual_chip(Chip(
        n_processors=constants.CORES_PER_VIRTUAL_CHIP, router=router_object,
        sdram=SDRAM(size=0),
        x=virtual_chip_x, y=virtual_chip_y,
        virtual=True, nearest_ethernet_x=None, nearest_ethernet_y=None))
