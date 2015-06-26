from pacman.model.partitionable_graph.abstract_tagged_partitionable_vertex \
    import AbstractTaggedPartitionableVertex
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_reverse_iptag_constraint \
    import TagAllocatorRequireReverseIptagConstraint
from spinn_machine.tags.reverse_iptag import UserReverseIPTag

import logging


logger = logging.getLogger(__name__)

class ReverseIPTaggedPartitionableVertex(AbstractTaggedPartitionableVertex):
    """ The reverse IP tagged partitionable vertex is a type of vertex that can
        hold tags for vertices that actually lie external to the SpiNNaker
        board.

        This class generates the necessary constraints on the vertex to contain
        the tags.
    """

    def __init__(self, n_atoms, label, max_atoms_per_core, tags, constraints=None):
        """ Constructor for the reverse ip tagged partitionable vertex.

        :param n_atoms: the number of atoms for the vertex
        :param label: the label of the vertex
        :param max_atoms_per_core: the max atoms that can be supported by a 
                    core. Note that this is translated into a partitioner max 
                    size constraint
        :param tags: a list of tag pairs (of type UserReverseIPTag; others
                    will be ignored)
        :param constraints: any extra constraints to be added to this vertex.
        :type n_atoms: int
        :type label: str
        :type max_atoms_per_core: int
        :type tags: list
        :type constraints: iterable list

        :return: the new partitionable vertex object

        :rtype: \
                    :py:class:`pacman.model.partitionable_graph.reverse_ip_tagged_partitionable_vertex.ReverseIPTaggedPartitionableVertex`

        :raise None: this method does not raise any exceptions
        """
        tags = [tag for tag in tags if isinstance(tag, UserReverseIPTag)]
        AbstractTaggedPartitionableVertex.__init__(self, n_atoms, label, 
                                             max_atoms_per_core, tags,
                                             constraints)

    def add_tag_constraint(self, tag):
        self.add_constraint(TagAllocatorRequireReverseIptagConstraint(
                            tag.port, tag.sdp_port, tag.board_address, 
                            tag.tag))

    def add_tag(self, tag):
        if isinstance(tag, UserReverseIPTag):
           AbstractTaggedPartitionableVertex.add_tag(self, tag)
