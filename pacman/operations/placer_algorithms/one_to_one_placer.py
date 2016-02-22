
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
from pacman.utilities.utility_objs.progress_bar import ProgressBar
from pacman.utilities.utility_objs.resource_tracker import ResourceTracker
from pacman import exceptions


class OneToOnePlacer(RadialPlacer):
    """
    one to one placer puts vertices which are directly connected to only its
    destination on the same chip
    """

    MAX_CORES_PER_CHIP_TO_CONSIDER = 16

    def __init__(self):
        RadialPlacer.__init__(self)

    def __call__(self, partitioned_graph, machine):

        sorted_vertices = self._sort_vertices_for_ease_of_one_to_one_connection(
            partitioned_graph)

        # check that the algorithm can handle the constraints
        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=partitioned_graph.subvertices,
            supported_constraints=[
                PlacerRadialPlacementFromChipConstraint,
                TagAllocatorRequireIptagConstraint,
                TagAllocatorRequireReverseIptagConstraint,
                PlacerChipAndCoreConstraint],
            abstract_constraint_type=AbstractPlacerConstraint)

        placements = Placements()

        self._do_allocation(sorted_vertices, placements, machine)

        return {'placements': placements}

    def _do_allocation(self, ordered_subverts, placements, machine):
        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(len(ordered_subverts),
                                   "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))

        # iterate over subverts
        for subvertex_list in ordered_subverts:

            # if too many one to ones to fit on a chip, allocate individually
            if len(subvertex_list) > self.MAX_CORES_PER_CHIP_TO_CONSIDER:
                for subvertex in subvertex_list:
                    self._allocate_individual(
                        subvertex, placements, progress_bar, resource_tracker)
            else:  # can allocate in one block

                # merge constraints
                placement_constraint, ip_tag_constraints, \
                    reverse_ip_tag_constraints = \
                    self._merge_constraints(subvertex_list)
                # locate most cores on a chip
                max_size_on_a_chip = resource_tracker.\
                    max_available_cores_on_chips_that_satisfy(
                        placement_constraint, ip_tag_constraints,
                        reverse_ip_tag_constraints)

                # if size fits block allocate, otherwise allocate individually
                if max_size_on_a_chip < len(subvertex_list):

                    # collect resource requirement
                    resources = list()
                    for subvert in subvertex_list:
                        resources.append(subvert.resources_required)

                    # get cores
                    cores = resource_tracker.allocate_group(
                        resources, placement_constraint, ip_tag_constraints,
                        reverse_ip_tag_constraints)

                    # allocate cores to subverts
                    for subvert, (x, y, p, _, _) in zip(subvertex_list, cores):
                        placement = Placement(subvert, x, y, p)
                        placements.add_placement(placement)
                        progress_bar.update()
                else:
                    for subvertex in subvertex_list:
                        self._allocate_individual(
                            subvertex, placements, progress_bar,
                            resource_tracker)
        progress_bar.end()

    @staticmethod
    def _merge_constraints(subvertex_list):
        merged_placement = None
        ip_tag = list()
        reverse_ip_tags = list()
        for subvertex in subvertex_list:
            place_constraints = utility_calls.locate_constraints_of_type(
                subvertex.constraints, PlacerChipAndCoreConstraint)
            ip_tag_constraints = utility_calls.locate_constraints_of_type(
                subvertex.constraints, TagAllocatorRequireIptagConstraint)
            ip_tag.extend(ip_tag_constraints)
            reverse_ip_tag = utility_calls.locate_constraints_of_type(
                subvertex.constraints,
                TagAllocatorRequireReverseIptagConstraint)
            reverse_ip_tags.extend(reverse_ip_tag)
            if len(place_constraints) != 0:
                for place_constraint in place_constraints:
                    if merged_placement is None:
                        merged_placement = place_constraint
                    else:
                        x_level = merged_placement.x == \
                            place_constraint.x
                        y_level = merged_placement.y == \
                            place_constraint.y
                        p_level = merged_placement.p != \
                            place_constraint.p
                        if not x_level or not y_level or not p_level:
                            raise exceptions.PacmanConfigurationException(
                                "cant handle these conflicting constraints")
        return merged_placement, ip_tag, reverse_ip_tags

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

    def _sort_vertices_for_ease_of_one_to_one_connection(
            self, partitioned_graph):
        """

        :param partitioned_graph: the partitioned graph of this application
        :return: list of sorted vertices
        """
        sorted_vertices = list()
        found_list = list()

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

                # if has constraint, add first then add incoming
                if len(chip_constraint) != 0:
                    one_to_one_incoming_edges = list()
                    one_to_one_incoming_edges.append(vertex)
                    sorted_vertices.append(one_to_one_incoming_edges)
                    found_list.append(vertex)
                    self.check_incoming_verts(
                        one_to_one_incoming_edges, vertex, partitioned_graph,
                        found_list)
                else:  # if no constraint add incoming then first
                    one_to_one_incoming_edges = list()
                    sorted_vertices.append(one_to_one_incoming_edges)
                    self.check_incoming_verts(
                        one_to_one_incoming_edges, vertex, partitioned_graph,
                        found_list)
                    one_to_one_incoming_edges.append(vertex)
                    found_list.append(vertex)
        return sorted_vertices

    @staticmethod
    def check_incoming_verts(one_to_one_verts, vertex, partitioned_graph,
                             found_list):
        """
        adds subverts which have a one to one connection
        :param one_to_one_verts: the list of sorted vertices
        :param vertex: the destination vertex
        :param partitioned_graph: the partitioned graph
        :param found_list: the list of found verts so far
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

                # if the vertex has no constraint, put in
                if len(chip_constraint) != 0:
                    one_to_one_verts.append(incoming_vert)
                    found_list.append(incoming_vert)
                else:  # if constraint exists, try to satisfy constraints.
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
