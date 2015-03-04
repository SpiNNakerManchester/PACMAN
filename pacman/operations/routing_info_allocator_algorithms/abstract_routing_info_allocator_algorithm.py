from abc import ABCMeta
from abc import abstractmethod
from collections import OrderedDict
from six import add_metaclass

from pacman.utilities import utility_calls

from pacman.exceptions import PacmanValueError

from pacman.model.constraints.key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.constraints.key_allocator_fixed_mask_constraint \
    import KeyAllocatorFixedMaskConstraint
from pacman.model.constraints.key_allocator_fixed_key_and_mask_constraint \
    import KeyAllocatorFixedKeyAndMaskConstraint
from pacman.model.constraints.key_allocator_same_keys_constraint \
    import KeyAllocatorSameKeysConstraint
from pacman.utilities.ordered_set import OrderedSet


@add_metaclass(ABCMeta)
class AbstractRoutingInfoAllocatorAlgorithm(object):
    """ An abstract algorithm that can produce routing keys and masks for\
        subedges in a partitioned_graph
    """

    def __init__(self):
        self._supported_constraints = list()

    @staticmethod
    def _get_edge_groups(partitioned_graph):
        """ Utility method to get groups of partitioned edges using any\
            :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorSameKeyConstraint`\
            constraints.  Note that no checking is done here about conflicts\
            related to other constraints.
        """

        # Keep a dictionary of the group which contains an edge
        same_key_groups = OrderedDict()

        for partitioned_edge in partitioned_graph.subedges:
            same_key_constraints = utility_calls.locate_constraints_of_type(
                partitioned_edge.constraints, KeyAllocatorSameKeysConstraint)
            if len(same_key_constraints) != 0:

                # If there are some constraints on this edge,
                # Find any existing groups containing the item
                found_groups = list()
                found_edges = set()
                for same_key_constraint in same_key_constraints:
                    edge_to_match = \
                        same_key_constraint.partitioned_edge_to_match
                    found_edges.add(edge_to_match)
                    if edge_to_match in same_key_groups:
                        found_groups.append(same_key_groups[edge_to_match])

                # Check if the current edge is already in a group
                found_edges.add(partitioned_edge)
                if partitioned_edge in same_key_groups:
                    found_groups.append(same_key_groups[partitioned_edge])

                if len(found_groups) == 0:

                    # If there is no group, create a group
                    for edge in found_edges:
                        same_key_groups[edge] = found_edges

                elif len(found_groups) == 1:

                    # If there is one group, just add to that
                    group_to_add_to = found_groups[0]
                    group_to_add_to.update(found_edges)
                    for edge in found_edges:
                        same_key_groups[edge] = group_to_add_to

                else:

                    # NOTE: this state should never occur, but if we do then.
                    # we must merge the groups already found
                    new_group = set()
                    for group in found_groups:
                        new_group.update(group)
                    for edge in found_edges:
                        same_key_groups[edge] = new_group

            elif partitioned_edge not in same_key_groups:

                # Otherwise, if the edge is not in a group,
                # put it in a new group by itself
                same_key_groups[partitioned_edge] = set([partitioned_edge])

        # Reduce the dictionary into a set of groups (in-mutabable)
        return OrderedSet(frozenset(group)
                          for group in same_key_groups.itervalues())

    @staticmethod
    def _is_contiguous_range(same_key_group):
        """ Determine if any edge in the group has a\
            :py:class:`pacman.model.constraints.key_allocator_contiguous_range_constraint.KeyAllocatorContiguousRangeContraint`

        :param same_key_group: Set of partitioned edges that are to be\
                    assigned the same keys and masks
        :type same_key_group: iterable of\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :return: True if the range should be contiguous
        """
        for edge in same_key_group:
            constraints = utility_calls.locate_constraints_of_type(
                edge.constraints, KeyAllocatorContiguousRangeContraint)
            if len(constraints) > 0:
                return True
        return False

    @staticmethod
    def _get_fixed_mask(same_key_group):
        """ Get a fixed mask from a group of partitioned edges if a\
            :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorFixedMaskConstraint`\
            constraint exists in any of the edges in the group.

        :param same_key_group: Set of partitioned edges that are to be\
                    assigned the same keys and masks
        :type same_key_group: iterable of\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :return: The fixed mask if found, or None
        :raise PacmanValueError: If two edges conflict in their requirements
        """
        mask = None
        edge_with_mask = None
        for edge in same_key_group:
            fixed_mask_constraints = utility_calls.locate_constraints_of_type(
                edge.constraints, KeyAllocatorFixedMaskConstraint)
            for fixed_mask_constraint in fixed_mask_constraints:
                if mask is not None and mask != fixed_mask_constraint.mask:
                    raise PacmanValueError(
                        "Two Partitioned Edges {} and {} must have the same"
                        " key and mask, but have different fixed masks,"
                        " {} and {}".format(edge, edge_with_mask, mask,
                                            fixed_mask_constraint.mask))

                mask = fixed_mask_constraint.mask
                edge_with_mask = edge

        return mask

    @staticmethod
    def _get_fixed_key_and_mask(same_key_group):
        """ Gets a fixed key and mask from a group of partitioned edges if a\
            :py:class:`pacman.model.constraints.key_allocator_same_key_constraint.KeyAllocatorFixedKeyAndMaskConstraint`\
            constraint exists in any of the edges in the group.

        :param same_key_group: Set of partitioned edges that are to be\
                    assigned the same keys and masks
        :type same_key_group: iterable of\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :raise PacmanValueError: If two edges conflict in their requirements
        """
        keys_and_masks = None
        edge_with_key_and_mask = None
        for edge in same_key_group:
            constraints = utility_calls.locate_constraints_of_type(
                edge.constraints, KeyAllocatorFixedKeyAndMaskConstraint)
            for constraint in constraints:

                # Check for conflicts
                if (keys_and_masks is not None
                        and keys_and_masks != constraint.keys_and_masks):
                    raise PacmanValueError(
                        "Two Partitioned Edges {} and {} must have the same"
                        " key and mask, but have different fixed key and"
                        " masks, {} and {}".format(
                            edge, edge_with_key_and_mask, keys_and_masks,
                            constraint.keys_and_masks))
                print constraint
                keys_and_masks = constraint.keys_and_masks
                edge_with_key_and_mask = edge

        return keys_and_masks

    @abstractmethod
    def allocate_routing_info(self, subgraph, placements, n_keys_map):
        """ Allocates routing information to the partitioned edges in a\
            partitioned graph

        :param subgraph: The partitioned graph to allocate the routing info for
        :type subgraph:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :param placements: The placements of the subvertices
        :type placements:\
                    :py:class:`pacman.model.placements.placements.Placements`
        :param n_keys_map: A map between the partitioned edges and the number\
                    of keys required by the edges
        :type n_keys_map:\
                    :py:class:`pacman.model.routing_info.abstract_partitioned_edge_n_keys_map.AbstractPartitionedEdgeNKeysMap`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """
