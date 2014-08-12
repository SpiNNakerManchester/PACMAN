from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_subvertex_same_chip_constraint import \
    PlacerSubvertexSameChipConstraint
from pacman.utilities.placement_tracker import PlacementTracker
from pacman.utilities.sdram_tracker import SDRAMTracker
from pacman import exceptions


import logging
logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPlacerAlgorithm(object):
    """ An abstract algorithm that can place a partitioned_graph
    """
    def __init__(self, machine, graph):
        """constrcutor for the abstract placer algorithm
        :param machine: The machine on which to place the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        self._placement_tracker = PlacementTracker(machine)
        self._machine = machine
        self._sdram_tracker = SDRAMTracker()
        self._graph = graph
        self._supported_constraints = list()

    @abstractmethod
    def place(self, subgraph, graph_mapper):
        """ Place a partitioned_graph so that each subvertex is placed on a core
            
        :param subgraph: The partitioned_graph to place
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param graph_mapper: the mappings between partitionable_graph and \
        partitioned_graph
        :type graph_mapper:
    pacman.model.graph_mapper.graph_mapper.GraphMapper
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """

    def _reduce_constraints(self, constraints, subvertex_label, placements):
        """ tries to reduce the placement constraints into one manageable one.\
        NOT CALLABLE OUTSIDE CLASSES TAHT INHIRRIT FROM THIS ONE

        :param constraints: the constraints placed on a vertex
        :param subvertex_label: the label from a given subvertex
        :param placements: the current list of placements
        :type constraints: iterable list of pacman.model.constraints.AbstractConstraints
        :type subvertex_label: str
        :type placements: iterable of pacman.model.placements.placement.Placement
        :return a reduced placement constraint
        :rtype: pacman.model.constraints.PlacerChipAndCoreConstraint
        :raise None: does not raise any known exception
        """

        x = None
        y = None
        p = None
        for constraint in constraints:
            if type(constraint) == type(PlacerChipAndCoreConstraint(0, 0)):
                x = self._check_param(constraint.x, x, subvertex_label)
                y = self._check_param(constraint.y, y, subvertex_label)
                p = self._check_param(constraint.p, p, subvertex_label)
            elif type(constraint) == type(PlacerSubvertexSameChipConstraint(None)):
                other_subvertex = constraint.subvertex
                other_placement = \
                    placements.get_placement_of_subvertex(other_subvertex)
                if other_placement is not None:
                    x = self._check_param(constraint.x, other_placement.x,
                                          subvertex_label)
                    y = self._check_param(constraint.y, other_placement.y,
                                          subvertex_label)
                    p = self._check_param(constraint.p, other_placement.p,
                                          subvertex_label)
                x = self._check_param(constraint.x, x, subvertex_label)
                y = self._check_param(constraint.y, y, subvertex_label)
                p = self._check_param(constraint.p, p, subvertex_label)
        if x is not None and y is not None:
            return PlacerChipAndCoreConstraint(x, y, p)
        else:
            return None

    @staticmethod
    def _check_param(param_to_check, param_to_update, subvertex_label):
        """ checks if constraints with overlapping requirements are satisifable\
        NOT CALLABLE OUTSIDE CLASSES TAHT INHIRRIT FROM THIS ONE

        :param param_to_check: a param to verify
        :param param_to_update: a second param to verify
        :param subvertex_label: the label fo the subvertex
        :type param_to_check: int
        :type param_to_update: int
        :type subvertex_label: str
        :return: the updated value of the param
        :rtype: int
        :raise PacmanPlaceException: when the param has been set and to a \
        different value. This is becuase being set to a different value makes \
        both constraints insatisifable

        """
        if param_to_check is not None:
            if param_to_update is None:
                param_to_update = param_to_check
            elif param_to_update != param_to_check:
                raise exceptions.PacmanPlaceException(
                    "there are conflicting placement constraints which "
                    "together cannot be satifisied for subvertex {}"
                    .format(subvertex_label))
        return param_to_update