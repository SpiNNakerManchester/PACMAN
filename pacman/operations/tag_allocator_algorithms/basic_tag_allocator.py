from pacman import exceptions
from pacman.model.constraints.\
    tag_allocator_constraints.tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint
from pacman.model.tag_infos.tag_infos import TagInfos
from pacman.operations.abstract_algorithms.\
    abstract_tag_allocator_algorithm import AbstractTagAllocatorAlgorithm
from pacman.utilities import utility_calls


class BasicTagAllocator(AbstractTagAllocatorAlgorithm):

    def __init__(self, machine):
        AbstractTagAllocatorAlgorithm.__init__(self, machine)
        self._tag_infos = TagInfos()

    def allocate(self, placements):
        """

        :param placements:
        :return:
        """

        avilable_tag_ids = self._locate_all_seperate_ethernet_connections()
        # iterate though the vertices and set tags which have tag ids set
        for placement in placements.placements:
            tag_allocator_constraints = \
                utility_calls.locate_constraints_of_type(
                    placement.subvertex.constraints, TagAllocatorRequireIptagConstraint)
            if len(tag_allocator_constraints) > 0:
                for tag_allocator_constraint in tag_allocator_constraints:
                    tag_id = tag_allocator_constraint.tag
                    if tag_id is not None:
                        board_address = tag_allocator_constraint.board_address
                        tag_id, board_address = self._check_tag(
                            tag_id, board_address, avilable_tag_ids)
                        self._set_tag(placement, tag_allocator_constraint,
                                      board_address, tag_id)

        # iterate though the vertices and set tags which have no tag id set
        for vertex in self._partitionable_graph.vertices:
            tag_allocator_constraint = \
                utility_calls.locate_constraints_of_type(vertex.constraints,
                                                         TagAllocatorRequireIptagConstraint)
            if len(tag_allocator_constraint) > 0:
                tag_id = vertex.tag()
                if tag_id is None:
                    board_address = vertex.board_address
                    tag, board_address = self._check_tag(tag_id, board_address,
                                                         avilable_tag_ids)
                    vertex.tag = tag
                    vertex.board_address = board_address
                    self._set_tag(vertex, tag_allocator_constraint)
        return self._tag_infos

    def _set_tag(self, vertex, constraint):

        if isinstance(vertex, AbstractIPTagableVertex):
            self._add_iptag(IPTag(port=vertex.port, address=vertex.address,
                                  tag=vertex.tag,
                                  board_address=vertex.board_address))
        elif isinstance(vertex, AbstractReverseIPTagableVertex):
            subverts = self._graph_mapper.get_subvertices_from_vertex(vertex)
            if len(subverts) > 1:
                raise exceptions.PacmanConfigurationException(
                    "reverse iptaggable populations can only be supported if "
                    "they are partitoned in a 1 to 1 ratio. Please reduce the "
                    "number of neurons per core, or the max-atoms per core to"
                    " support a one core mapping for your iptaggable"
                    " population.")
            subvert = next(iter(subverts))
            placement = self._placements.get_placement_of_subvertex(subvert)
            self._add_reverse_tag(ReverseIPTag(
                port=vertex.port, tag=vertex.tag, destination_x=placement.x,
                destination_y=placement.y, destination_p=placement.p,
                board_address=vertex.board_address))

    def is_tag_allocator(self):
        """

        :return:
        """
        return True

    @staticmethod
    def _check_tag(tag_id, board_address, avilable_tag_ids):
        """

        :param tag_id:
        :param board_address:
        :param avilable_tag_ids:
        :return:
        """
        #check that board address is a connected ethernet
        if (board_address is not None
                and board_address not in avilable_tag_ids.keys()):
            raise exceptions.PacmanConfigurationException(
                "This board address is not one of the listed connected"
                "ethernets, please fix this and try again")

        # fixed in both board and tag
        if tag_id is not None and board_address is not None:
            if tag_id in avilable_tag_ids[board_address]:
                avilable_tag_ids[board_address].remove(tag_id)
                return tag_id, board_address
            else:
                raise exceptions.PacmanConfigurationException(
                    "This tag has already been used by some other iptag, please"
                    "correct this and try again")

        # fixed in tag id but not in board ( not sure if this is needed )
        elif tag_id is not None and board_address is None:
            key_index = 0
            while key_index < len(avilable_tag_ids.keys()):
                key = avilable_tag_ids.keys()[key_index]
                if tag_id in avilable_tag_ids[key]:
                    avilable_tag_ids[key].remove(tag_id)
                    return tag_id, key
                key_index += 1
            raise exceptions.PacmanConfigurationException(
                "Could not locate any connection which has this tag free, "
                "please rectify and try again")

        # none fixed tag id and fixed board
        elif tag_id is None and board_address is not None:
            if len(avilable_tag_ids[board_address]) == 0:
                raise exceptions.PacmanConfigurationException(
                    "This board no longer has any tags left, please rectify "
                    "and try again")
            else:
                return avilable_tag_ids[board_address].pop(), board_address

        # no fixed tag nor fixed board (easiest)
        elif tag_id is None and board_address is None:
            key_index = 0
            while key_index < len(avilable_tag_ids.keys()):
                key = avilable_tag_ids.keys()[key_index]
                if len(avilable_tag_ids[key]) != 0:
                    return avilable_tag_ids[board_address].pop(), key
                key_index += 1
            raise exceptions.PacmanConfigurationException(
                "There is no more tags avilable, therefore cannot allocate a "
                "tag, please rectify and try again")
        else:
            raise exceptions.PacmanConfigurationException(
                "dont know how i got here. But theres some form of tag "
                "configuration that i dont recongise. Please rectify and "
                "try again.")