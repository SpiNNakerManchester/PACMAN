
# pacman imports
from pacman import exceptions
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
import traceback


class OneToOnePlacer(RadialPlacer):
    """ Placer that puts vertices which are directly connected to only its\
        destination on the same chip
    """

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

        return placements

    def _do_allocation(self, ordered_subverts, placements, machine):

        # Iterate over subvertices and generate placements
        progress_bar = ProgressBar(
            len(ordered_subverts), "Placing graph vertices")
        resource_tracker = ResourceTracker(
            machine, self._generate_radial_chips(machine))

        # iterate over subverts
        for subvertex_list in ordered_subverts:

            # ensure largest cores per chip is a devisional by 2 number
            # (for one to one placement)
            max_cores_on_chip = \
                resource_tracker.most_avilable_cores_on_a_chip()
            if max_cores_on_chip % 2 != 0:
                max_cores_on_chip -= 1

            # if too many one to ones to fit on a chip, allocate individually
            if len(subvertex_list) > max_cores_on_chip:
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
                except exceptions.PacmanValueError or \
                        exceptions.PacmanException or \
                        exceptions.PacmanInvalidParameterException:
                    traceback.print_exc()

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
            if vertex not in found_list:
                connected_vertices = self._find_one_to_one_vertices(
                    vertex, partitioned_graph)
                new_list = [
                    v for v in connected_vertices if v not in found_list]
                sorted_vertices.append(new_list)
                found_list.update(set(new_list))

        # locate vertices which have no output or input, and add them for
        # placement
        for vertex in ordered_subverts:
            if vertex not in found_list:
                sorted_vertices.append([vertex])
        return sorted_vertices

    @staticmethod
    def _find_one_to_one_vertices(vertex, partitioned_graph):
        """
        find vertices which have one to one connections with the given vertex,
        and where their constraints dont force them onto different chips.
        :param vertex:  the vertex to use as a basis for one to one connections
        :param partitioned_graph: the graph to look for other one to one verts
        :return:  set of one to one vertices
        """
        x, y, _ = utility_calls.get_chip_and_core(vertex.constraints)
        found_vertices = [vertex]
        vertices_seen = {vertex}

        #look for one to ones leaving this vertex
        outgoing = partitioned_graph.outgoing_subedges_from_subvertex(vertex)
        vertices_to_try = [edge.post_subvertex for edge in outgoing]
        while len(vertices_to_try) != 0:
            next_vertex = vertices_to_try.pop()
            if next_vertex not in vertices_seen:
                vertices_seen.add(next_vertex)
                post_x, post_y, _ = utility_calls.get_chip_and_core(
                    next_vertex.constraints)
                conflict = False
                if x is not None and post_x is not None and x != post_x:
                    conflict = True
                if y is not None and post_y is not None and y != post_y:
                    conflict = True
                edges = partitioned_graph.incoming_subedges_from_subvertex(
                    next_vertex)
                if len(edges) == 1 and not conflict:
                    found_vertices.append(next_vertex)
                    if post_x is not None:
                        x = post_x
                    if post_y is not None:
                        y = post_y
                    outgoing = \
                        partitioned_graph.outgoing_subedges_from_subvertex(
                            next_vertex)
                    vertices_to_try.extend([
                        edge.post_subvertex for edge in outgoing
                        if edge.post_subvertex not in vertices_seen])

        #look for one to ones entering this vertex
        incoming = partitioned_graph.incoming_subedges_from_subvertex(
            vertex)
        vertices_to_try = [
            edge.pre_subvertex for edge in incoming
            if edge.pre_subvertex not in vertices_seen]
        while len(vertices_to_try) != 0:
            next_vertex = vertices_to_try.pop()
            if next_vertex not in vertices_seen:
                vertices_seen.add(next_vertex)
                pre_x, pre_y, _ = utility_calls.get_chip_and_core(
                    next_vertex.constraints)
                conflict = False
                if x is not None and pre_x is not None and x != pre_x:
                    conflict = True
                if y is not None and pre_y is not None and y != pre_y:
                    conflict = True
                edges = partitioned_graph.outgoing_subedges_from_subvertex(
                    next_vertex)
                if len(edges) == 1 and not conflict:
                    found_vertices.append(next_vertex)
                    if pre_x is not None:
                        x = pre_x
                    if pre_y is not None:
                        y = pre_y
                    incoming = \
                        partitioned_graph.incoming_subedges_from_subvertex(
                            next_vertex)
                    vertices_to_try.extend([
                        edge.pre_subvertex for edge in incoming
                        if edge.pre_subvertex not in vertices_seen])

        return found_vertices
