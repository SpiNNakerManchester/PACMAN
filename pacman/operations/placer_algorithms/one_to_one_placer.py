
# pacman imports
from pacman.model.constraints.abstract_constraints.\
    abstract_placer_constraint import \
    AbstractPlacerConstraint
from pacman.model.constraints.placer_constraints.\
    placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from pacman.model.constraints.placer_constraints.\
    placer_radial_placement_from_chip_constraint import \
    PlacerRadialPlacementFromChipConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_reverse_iptag_constraint import \
    TagAllocatorRequireReverseIptagConstraint
from pacman.model.placements.placements import Placements
from pacman.model.placements.placement import Placement
from pacman.operations.placer_algorithms import RadialPlacer
from pacman.utilities import utility_calls
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker

from spinn_machine.utilities.progress_bar import ProgressBar


class OneToOnePlacer(RadialPlacer):
    """ Placer that puts vertices which are directly connected to only its\
        destination on the same chip
    """

    MAX_CORES_PER_CHIP_TO_CONSIDER = 16

    def __init__(self):
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

        sorted_vertices = self._sort_vertices_for_one_to_one_connection(
            partitioned_graph)

        placements = Placements()

        self._do_allocation(sorted_vertices, placements, machine)

        return {'placements': placements}

    def _do_allocation(self, ordered_subverts, placements, machine):

        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(
            len(ordered_subverts), "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))

        # iterate over subverts
        for subvertex_list in ordered_subverts:

            # if too many one to ones to fit on a chip, allocate individually
            if len(subvertex_list) > self.MAX_CORES_PER_CHIP_TO_CONSIDER:
                for subvertex in subvertex_list:
                    self._allocate_individual(
                        subvertex, placements, progress_bar, resource_tracker)
            else:

                # try to allocate in one block
                group_resources = [
                    subvert.resources_required for subvert in subvertex_list]
                group_constraints = [
                    subvert.constraints for subvert in subvertex_list]

                try:
                    allocations = \
                        resource_tracker.allocate_constrained_group_resources(
                            group_resources, group_constraints)

                    # allocate cores to subverts
                    for subvert, (x, y, p, _, _) in zip(
                            subvertex_list, allocations):
                        placement = Placement(subvert, x, y, p)
                        placements.add_placement(placement)
                        progress_bar.update()
                except:

                    # If something goes wrong, try to allocate each
                    # individually
                    for subvertex in subvertex_list:
                        self._allocate_individual(
                            subvertex, placements, progress_bar,
                            resource_tracker)
        progress_bar.end()

    @staticmethod
    def _allocate_individual(
            subvertex, placements, progress_bar, resource_tracker):

        # Create and store a new placement anywhere on the board
        (x, y, p, _, _) = resource_tracker.\
            allocate_constrained_resources(
                subvertex.resources_required, subvertex.constraints)
        placement = Placement(subvertex, x, y, p)
        placements.add_placement(placement)
        progress_bar.update()

    def _sort_vertices_for_one_to_one_connection(
            self, partitioned_graph):
        """

        :param partitioned_graph: the partitioned graph of this application
        :return: list of sorted vertices
        """
        sorted_vertices = list()
        found_list = set()

        # order subverts based on constraint priority
        ordered_subverts = utility_calls.sort_objects_by_constraint_authority(
            partitioned_graph.subvertices)

        for vertex in ordered_subverts:
            incoming_edges = \
                partitioned_graph.incoming_subedges_from_subvertex(vertex)

            # do search if not already added and has incoming edges
            if vertex not in found_list and len(incoming_edges) != 0:
                chip_constraint = utility_calls.locate_constraints_of_type(
                    vertex.constraints, PlacerChipAndCoreConstraint)

                if len(chip_constraint) != 0:

                    # if has constraint, add first then add incoming
                    one_to_one_incoming_edges = list()
                    one_to_one_incoming_edges.append(vertex)
                    sorted_vertices.append(one_to_one_incoming_edges)
                    found_list.append(vertex)
                    self.check_incoming_verts(
                        one_to_one_incoming_edges, vertex, partitioned_graph,
                        found_list)
                else:

                    # if no constraint add incoming then first
                    one_to_one_incoming_edges = list()
                    sorted_vertices.append(one_to_one_incoming_edges)
                    self.check_incoming_verts(
                        one_to_one_incoming_edges, vertex, partitioned_graph,
                        found_list)
                    one_to_one_incoming_edges.append(vertex)
                    found_list.append(vertex)

        # locate vertices which have no output or input, and add them for
        # placement
        for vertex in ordered_subverts:
            if vertex not in found_list:
                listed_vertex = list()
                listed_vertex.append(vertex)
                sorted_vertices.append(listed_vertex)
        return sorted_vertices

    @staticmethod
    def check_incoming_verts(one_to_one_verts, vertex, partitioned_graph,
                             found_list):
        """ Adds subverts which have a one to one connection
        :param one_to_one_verts: the list of sorted vertices
        :param vertex: the destination vertex
        :param partitioned_graph: the partitioned graph
        :param found_list: the list of found vertices so far
        :return:
        """

        # locate incoming edges for this vertex
        incoming_edges = \
            partitioned_graph.incoming_subedges_from_subvertex(vertex)

        # locate constraints of chip and core for this vertex
        chip_constraint = utility_calls.locate_constraints_of_type(
            vertex.constraints, PlacerChipAndCoreConstraint)

        for incoming_edge in incoming_edges:
            incoming_vert = incoming_edge.pre_subvertex
            number_of_outgoing_edges = partitioned_graph.\
                outgoing_subedges_from_subvertex(incoming_vert)

            # if only one outgoing edge, decide to put it in same chip pile
            if (len(number_of_outgoing_edges) == 1 and
                    incoming_vert not in found_list):

                if len(chip_constraint) != 0:

                    # if the vertex has no constraint, put in
                    one_to_one_verts.append(incoming_vert)
                    found_list.append(incoming_vert)
                else:

                    # if constraint exists, try to satisfy constraints.
                    chip_constraint_incoming = \
                        utility_calls.locate_constraints_of_type(
                            incoming_vert.constraints,
                            PlacerChipAndCoreConstraint)
                    if len(chip_constraint_incoming) == 0:
                        one_to_one_verts.append(incoming_vert)
                        found_list.append(incoming_vert)
                    else:
                        x_level = chip_constraint[0].x == \
                            chip_constraint_incoming[0].x
                        y_level = chip_constraint[0].y == \
                            chip_constraint_incoming[0].y
                        p_level = chip_constraint[0].p != \
                            chip_constraint_incoming[0].p
                        if x_level and y_level and p_level:
                            one_to_one_verts.append(incoming_vert)
                            found_list.append(incoming_vert)
