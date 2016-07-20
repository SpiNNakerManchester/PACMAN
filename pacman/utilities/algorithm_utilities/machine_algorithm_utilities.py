from spinn_machine.sdram import SDRAM
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.processor import Processor
from spinn_machine.router import Router
import sys


def create_virtual_chip(
        machine, spinnaker_link_id, fpga_link_id, fpga_id, virtual_chip_x,
        virtual_chip_y, board_address):
    """ Create a virtual chip as a real chip in the machine

    :param spinnaker_link_id:
    :param virtual_chip_x:
    :param virtual_chip_y:
    :param board_address:
    :param fpga_id:
    :param fpga_link_id:
    :param machine: the machine which will be adjusted
    :return: The spinnaker link data
    """

    if spinnaker_link_id is not None:
        # Get the spinnaker link from the machine
        link_data = machine.get_spinnaker_link_with_id(
            spinnaker_link_id, board_address)
    else:
        link_data = machine.get_sata_link_with_id(
            board_address, fpga_link_id, fpga_id)

    # If the chip already exists, return the data
    if machine.is_chip_at(virtual_chip_x, virtual_chip_y):
        if not machine.get_chip_at(virtual_chip_x, virtual_chip_y).virtual:
            raise Exception(
                "Attempting to add virtual chip in place of a real chip")
        return link_data

    # Create link to the virtual chip from the real chip
    virtual_link_id = (link_data.connected_link + 3) % 6
    to_virtual_chip_link = Link(
        destination_x=virtual_chip_x,
        destination_y=virtual_chip_y,
        source_x=link_data.connected_chip_x,
        source_y=link_data.connected_chip_y,
        multicast_default_from=virtual_link_id,
        multicast_default_to=virtual_link_id,
        source_link_id=link_data.connected_link)

    # Create link to the real chip from the virtual chip
    from_virtual_chip_link = Link(
        destination_x=link_data.connected_chip_x,
        destination_y=link_data.connected_chip_y,
        source_x=virtual_chip_x,
        source_y=virtual_chip_y,
        multicast_default_from=link_data.connected_link,
        multicast_default_to=link_data.connected_link,
        source_link_id=virtual_link_id)

    # create the router
    links = [from_virtual_chip_link]
    router_object = Router(
        links=links, emergency_routing_enabled=False,
        clock_speed=Router.ROUTER_DEFAULT_CLOCK_SPEED,
        n_available_multicast_entries=sys.maxint)

    # create the processors
    processors = list()
    for virtual_core_id in range(0, 128):
        processors.append(Processor(virtual_core_id))

    # connect the real chip with the virtual one
    connected_chip = machine.get_chip_at(
        link_data.connected_chip_x,
        link_data.connected_chip_y)
    connected_chip.router.add_link(to_virtual_chip_link)

    machine.add_chip(Chip(
        processors=processors, router=router_object,
        sdram=SDRAM(size=0),
        x=virtual_chip_x, y=virtual_chip_y,
        virtual=True, nearest_ethernet_x=None, nearest_ethernet_y=None))

    return link_data
