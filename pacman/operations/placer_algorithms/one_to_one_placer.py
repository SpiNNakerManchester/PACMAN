
# pacman imports
from pacman.model.constraints.abstract_constraints.\
    abstract_placer_constraint import \
    AbstractPlacerConstraint
from pacman.model.constraints.placer_constraints.\
    placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from pacman.model.placements.placements import Placements
from pacman.model.placements.placement import Placement
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker


class OneToOnePlacer(object):
    """
    one to one placer puts vertices which are directly connected to only its
    destination on the same chip
    """

    def __call__(self, partitioned_graph, machine):

        sorted_vertices = self._sort_vertices_for_ease_of_one_to_one_connection(
            partitioned_graph)

        # check that the algorithm can handle the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=partitioned_graph.subvertices,
            supported_constraints=[PlacerChipAndCoreConstraint],
            abstract_constraint_type=AbstractPlacerConstraint)

        placements = Placements()
        ordered_subverts = utility_calls.sort_objects_by_constraint_authority(
            partitioned_graph.subvertices)

        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(len(ordered_subverts),
                                   "Placing graph vertices")
        resource_tracker = ResourceTracker(machine)
        for subvertex in ordered_subverts:

            # Create and store a new placement anywhere on the board
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                subvertex.resources_required, subvertex.constraints)
            placement = Placement(subvertex, x, y, p)
            placements.add_placement(placement)
            progress_bar.update()
        progress_bar.end()
        return {'placements': placements}

    def _sort_vertices_for_ease_of_one_to_one_connection(
            self, partitioned_graph):
        """

        :param partitioned_graph: the partitioned graph of this application
        :return: list of sorted vertices
        """
        sorted_vertices = list()

        ordered_subverts = utility_calls.sort_objects_by_constraint_authority(
            partitioned_graph.subvertices)

        for vertex in ordered_subverts:
            if vertex not in sorted_vertices:
                chip_constraint = utility_calls.locate_constraints_of_type(
                    vertex.constraints, PlacerChipAndCoreConstraint)
                if len(chip_constraint) != 0:
                    sorted_vertices.append(vertex)
                    self.check_incoming_verts(
                        sorted_vertices, vertex, partitioned_graph)
                else:
                    self.check_incoming_verts(
                        sorted_vertices, vertex, partitioned_graph)
                    sorted_vertices.append(vertex)
        return sorted_vertices

    @staticmethod
    def check_incoming_verts(sorted_vertices, vertex, partitioned_graph):
        """
        adds subverts which have a one to one connection
        :param sorted_vertices: the list of sorted vertices
        :param vertex: the destination vertex
        :param partitioned_graph: the partitioned graph
        :return:
        """
        incoming_edges = \
            partitioned_graph.incoming_subedges_from_subvertex(vertex)
        if len(incoming_edges) != 0:
            for incoming_edge in incoming_edges:
                incoming_vert = incoming_edge.pre_subvertex
                number_of_outgoing_edges = incoming_vert.\
                    outgoing_subedges_from_subvertex(incoming_vert)
                if len(number_of_outgoing_edges) == 1:
                    sorted_vertices.append(incoming_vert)