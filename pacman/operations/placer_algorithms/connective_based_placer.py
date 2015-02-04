from pacman.model.constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint
from pacman.model.placements.placements import Placements
from pacman.operations.placer_algorithms.radial_placer import RadialPlacer
from pacman.utilities import utility_calls
from pacman.utilities.progress_bar import ProgressBar

import logging
import math

logger = logging.getLogger(__name__)


class ConnectiveBasedPlacer(RadialPlacer):
    """ An radial algorithm that can place a partitioned_graph onto a
     machine based off a circle out behaviour from a ethernet at a given point
     and which will place highly connected cores on the same chip or close by"""

    def __init__(self, machine):
        """constructor to build a
        pacman.operations.placer_algorithms.RadialPlacer.RadialPlacer
        :param machine: The machine on which to place the partitionable_graph
        :type machine: :py:class:`spinn_machine.machine.Machine`
        """
        RadialPlacer.__init__(self, machine)

    def place(self, partitioned_graph):
        """ Place a partitioned_graph so that each subvertex is placed on a core

        :param partitioned_graph: The partitioned_graph to place
        :type partitioned_graph:
        :py:class:
        `pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :return: A set of placements
        :rtype: :py:class:`pacman.model.placements.placements.Placements`
        :raise pacman.exceptions.PacmanPlaceException: If something\
                   goes wrong with the placement
        """
        #check that the algorithm can handle the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=partitioned_graph.subvertices,
            supported_constraints=self._supported_constraints,
            abstract_constraint_type=AbstractPlacerConstraint)

        placements = Placements()
        constrained_vertices = list()
        unconstrained_vertices = list()
        for subvertex in partitioned_graph.subvertices:
            placement_constraints =\
                utility_calls.locate_constraints_of_type(
                    subvertex.constraints, AbstractPlacerConstraint)
            if len(placement_constraints) > 0:
                real_constrained = False
                for placement_constraint in placement_constraints:




        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(len(ordered_subverts),
                                   "for placing the partitioned_graphs "
                                   "subvertices")

        for subvertex in ordered_subverts:
            # Create and store a new placement
            placement = self._place_subvertex(subvertex, placements)
            placements.add_placement(placement)
            progress_bar.update()
        progress_bar.end()
        return placements

    def _try_to_place(self, placement_constraints, resources, subvert_label,
                      placements):
        """helper method for partitioners
        :param placement_constraints: the placement constraints of a vertex
        :param resources: the sdram, cpu and dctm usage of the subvertex
        :param subvert_label: the label of the subvert
        :param placements: the placement container
        :type placements: pacman.model.placements.placements.Placements
        :type resources: pacman.model.resources.resource_container.ResourceContainer
        :type placement_constraints: iterable of implementations of
        pacaman.model.constraints.abstractPlacementConstraint
        :type subvert_label: str
        :return: the x,y,p coord of the placement
        :rtype: int, int, int
        :raise None: this method does not raise any known exceptions
        """
        placement_constraint = \
            self._reduce_constraints(placement_constraints, subvert_label,
                                     placements)

        #locate middle of the machine to start radial placement off at
        machine_max_x = self._machine.max_chip_x
        machine_max_y = self._machine.max_chip_y

        middle_x = math.floor(machine_max_x / 2)
        middle_y = math.floor(machine_max_y / 2)

        #if there's a placement constraint, then check out the chip and only
        # that chip
        if placement_constraint is not None:
            return self._deal_with_constraint_placement(placement_constraint,
                                                        subvert_label,
                                                        resources)
        else:
            chips = self._machine.chips
            return self._deal_with_non_constrained_placement(
                subvert_label, resources, chips, middle_x, middle_y)
