import logging

from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_constraints\
    .placer_radial_placement_from_chip_constraint import \
    PlacerRadialPlacementFromChipConstraint
from pacman.model.constraints.abstract_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_reverse_iptag_constraint import \
    TagAllocatorRequireReverseIptagConstraint
from pacman.model.placements.placements import Placements
from pacman.operations.placer_algorithms.radial_placer import RadialPlacer
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker

logger = logging.getLogger(__name__)


class ConnectiveBasedPlacer(RadialPlacer):
    """ A radial algorithm that can place a partitioned_graph onto a\
        machine using a circle out behaviour from a Ethernet at a given point\
        and which will place things that are most connected closest to each\
        other
    """

    def __init__(self):
        """
        """
        RadialPlacer.__init__(self)

    def __call__(self, partitioned_graph, machine):

        # check that the algorithm can handle the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=partitioned_graph.subvertices,
            supported_constraints=[
                PlacerRadialPlacementFromChipConstraint,
                TagAllocatorRequireIptagConstraint,
                TagAllocatorRequireReverseIptagConstraint,
                PlacerChipAndCoreConstraint],
            abstract_constraint_type=AbstractPlacerConstraint)

        # Sort the vertices into those with and those without
        # placement constraints
        placements = Placements()
        constrained_vertices = list()
        unconstrained_vertices = set()
        for subvertex in partitioned_graph.subvertices:
            placement_constraints = utility_calls.locate_constraints_of_type(
                subvertex.constraints, AbstractPlacerConstraint)
            if len(placement_constraints) > 0:
                constrained_vertices.append(subvertex)
            else:
                unconstrained_vertices.add(subvertex)

        # Iterate over constrained vertices and generate placements
        progress_bar = ProgressBar(len(partitioned_graph.subvertices),
                                   "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))
        for vertex in constrained_vertices:
            self._place_vertex(vertex, resource_tracker, machine, placements)
            progress_bar.update()

        while len(unconstrained_vertices) > 0:

            # Keep track of all vertices connected to the currently placed ones
            next_vertices = set()

            # Initially, add the overall most connected vertex
            max_connected_vertex = self._find_max_connected_vertex(
                unconstrained_vertices, partitioned_graph)
            next_vertices.add(max_connected_vertex)

            while len(next_vertices) > 0:

                # Find the vertex most connected to the currently placed
                # vertices
                vertex = self._find_max_connected_vertex(next_vertices,
                                                         partitioned_graph)

                # Place the vertex
                self._place_vertex(vertex, resource_tracker, machine,
                                   placements)
                progress_bar.update()
                unconstrained_vertices.remove(vertex)
                next_vertices.remove(vertex)

                # Add all vertices connected to this one to the set
                for in_edge in (partitioned_graph
                                .incoming_subedges_from_subvertex(vertex)):
                    if in_edge.pre_subvertex in unconstrained_vertices:
                        next_vertices.add(in_edge.pre_subvertex)
                for out_edge in (partitioned_graph
                                 .outgoing_subedges_from_subvertex(vertex)):
                    if out_edge.post_subvertex in unconstrained_vertices:
                        next_vertices.add(out_edge.post_subvertex)
        # finished, so stop progress bar and return placements
        progress_bar.end()
        return {'placements': placements}

    def _find_max_connected_vertex(self, vertices, partitioned_graph):
        max_connected_vertex = None
        max_n_edges = 0
        for vertex in vertices:
            n_in_edges = len(
                partitioned_graph.outgoing_subedges_from_subvertex(vertex))
            n_out_edges = len(
                partitioned_graph.incoming_subedges_from_subvertex(vertex))
            n_edges = n_in_edges + n_out_edges

            if max_connected_vertex is None or n_edges > max_n_edges:
                max_connected_vertex = vertex
                max_n_edges = n_edges
        return max_connected_vertex
