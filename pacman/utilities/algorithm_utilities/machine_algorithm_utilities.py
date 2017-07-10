from spinn_machine import SDRAM, Chip, Link, Processor, Router
import sys


def create_virtual_chip(machine, link_data, virtual_chip_x, virtual_chip_y):

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
