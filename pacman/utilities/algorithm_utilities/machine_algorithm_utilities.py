from spinn_machine.sdram import SDRAM
from spinn_machine.chip import Chip
from spinn_machine.link import Link
from spinn_machine.processor import Processor
from spinn_machine.router import Router
import sys


def create_virtual_chip(machine, virtual_vertex):
        """ Create a virtual chip as a real chip in the machine
        :param virtual_vertex: virtual vertex to convert into a real chip
        :param machine: the machine which will be adjusted
        :return: the real chip
        """

        # Get the spinnaker link from the machine
        spinnaker_link_data = machine.get_spinnaker_link_with_id(
            virtual_vertex.spinnaker_link_id)

        # Create link to the virtual chip from the real chip
        virtual_link_id = (spinnaker_link_data.connected_link + 3) % 6
        to_virtual_chip_link = Link(
            destination_x=virtual_vertex.virtual_chip_x,
            destination_y=virtual_vertex.virtual_chip_y,
            source_x=spinnaker_link_data.connected_chip_x,
            source_y=spinnaker_link_data.connected_chip_y,
            multicast_default_from=virtual_link_id,
            multicast_default_to=virtual_link_id,
            source_link_id=spinnaker_link_data.connected_link)

        # Create link to the real chip from the virtual chip
        from_virtual_chip_link = Link(
            destination_x=spinnaker_link_data.connected_chip_x,
            destination_y=spinnaker_link_data.connected_chip_y,
            source_x=virtual_vertex.virtual_chip_x,
            source_y=virtual_vertex.virtual_chip_y,
            multicast_default_from=spinnaker_link_data.connected_link,
            multicast_default_to=spinnaker_link_data.connected_link,
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
            processors.append(Processor(virtual_core_id,
                                        Processor.CPU_AVAILABLE,
                                        virtual_core_id == 0))

        # connect the real chip with the virtual one
        connected_chip = machine.get_chip_at(
            spinnaker_link_data.connected_chip_x,
            spinnaker_link_data.connected_chip_y)
        connected_chip.router.add_link(to_virtual_chip_link)

        machine.add_chip(Chip(
            processors=processors, router=router_object,
            sdram=SDRAM(
                total_size=0, user_base_address=0, system_base_address=0),
            x=virtual_vertex.virtual_chip_x, y=virtual_vertex.virtual_chip_y,
            virtual=True, nearest_ethernet_x=None, nearest_ethernet_y=None))
