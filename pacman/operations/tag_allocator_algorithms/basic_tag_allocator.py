from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ordered_set import OrderedSet

# pacman imports
from pacman.model.tags import Tags
from pacman.utilities.utility_objs import ResourceTracker

# spinn_machine imports
from spinn_machine.tags import IPTag, ReverseIPTag

# An arbitrary range of ports from which to allocate ports to Reverse IP Tags
_BOARD_PORTS = range(17896, 18000)


class BasicTagAllocator(object):
    """ Basic tag allocator that goes though the boards available and applies
        the ip tags and reverse ip tags as needed.

    """

    __slots__ = []

    def __call__(self, machine, placements):
        """ see AbstractTagAllocatorAlgorithm.allocate_tags
        """

        resource_tracker = ResourceTracker(machine)

        # Keep track of ports allocated to reverse ip tags and tags that still
        # need a port to be allocated
        ports_to_allocate = dict()
        tags_to_allocate_ports = list()

        # Check that the algorithm can handle the constraints
        progress = ProgressBar(placements.n_placements + 1, "Allocating tags")
        placements_with_tags = list()
        for placement in placements.placements:
            self._gather_placements_with_tags(placement, placements_with_tags)
            progress.update()

        # Go through and allocate the tags
        tags = Tags()
        for placement in placements_with_tags:
            self._allocate_tags_for_placement(
                placement, resource_tracker, tags, ports_to_allocate,
                tags_to_allocate_ports)
        progress.update()

        progress.end()

        # Finally allocate the ports to the reverse ip tags
        self._allocate_ports_for_reverse_ip_tags(
            tags_to_allocate_ports, ports_to_allocate, tags)

        return list(tags.ip_tags), list(tags.reverse_ip_tags), tags

    def _gather_placements_with_tags(self, placement, collector):
        if (placement.vertex.resources_required.iptags or
                placement.vertex.resources_required.reverse_iptags):
            ResourceTracker.check_constraints([placement.vertex])
            collector.append(placement)

    def _allocate_tags_for_placement(self, placement, resource_tracker,
                                     tag_collector, ports_collector,
                                     tag_port_tasks):
        vertex = placement.vertex
        resources = vertex.resources_required

        # Get the constraint details for the tags
        (board_address, ip_tags, reverse_ip_tags) = \
            ResourceTracker.get_ip_tag_info(resources, vertex.constraints)

        # Allocate the tags, first-come, first-served, using the fixed
        # placement of the vertex, and the required resources
        chips = [(placement.x, placement.y)]
        (_, _, _, returned_ip_tags, returned_reverse_ip_tags) = \
            resource_tracker.allocate_resources(
                resources, chips, placement.p, board_address, ip_tags,
                reverse_ip_tags)

        # Put the allocated ip tag information into the tag object
        if returned_ip_tags is not None:
            for (tag_constraint, (board_address, tag, dest_x, dest_y)) in \
                    zip(ip_tags, returned_ip_tags):
                ip_tag = IPTag(
                    board_address=board_address, destination_x=dest_x,
                    destination_y=dest_y, tag=tag,
                    ip_address=tag_constraint.ip_address,
                    port=tag_constraint.port,
                    strip_sdp=tag_constraint.strip_sdp,
                    traffic_identifier=tag_constraint.traffic_identifier)
                tag_collector.add_ip_tag(ip_tag, vertex)

        if returned_reverse_ip_tags is None:
            return

        # Put the allocated reverse ip tag information into the tag object
        for tag_constraint, (board_address, tag) in zip(
                reverse_ip_tags, returned_reverse_ip_tags):
            if board_address not in ports_collector:
                ports_collector[board_address] = OrderedSet(_BOARD_PORTS)
            if tag_constraint.port is not None:
                reverse_ip_tag = ReverseIPTag(
                    board_address, tag, tag_constraint.port,
                    placement.x, placement.y, placement.p,
                    tag_constraint.sdp_port)
                tag_collector.add_reverse_ip_tag(reverse_ip_tag, vertex)

                ports_collector[board_address].discard(tag_constraint.port)
            else:
                tag_port_tasks.append(
                    (tag_constraint, board_address, tag, vertex, placement))

    def _allocate_ports_for_reverse_ip_tags(self, tasks, ports, tags):
        for tag_constraint, board_address, tag, vertex, placement in tasks:
            if board_address not in ports:
                ports[board_address] = OrderedSet(_BOARD_PORTS)
            port = ports[board_address].pop(last=False)
            reverse_ip_tag = ReverseIPTag(
                board_address, tag, port,
                placement.x, placement.y, placement.p,
                tag_constraint.sdp_port)
            tags.add_reverse_ip_tag(reverse_ip_tag, vertex)
