from pacman.model.constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint
from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
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
                constrained_vertices.append(subvertex)
            else:
                unconstrained_vertices.append(subvertex)

        #sort out unconstrained vertices so that they go in order of
        # most connected
        unconstrained_vertices = \
            self._sort_out_unconstrained_vertices_on_connectivity(
                unconstrained_vertices, partitioned_graph)

        sorted(unconstrained_vertices,
               key=lambda unc_sub_tuple: unc_sub_tuple[1])

        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(len(partitioned_graph.subvertices),
                                   "for placing the partitioned_graphs "
                                   "subvertices")

        for subvertex in constrained_vertices:
            # Create and store a new placement
            placement = self._place_subvertex(subvertex, placements)
            placements.add_placement(placement)
            progress_bar.update()

        #take the first and place, then look for most connected
        completed = dict()
        first = unconstrained_vertices[0]
        placement = self._place_subvertex(first[0], placements)
        placements.add_placement(placement)
        progress_bar.update()
        unconstrained_vertices.remove(first)
        self._append_all_subverts_connected_to(first, partitioned_graph,
                                               completed)

        #loop around locating next most connected to whats already placed
        #so that eventally theres none left
        while len(unconstrained_vertices) > 0:
            next_subvert = \
                self._locate_next_most_connected(unconstrained_vertices,
                                                 completed)
            placement = self._place_subvertex(next_subvert[0], placements)
            placements.add_placement(placement)
            progress_bar.update()
            unconstrained_vertices.remove(next_subvert)
            self._append_all_subverts_connected_to(
                next_subvert, partitioned_graph, completed)

        progress_bar.end()
        return placements

    @staticmethod
    def _locate_next_most_connected(unconstrained_vertices, completed):
        """locate the next based off whats already been placed

        :param unconstrained_vertices:
        :param completed:
        :return:
        """
        #no point cycling if theres only one entry
        if len(unconstrained_vertices) == 1:
            return unconstrained_vertices[0]

        max_so_far = None
        for unconstrained_vertex in unconstrained_vertices:
            current_value = 0
            for placed_subvert in completed.keys():
                if unconstrained_vertex[1] in completed[placed_subvert]:
                    current_value += unconstrained_vertex[1].n_atoms
            if max_so_far is None or max_so_far[0] < current_value:
                max_so_far = (current_value, unconstrained_vertex[1])

        #nothing connected to stuff already placed, locate next dense one
        if max_so_far[0] == 0:
            sorted(unconstrained_vertices,
               key=lambda unc_sub_tuple: unc_sub_tuple[1])
            return unconstrained_vertices[0]
        else:
            return max_so_far[1]

    @staticmethod
    def _append_all_subverts_connected_to(subvert, partitioned_graph,
                                          mapping):
        """helper method for figuing most connected

        :param subvert:
        :param partitioned_graph:
        :param mapping:
        :return:
        """
        in_edges = partitioned_graph.incoming_subedges_from_subvertex(subvert)
        mapping[subvert] = list()
        if in_edges is not None:
            for in_edge in in_edges:
                mapping[subvert].append(in_edge.pre_subvertex)

    @staticmethod
    def _sort_out_unconstrained_vertices_on_connectivity(
            unconstrained_vertices, partitioned_graph):
        """ helper method which takes the collection of subvertices and
         orders them based on whos msot connected

        :param unconstrained_vertices: the list of unordered unconstrained vertices
        :type iterable of pacman.partitioned_vertices.Partitioned_vertex
        :return: a list of un_constraiend_vertices
        """
        sorted_unconstrained_vertices = list()
        for subvertex in unconstrained_vertices:
            total_atoms = 0
            in_edges = \
                partitioned_graph.incoming_subedges_from_subvertex(subvertex)
            for in_edge in in_edges:
                total_atoms += in_edge.pre_subvertex.n_atoms
            sorted_unconstrained_vertices.append((subvertex, total_atoms))
        return sorted_unconstrained_vertices

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
