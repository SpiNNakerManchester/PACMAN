# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.log import FormatAdapter
from spinn_machine import MulticastRoutingEntry
from pacman.model.graphs import (
    AbstractVirtual, AbstractFPGA, AbstractSpiNNakerLink)
from pacman.exceptions import PacmanConfigurationException
from pacman.model.routing_tables import UnCompressedMulticastRoutingTable
import logging

logger = FormatAdapter(logging.getLogger(__name__))


def external_device_null_routing_table_generator(
        machine, machine_graph, routing_tables):
    """ Examine external devices and ensure that every vertex has at least one
        outgoing edge to somewhere, and if not, add a routing entry to nowhere

    :param Machine machine: The machine to be used
    :param MachineGraph machine_graph:
        The machine graph containing the external devices (no devices is OK)
    :param MulticastRoutingTables routing_tables:
        The existing routing tables, to which entries can be added
    """

    for vertex in machine_graph.vertices:
        if isinstance(vertex, AbstractVirtual):
            edges = machine_graph.get_edges_starting_at_vertex(vertex)

            if not edges:
                keys_and_masks = vertex.outgoing_keys_and_masks()
                if keys_and_masks is None and vertex.app_vertex is not None:
                    keys_and_masks = \
                        vertex.app_vertex.get_outgoing_keys_and_masks(vertex)

                # If there are no edges, there has to be some outgoing keys
                # and masks, as otherwise this isn't going to work
                if keys_and_masks is None:
                    _raise_exception(vertex)

                x, y = _real_xy(vertex, machine)
                logger.warn(
                    f"The traffic from External device {vertex} will be"
                    f" stopped at {x}, {y} as there it has no outgoing edges")

                # Add the keys and masks to the real multicast routing table
                # but with no targets
                for key_and_mask in keys_and_masks:
                    table = routing_tables.get_routing_table_for_chip(x, y)
                    if table is None:
                        table = UnCompressedMulticastRoutingTable(x, y)
                        routing_tables.add_routing_table(table)
                    table.add_multicast_routing_entry(MulticastRoutingEntry(
                        key_and_mask.key, key_and_mask.mask))


def _raise_exception(vertex):
    """ Raise an exception about a virtual vertex not having edges or keys

    :param AbstractVirtual vertex: The vertex to raise the exception for
    """
    if vertex.app_vertex is not None:
        raise PacmanConfigurationException(
            f"The machine vertex {vertex} of the device {vertex.app_vertex}"
            " doesn't have any outgoing edges.  This means any packets sent by"
            " the device will not have any associated routing entries, which"
            " could cause unexpected results.  This can be fixed by either"
            " ensuring that all parts of the device are received somewhere, or"
            " overriding the 'get_outgoing_keys_and_masks' method in the"
            " device class.")
    else:
        raise PacmanConfigurationException(
            f"The external device machine vertex {vertex} doesn't have any"
            " outgoing edges.  This means any packets sent by the device will"
            " not have any associated routing entries, which could cause"
            " unexpected results.  This can be fixed by either ensuring that"
            " all parts of the device are received somewhere, or overriding"
            " the 'outgoing_keys_and_masks' method in the device class.")


def _real_xy(vertex, machine):
    """ Get the x and y coordinates of the real-chip the device is connected to

    :param AbstractVirtual vertex: The device machine vertex
    :param ~spinn_machine.Machine machine: The machine
    :rtype: tuple(int,int)
    """
    link_data = None
    if isinstance(vertex, AbstractFPGA):
        link_data = machine.get_fpga_link_with_id(
            vertex.fpga_id, vertex.fpga_link_id, vertex.board_address)
    elif isinstance(vertex, AbstractSpiNNakerLink):
        link_data = machine.get_spinnaker_link_with_id(
            vertex.spinnaker_link_id, vertex.board_address)
    return link_data.connected_chip_x, link_data.connected_chip_y
