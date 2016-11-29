
# pacman imports
from pacman.model.tags.tags import Tags
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker

# spinn_machine imports
from spinn_machine.tags.iptag import IPTag
from spinn_machine.tags.reverse_iptag import ReverseIPTag
from spinn_machine.utilities.progress_bar import ProgressBar


class BasicTagAllocator(object):
    """ Basic tag allocator that goes though the boards available and applies
        the ip tags and reverse ip tags as needed.

    """

    __slots__ = []

    def __call__(self, machine, placements):
        """ see AbstractTagAllocatorAlgorithm.allocate_tags
        """

        resource_tracker = ResourceTracker(machine)

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
                for (tag_constraint, (board_address, tag)) in zip(
                        ip_tags, returned_ip_tags):
                    ip_tag = IPTag(
                        board_address=board_address, tag=tag,
                        ip_address=tag_constraint.ip_address,
                        port=tag_constraint.port,
                        strip_sdp=tag_constraint.strip_sdp,
                        traffic_identifier=tag_constraint.traffic_identifier)
                    tags.add_ip_tag(ip_tag, vertex)

            # Put the allocated reverse ip tag information into the tag object
            if returned_reverse_ip_tags is not None:
                for (tag_constraint, (board_address, tag)) in zip(
                        reverse_ip_tags, returned_reverse_ip_tags):
                    reverse_ip_tag = ReverseIPTag(
                        board_address, tag, tag_constraint.port, placement.x,
                        placement.y, placement.p, tag_constraint.sdp_port)
                    tags.add_reverse_ip_tag(reverse_ip_tag, vertex)

        progress_bar.end()
        return list(tags.ip_tags), list(tags.reverse_ip_tags), tags
