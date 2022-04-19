# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pacman.model.resources import ResourceContainer, ConstantSDRAM
from spinn_utilities.ordered_set import OrderedSet
from pacman.model.constraints.placer_constraints import (
    ChipAndCoreConstraint, SameChipAsConstraint, BoardConstraint,
    RadialPlacementFromChipConstraint)
from pacman.utilities import VertexSorter, ConstraintOrder


def sort_vertices_by_known_constraints(vertices):
    """ Sort vertices to be placed by constraint so that those with\
        more restrictive constraints come first.

    :param list(ApplicationVertex) vertices:
    :rtype: list(ApplicationVertex)
    """
    sorter = VertexSorter([
        ConstraintOrder(ChipAndCoreConstraint, 1, ["p"]),
        ConstraintOrder(ChipAndCoreConstraint, 2),
        ConstraintOrder(SameChipAsConstraint, 3),
        ConstraintOrder(BoardConstraint, 4),
        ConstraintOrder(RadialPlacementFromChipConstraint, 5)])
    return sorter.sort(vertices)


def get_same_chip_vertex_groups(machine_graph):
    """ Get a dictionary of vertex to set of vertices that must be placed on\
       the same chip

    :param MachineGraph machine_graph: The graph containing the vertices
    :rtype: dict(MachineVertex, set(MachineVertex))
    """
    same_chip = dict()
    couples = list()
    for vertex in machine_graph.vertices:
        for constraint in vertex.constraints:
            if isinstance(constraint, SameChipAsConstraint):
                couples.append((vertex, constraint.vertex))
        same_chip[vertex] = {vertex}
    for partition in machine_graph.outgoing_sdram_edge_partitions:
        for edge in partition.edges:
            couples.append((edge.pre_vertex, edge.post_vertex))

    for (pre, post) in couples:
        group = same_chip[pre].union(same_chip[post])
        for v in group:
            same_chip[v] = group

    return same_chip


def add_set(all_sets, new_set):
    """
    Adds a new set into the list of sets, concatenating sets if required.

    If the new set does not overlap any existing sets it is added.

    However if the new sets overlaps one or more existing sets, a superset is
    created combining all the overlapping sets.
    Existing overlapping sets are removed and only the new superset is added.

    :param list(set) all_sets: List of non-overlapping sets
    :param set new_set:
        A new set which may or may not overlap the previous sets.
    """

    union = OrderedSet()
    removes = []
    for a_set in all_sets:
        if not new_set.isdisjoint(a_set):
            removes.append(a_set)
            union |= a_set
    union |= new_set
    if removes:
        for a_set in removes:
            all_sets.remove(a_set)
    all_sets.append(union)


def create_vertices_groups(vertices, same_group_as_function):
    """
    :param iterable(AbstractVertex) vertices:
    :param same_group_as_function:
    :type same_group_as_function:
        callable(AbstractVertex, set(AbstractVertex))
    """
    groups = list()
    done = set()
    for vertex in vertices:
        if vertex in done:
            continue
        same_chip_as_vertices = same_group_as_function(vertex)
        if same_chip_as_vertices:
            same_chip_as_vertices.add(vertex)
            # Singletons on interesting and added later if needed
            if len(same_chip_as_vertices) > 1:
                add_set(groups, same_chip_as_vertices)
            done.update(same_chip_as_vertices)
    return groups


def create_requirement_collections(vertices, machine_graph):
    """ Get a collection of requirements that includes SDRAM edge resources
    """

    # Get all but the last requirements, keeping the SDRAM edge requirements
    required_resources = list()
    to_add_partitions = set()
    last_resources = None
    last_constraints = None
    for vertex in vertices:
        if last_resources is not None:
            required_resources.append([
                last_resources, last_constraints])
        last_resources = vertex.resources_required
        last_constraints = vertex.constraints
        to_add_partitions.update(
            machine_graph.get_sdram_edge_partitions_starting_at_vertex(
                vertex))

    # Add up all the SDRAM edge requirements
    total_sdram = 0
    for partition in to_add_partitions:
        total_sdram += partition.total_sdram_requirements()

    # Add the SDRAM requirements to the final requirements
    resources = ResourceContainer(sdram=ConstantSDRAM(total_sdram))
    resources.extend(last_resources)
    required_resources.append([resources, last_constraints])

    return required_resources
