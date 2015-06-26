from pacman.model.constraints.abstract_constraints.\
    abstract_tag_allocator_constraint import AbstractTagAllocatorConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_reverse_iptag_constraint import \
    TagAllocatorRequireReverseIptagConstraint
from pacman.model.tags.tags import Tags
from pacman.operations.abstract_algorithms.\
    abstract_tag_allocator_algorithm import AbstractTagAllocatorAlgorithm
from pacman.utilities import utility_calls
from pacman.utilities.resource_tracker import ResourceTracker
from spinn_machine.tags.iptag import IPTag
from spinn_machine.tags.reverse_iptag import ReverseIPTag
from pacman.utilities.progress_bar import ProgressBar
from pacman.model.partitioned_graph.taggable_partitioned_vertex import \
     TaggablePartitionedVertex


class BasicTagAllocator(AbstractTagAllocatorAlgorithm):
    """ Basic tag allocator that goes though the boards available and applies
        the iptags and reverse iptags as needed.

    """

    def __init__(self):
        AbstractTagAllocatorAlgorithm.__init__(self)
        self._supported_constraints.append(TagAllocatorRequireIptagConstraint)
        self._supported_constraints.append(
            TagAllocatorRequireReverseIptagConstraint)

    def allocate_tags(self, machine, placements):
        """ see AbstractTagAllocatorAlgorithm.allocate_tags
        """

        resource_tracker = ResourceTracker(machine)

        # Check that the algorithm can handle the constraints
        placements_with_tags = [placement for placement in placements.placements
                  if isinstance(placement.subvertex, TaggablePartitionedVertex)
                  and utility_calls.check_algorithm_can_support_constraints(
                      constrained_vertices=[placement.subvertex],
                      supported_constraints=self._supported_constraints,
                      abstract_constraint_type=AbstractTagAllocatorConstraint)]
        progress_bar = ProgressBar(len(placements_with_tags),
                                   "Allocating Tags")
        """
        placements_with_tags = list()
        for placement in placements.placements:
            utility_calls.check_algorithm_can_support_constraints(
                constrained_vertices=[placement.subvertex],
                supported_constraints=self._supported_constraints,
                abstract_constraint_type=AbstractTagAllocatorConstraint)
            if len(utility_calls.locate_constraints_of_type(
                    placement.subvertex.constraints,
                    AbstractTagAllocatorConstraint)):
                placements_with_tags.append(placement)
            progress_bar.update()
        """

        # Go through and allocate the tags
        tags = Tags()
        for placement in placements_with_tags:
            vertex = placement.subvertex

            # Get the constraint details for the tags
            (board_address, ip_tags, reverse_ip_tags) =\
                utility_calls.get_ip_tag_info(vertex.constraints)

            # Allocate the tags, first-come, first-served, using the
            # fixed placement of the vertex, and the required resources
            chips = [(placement.x, placement.y)]
            resources = vertex.resources_required
            (_, _, _, returned_ip_tags, returned_reverse_ip_tags) = \
                resource_tracker.allocate_resources(
                    resources, chips, placement.p, board_address, ip_tags,
                    reverse_ip_tags)

            print "Allocated tags for vertex %s, forward: %s, reverse: %s" % (vertex.label, returned_ip_tags, returned_reverse_ip_tags)
            # Put the allocated ip tag information into the tag object
            if returned_ip_tags is not None:
                for (tag_constraint, (board_address, tag)) in zip(
                        ip_tags, returned_ip_tags):
                    ip_tag = IPTag(
                        board_address, tag, tag_constraint.ip_address,
                        tag_constraint.port, tag_constraint.strip_sdp)
                    tags.add_ip_tag(ip_tag, vertex)
                    vertex.add_ip_tag(ip_tag) 

            # Put the allocated reverse ip tag information into the tag object
            if returned_reverse_ip_tags is not None:
                for (tag_constraint, (board_address, tag)) in zip(
                        reverse_ip_tags, returned_reverse_ip_tags):
                    reverse_ip_tag = ReverseIPTag(
                        board_address, tag, tag_constraint.port, placement.x,
                        placement.y, placement.p, tag_constraint.sdp_port)
                    tags.add_reverse_ip_tag(reverse_ip_tag, vertex)
                    vertex.add_reverse_ip_tag(reverse_ip_tag)
            progress_bar.update()

        progress_bar.end()
        return tags
