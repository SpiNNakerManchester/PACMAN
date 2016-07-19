import logging
from pacman.utilities.algorithm_utilities import placer_algorithm_utilities

from pacman.model.constraints.placer_constraints.abstract_placer_constraint \
    import AbstractPlacerConstraint
from pacman.model.placements.placements import Placements
from pacman.operations.placer_algorithms.radial_placer import RadialPlacer
from pacman.utilities import utility_calls
from spinn_machine.utilities.progress_bar import ProgressBar
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
        self._check_constraints(partitioned_graph.vertices)

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
        constrained_vertices = \
            placer_algorithm_utilities.sort_vertices_by_known_constraints(
                constrained_vertices)
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
        return placements

    def _find_max_connected_vertex(self, vertices, partitioned_graph):
        max_connected_vertex = None
        max_weight = 0
        for vertex in vertices:
            in_weight = sum([
                edge.weight
                for edge in partitioned_graph.outgoing_subedges_from_subvertex(
                    vertex)])
            out_weight = sum([
                edge.weight
                for edge in partitioned_graph.incoming_subedges_from_subvertex(
                    vertex)])
            weight = in_weight + out_weight

            if max_connected_vertex is None or weight > max_weight:
                max_connected_vertex = vertex
                max_weight = weight
        return max_connected_vertex
