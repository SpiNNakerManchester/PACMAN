from pacman.operations.abstract_algorithms\
    .abstract_element_allocator_algorithm \
    import AbstractElementAllocatorAlgorithm
from abc import abstractmethod
from six import add_metaclass
from abc import ABCMeta


@add_metaclass(ABCMeta)
class AbstractChipIdAllocatorAlgorithm(AbstractElementAllocatorAlgorithm):

    @abstractmethod
    def allocate_chip_ids(self, partitionable_graph, machine):
        """ Allocates chip ids for AbstractVirtualVertices
        """

    def _create_virtual_chip(self, machine, virtual_vertex):
        """ Create a virtual chip as a real chip in the spinnmachine machine\
            object
        :param virtual_vertex: virutal vertex to convert into a real chip
        :return: the real chip
        """
        sdram_object = SDRAM()

        # creates the two links
        spinnaker_link_id = virtual_vertex.spinnaker_link_id
        spinnaker_link_data = \
            self._machine.locate_connected_chips_coords_and_link(
                config.getint("Machine", "version"), spinnaker_link_id)
        virtual_link_id = (spinnaker_link_data.connected_link + 3) % 6
        to_virtual_chip_link = Link(
            destination_x=virtual_vertex.virtual_chip_x,
            destination_y=virtual_vertex.virtual_chip_y,
            source_x=spinnaker_link_data.connected_chip_x,
            source_y=spinnaker_link_data.connected_chip_y,
            multicast_default_from=virtual_link_id,
            multicast_default_to=virtual_link_id,
            source_link_id=spinnaker_link_data.connected_link)

        from_virtual_chip_link = Link(
            destination_x=spinnaker_link_data.connected_chip_x,
            destination_y=spinnaker_link_data.connected_chip_y,
            source_x=virtual_vertex.virtual_chip_x,
            source_y=virtual_vertex.virtual_chip_y,
            multicast_default_from=(spinnaker_link_data.connected_link),
            multicast_default_to=spinnaker_link_data.connected_link,
            source_link_id=virtual_link_id)

        # create the router
        links = [from_virtual_chip_link]
        router_object = MachineRouter(
            links=links, emergency_routing_enabled=False,
            clock_speed=MachineRouter.ROUTER_DEFAULT_CLOCK_SPEED,
            n_available_multicast_entries=sys.maxint)

        # create the processors
        processors = list()
        for virtual_core_id in range(0, 128):
            processors.append(Processor(virtual_core_id,
                                        Processor.CPU_AVAILABLE,
                                        virtual_core_id == 0))

        # connect the real chip with the virtual one
        connected_chip = self._machine.get_chip_at(
            spinnaker_link_data.connected_chip_x,
            spinnaker_link_data.connected_chip_y)
        connected_chip.router.add_link(to_virtual_chip_link)

        # return new v chip
        return Chip(
            processors=processors, router=router_object, sdram=sdram_object,
            x=virtual_vertex.virtual_chip_x, y=virtual_vertex.virtual_chip_y,
            virtual=True, nearest_ethernet_x=None, nearest_ethernet_y=None)

