from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint
from pacman.utilities.placement_tracker import PlacementTracker
from pacman.utilities.sdram_tracker import SDRAMTracker
from pacman import exceptions


import logging
logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPlacerAlgorithm(object):
    """ An abstract algorithm that can place a subgraph
    """
    def __init__(self, machine, graph):
        """constrcutor for the abstract placer algorithum
        :param machine: The machine on which to place the graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        self._placement_tracker = PlacementTracker(machine)
        self._sdram_tracker = SDRAMTracker()
        self._graph = graph
        self._supported_constrants = list()

    @abstractmethod
    def place(self, subgraph, graph_to_subgraph_mapper):
        """ Place a subgraph so that each subvertex is placed on a core
            
        :param subgraph: The subgraph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param graph_to_subgraph_mapper: the mappings between graph and subgraph
        :type graph_to_subgraph_mapper:
        pacman.model.graph_subgraph_mapper.graph_subgraph_mapper.GraphSubgraphMapper
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """

    @staticmethod
    def sort_subverts_by_constraint_authority(subvertices):
        """helper method for all placers. \
        It takes the subverts of a subgraph and orders them into a list with a
        order based off rank on the constraint
        :param subvertices: The subvertices of the subgraph
        :type subvertices: iterable of pacman.model.subgraph.subvertex.SubVertex
        :return: A list of ordered subverts
        :rtype: list of :py:class:`pacman.model.subgraph.subvertex.SubVertex'
        :raise None: this method does not raise any known exceptions
        """
        rank_to_subvert_mapping = dict()
        for subvert in subvertices:
            max_rank_so_far = 0
            for constraint in subvert.constraints:
                #only store ranks for placer contraints and ones that are better
                #than already seen
                if (constraint.rank >= max_rank_so_far
                        and isinstance(constraint, AbstractPlacerConstraint)):
                    max_rank_so_far = constraint.rank
            if not max_rank_so_far in rank_to_subvert_mapping.keys():
                rank_to_subvert_mapping[max_rank_so_far] = list()
            rank_to_subvert_mapping[max_rank_so_far].append(subvert)

        ordered_keys = \
            sorted(rank_to_subvert_mapping.keys(), key=int, reverse=True)
        ordered_subverts = list()
        for ordered_key in ordered_keys:
            subvert_list = rank_to_subvert_mapping[ordered_key]
            for subvert in subvert_list:
                ordered_subverts.append(subvert)
        return ordered_subverts

    def _check_can_support_constraints(self, subgraph):
        """checks that the constraints on the vertices in the graph are all
        supported by the given implimentation of the partitioner.

        :param subgraph: The subgraph to place from
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.SubGraph`
        :raise pacman.exceptions.PacmanPartitionException: if theres a
        constraint in the vertices in the graph to which this implemntation
        of the partitioner cannot handle
        """
        for subvert in subgraph.subvertices:
            for constraint in subvert.constraints:
                if isinstance(constraint, AbstractPlacerConstraint):
                    located = False
                    for supported_constraint in self._supported_constrants:
                        if isinstance(constraint, supported_constraint):
                            located = True
                    if not located:
                        raise exceptions.PacmanPartitionException(
                            "the placing algorithum selected cannot support "
                            "the placment constraint '{}', which has been "
                            "placed on subvert labelled {}"
                            .format(constraint, subvert.label))
