
# pacman imports
from pacman.model.tags.tags import Tags
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker

# spinn_machine imports
from spinn_machine.tags.iptag import IPTag
from spinn_machine.tags.reverse_iptag import ReverseIPTag
from spinn_machine.utilities.progress_bar import ProgressBar
from spinn_machine.utilities.ordered_set import OrderedSet

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

        # Keep track of ports allocated to reverse ip tags
        # and tags that still need a port to be allocated
        ports_to_allocate = dict()
        tags_to_allocate_ports = list()

        # Check that the algorithm can handle the constraints
        progress_bar = ProgressBar(placements.n_placements,
                                   "Allocating tags")
        placements_with_tags = list()
        for placement in placements.placements:
            if (len(placement.vertex.resources_required.iptags) > 0 or
                    len(placement.vertex.resources_required.
                        reverse_iptags) > 0):
                ResourceTracker.check_constraints([placement.vertex])
                placements_with_tags.append(placement)
            progress_bar.update()

        # Go through and allocate the tags
        tags = Tags()
        for placement in placements_with_tags:
            vertex = placement.vertex
            resources = vertex.resources_required

            # Get the constraint details for the tags
            (board_address, ip_tags, reverse_ip_tags) = \
                ResourceTracker.get_ip_tag_info(resources, vertex.constraints)

            # Allocate the tags, first-come, first-served, using the
            # fixed placement of the vertex, and the required resources
            chips = [(placement.x, placement.y)]
            (_, _, _, returned_ip_tags, returned_reverse_ip_tags) = \
                resource_tracker.allocate_resources(
                    resources, chips, placement.p, board_address, ip_tags,
                    reverse_ip_tags)

            # Put the allocated ip tag information into the tag object
            if returned_ip_tags is not None:
                for (tag_constraint,
                        (board_address, tag, dest_x, dest_y)) in zip(
                            ip_tags, returned_ip_tags):
                    ip_tag = IPTag(
                        board_address=board_address, destination_x=dest_x,
                        destination_y=dest_y, tag=tag,
                        ip_address=tag_constraint.ip_address,
                        port=tag_constraint.port,
                        strip_sdp=tag_constraint.strip_sdp,
                        traffic_identifier=tag_constraint.traffic_identifier)
                    tags.add_ip_tag(ip_tag, vertex)

            # Put the allocated reverse ip tag information into the tag object
            if returned_reverse_ip_tags is not None:
                for (tag_constraint, (board_address, tag)) in zip(
                        reverse_ip_tags, returned_reverse_ip_tags):
                    if board_address not in ports_to_allocate:
                        ports_to_allocate[board_address] = OrderedSet(
                            _BOARD_PORTS)
                    if tag_constraint.port is not None:
                        reverse_ip_tag = ReverseIPTag(
                            board_address, tag, tag_constraint.port,
                            placement.x, placement.y, placement.p,
                            tag_constraint.sdp_port)
                        tags.add_reverse_ip_tag(reverse_ip_tag, vertex)

                        ports_to_allocate[board_address].discard(
                            tag_constraint.port)
                    else:
                        tags_to_allocate_ports.append(
                            (tag_constraint, board_address, tag, vertex,
                             placement))

        progress_bar.end()

        # Finally allocate the ports to the reverse ip tags
        for (tag_constraint, board_address, tag, vertex, placement) in\
                tags_to_allocate_ports:
            if board_address not in ports_to_allocate:
                ports_to_allocate[board_address] = OrderedSet(_BOARD_PORTS)
            port = ports_to_allocate[board_address].pop(last=False)
            reverse_ip_tag = ReverseIPTag(
                board_address, tag, port,
                placement.x, placement.y, placement.p,
                tag_constraint.sdp_port)
            tags.add_reverse_ip_tag(reverse_ip_tag, vertex)

        return list(tags.ip_tags), list(tags.reverse_ip_tags), tags
