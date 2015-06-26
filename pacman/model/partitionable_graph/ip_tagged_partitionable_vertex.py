from pacman.model.partitionable_graph.abstract_tagged_partitionable_vertex \
    import AbstractTaggedPartitionableVertex
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint \
    import TagAllocatorRequireIptagConstraint
from spinn_machine.tags.user_iptag import UserIPTag

import logging


logger = logging.getLogger(__name__)

class IPTaggedPartitionableVertex(AbstractTaggedPartitionableVertex):
    """ The IP tagged partitionable vertex is a type of vertex that can hold 
        tags for vertices that communicate externally.

        This class generates the necessary constraints on the vertex to contain
        the tags.
    """

    def __init__(self, n_atoms, label, max_atoms_per_core, tags, constraints=None):
        """ Constructor for the IP tagged partitionable vertex.

        :param n_atoms: the number of atoms for the vertex
        :param label: the label of the vertex
        :param max_atoms_per_core: the max atoms that can be supported by a \
                    core. Note that this is translated into a partitioner max \
                    size constraint
        :param tags: a list of tags (of type UserIPTag; others will be ignored)
        :param constraints: any extra constraints to be added to this vertex.
        :type n_atoms: int
        :type label: str
        :type max_atoms_per_core: int
        :type tags: list
        :type constraints: iterable list

        :return: the new partitionable vertex object

        :rtype: \
                    :py:class:`pacman.model.partitionable_graph.ip_tagged_partitionable_vertex.IPTaggedPartitionableVertex`

        :raise None: this method does not raise any exceptions
        """
        # take only IP tags; ignore everything else. 
        tags = [tag for tag in tags if isinstance(tag, UserIPTag)] 
        AbstractTaggedPartitionableVertex.__init__(self, n_atoms, label, 
                                          max_atoms_per_core, tags, constraints)
        
    def add_tag_constraint(self, tag):
        self.add_constraint(TagAllocatorRequireIptagConstraint(
                            tag.ip_address, tag.port, tag.strip_sdp,
                            tag.board_address, tag.tag))
                                                                  
    def add_tag(self, tag):
        if isinstance(tag, UserIPTag):
           AbstractTaggedPartitionableVertex.add_tag(self, tag)
