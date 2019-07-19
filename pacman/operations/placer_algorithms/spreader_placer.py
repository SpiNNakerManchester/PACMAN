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

try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs.common import EdgeTrafficType
from pacman.model.placements import Placement, Placements
from pacman.operations.placer_algorithms import OneToOnePlacer
from pacman.utilities.algorithm_utilities.placer_algorithm_utilities import (
    create_vertices_groups, get_same_chip_vertex_groups)
from pacman.utilities.utility_objs import ResourceTracker
from pacman.model.constraints.placer_constraints import (
    SameChipAsConstraint, ChipAndCoreConstraint)


class SpreaderPlacer(OneToOnePlacer):
    # number of cycles over the machine graph (
    # 1. same chip,
    # 2. 1 to 1,
    # 3. sort left overs
    # 4 left overs)
    ITERATIONS = 4

    # distinct steps (
    # 1. check constraints,
    # 2. same chip sets,
    # 3. 1 to 1 sets,
    # 4. chip and core)
    STEPS = 4

    def __init__(self):
        OneToOnePlacer.__init__(self)

    def __call__(self, machine_graph, machine, n_keys_map, plan_n_timesteps):
        """ places vertices on as many chips as available with a effort to
        reduce the number of packets being received by the router in total.

        :param machine_graph: the machine graph
        :param machine: the SpiNNaker machine
        :param n_keys_map: the n keys from partition map
        :param plan_n_timesteps: number of timesteps to plan for
        :return: placements.
        """

        # create progress bar
        progress_bar = ProgressBar(
            (machine_graph.n_vertices * self.ITERATIONS) + self.STEPS,
            "Placing graph vertices via spreading over an entire machine")

        # check that the algorithm can handle the constraints
        self._check_constraints(
            machine_graph.vertices,
            additional_placement_constraints={SameChipAsConstraint})
        progress_bar.update()

        # get same chip groups
        same_chip_vertex_groups = get_same_chip_vertex_groups(machine_graph)
        progress_bar.update()
        # get chip and core placed verts
        hard_chip_constraints = self._locate_hard_placement_verts(
            machine_graph)
        progress_bar.update()
        # get one to one groups
        one_to_one_groups = create_vertices_groups(
            machine_graph.vertices,
            functools.partial(
                self._find_one_to_one_vertices, graph=machine_graph))
        progress_bar.update()

        # sort chips so that they are radial from a given point and other
        # init data structs
        chips_in_order = self._determine_chip_list(machine)
        resource_tracker = ResourceTracker(
            machine, plan_n_timesteps, chips=chips_in_order)
        placements = Placements()
        placed_vertices = set()
        cost_per_chip = defaultdict(int)
        progress_bar.update()

        # allocate hard ones
        for hard_vertex in hard_chip_constraints:
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                hard_vertex.resources_required, hard_vertex.constraints)
            placements.add_placement(Placement(hard_vertex, x, y, p))
            placed_vertices.add(hard_vertex)
            cost_per_chip[(x, y)] += self._get_cost(
                hard_vertex, machine_graph, n_keys_map)

        # place groups of verts that need the same chip on the same chip,
        self._place_same_chip_verts(
            same_chip_vertex_groups, chips_in_order, placements,
            progress_bar, resource_tracker, placed_vertices, cost_per_chip,
            machine_graph, n_keys_map)

        # place 1 group per chip if possible on same chip as any already
        # placed verts. if not then radially from it.
        self._place_one_to_one_verts(
            one_to_one_groups, chips_in_order, placements, progress_bar,
            resource_tracker, placed_vertices, cost_per_chip, machine_graph,
            n_keys_map, machine)

        # place vertices which don't have annoying placement constraints.
        # spread them over the chips so that they have minimal impact on the
        # overall incoming packet cost per router.
        self._place_left_over_verts(
            machine_graph, chips_in_order, placements, progress_bar,
            resource_tracker, placed_vertices, cost_per_chip, n_keys_map)
        progress_bar.end()

        # return the built placements
        return placements

    def _sort_left_over_verts_based_on_incoming_packets(
            self, machine_graph, placed_vertices, n_keys_map):
        """ sort left overs verts so that the ones with the most costly verts
        are at the front of the list

        :param machine_graph: machine graph
        :param placed_vertices: the verts already placed
        :param n_keys_map: map between partition to n keys.
        :return: new list of verts to process.
        :rtype: iterable of vertices.
        """

        vert_list = list()
        in_coming_size_map = defaultdict(list)
        for vertex in machine_graph.vertices:
            if vertex not in placed_vertices:
                incoming_size = self._get_cost(
                    vertex, machine_graph, n_keys_map)
                in_coming_size_map[incoming_size].append(vertex)
        sorted_keys = sorted(in_coming_size_map.keys(), reverse=True)
        for key in sorted_keys:
            vert_list.extend(in_coming_size_map[key])
        return vert_list

    @staticmethod
    def _sort_chips_based_off_incoming_cost(chips, cost_per_chip):
        """ sorts chips out so that the chip in front has least incoming cost.

        :param chips: iterable of chips to sort
        :param cost_per_chip: the map of (x,y) and cost.
        :return: iterable of chips in a sorted fashion.
        :rtype: iterable of SPiNNMachine.machine.chip
        """

        data = sorted(chips, key=lambda chip: cost_per_chip[chip[0], chip[1]])
        return data

    @staticmethod
    def _get_cost(vertex, machine_graph, n_keys_map):
        """ gets how many packets are to be processed by a given vertex.

        :param vertex: the vertex the get the cost of
        :param machine_graph: the machine graph
        :param n_keys_map: the map of outgoing partition and n keys down it.
        :return: total keys to come into this vertex.
        :rtype: int
        """

        # NOTE we going to assume as a worst case scenario that every key is
        # sent every time step. but this is obviously not valid often
        # handle incoming
        total_incoming_keys = 0
        for incoming_edge in machine_graph.get_edges_ending_at_vertex(vertex):
            if incoming_edge.traffic_type == EdgeTrafficType.MULTICAST:
                incoming_partition = \
                    machine_graph.get_outgoing_partition_for_edge(
                        incoming_edge)
                total_incoming_keys += n_keys_map.n_keys_for_partition(
                    incoming_partition)

        # handle outgoing
        out_going_partitions = \
            machine_graph.get_outgoing_edge_partitions_starting_at_vertex(
                vertex)
        for partition in out_going_partitions:
            edge = list(partition.edges)[0]
            if edge.traffic_type == EdgeTrafficType.MULTICAST:
                total_incoming_keys += \
                    n_keys_map.n_keys_for_partition(partition)
        return total_incoming_keys

    @staticmethod
    def _locate_hard_placement_verts(machine_graph):
        """ locates the verts with hard constraints

        :param machine_graph: the machine graph
        :return: list of verts to just place where they demand it
        :rtype: iterable of machine vertex.
        """
        hard_verts = list()
        for vertex in machine_graph.vertices:
            for constraint in vertex.constraints:
                if isinstance(constraint, ChipAndCoreConstraint):
                    hard_verts.append(vertex)
        return hard_verts

    def _place_same_chip_verts(
            self, same_chip_vertex_groups, chips_in_order,
            placements, progress_bar, resource_tracker, placed_vertices,
            cost_per_chip, machine_graph, n_keys_map):
        """ places verts which have to be on the same chip on minimum chip.

        :param same_chip_vertex_groups: groups of verts which want to be on
        the same chip.
        :param chips_in_order: chips in radial order from mid machine
        :param placements: placements holder
        :param progress_bar: progress bar
        :param resource_tracker: resource tracker
        :param placed_vertices: list of vertices which have already been placed
        :param cost_per_chip: map between (x,y) and the cost of packets
        :rtype: None
        """
        for vertex in same_chip_vertex_groups.keys():
            if len(same_chip_vertex_groups[vertex]) != 1:
                if vertex not in placed_vertices:
                    to_do_as_group = list()
                    for other_vert in same_chip_vertex_groups[vertex]:
                        if other_vert not in placed_vertices:
                            to_do_as_group.append(
                                (other_vert.resources_required,
                                 other_vert.constraints))

                    # allocate as a group to sorted chips so that ones with
                    # least incoming packets are considered first
                    results = \
                        resource_tracker.allocate_constrained_group_resources(
                            to_do_as_group, chips=chips_in_order)

                    # create placements and add cost to the chip
                    for (x, y, p, _, _), placed_vertex in zip(
                            results, same_chip_vertex_groups[vertex]):
                        placements.add_placement(
                            Placement(placed_vertex, x, y, p))
                        placed_vertices.add(placed_vertex)
                        cost_per_chip[(x, y)] += self._get_cost(
                            placed_vertex, machine_graph, n_keys_map)

                # resort the chips, as no idea where in the list the resource
                # tracker selected
                chips_in_order = self._sort_chips_based_off_incoming_cost(
                    chips_in_order, cost_per_chip)

        # update progress bar to cover one cycle of all the verts in the graph
        progress_bar.update(len(machine_graph.vertices))

    def _place_one_to_one_verts(
            self, one_to_one_groups, chips_in_order, placements, progress_bar,
            resource_tracker, placed_vertices, cost_per_chip, machine_graph,
            n_keys_map, machine):
        """ place 1 to 1 groups on the same chip if possible. else radially
        from it

        :param one_to_one_groups: the 1 to 1 groups
        :param chips_in_order: chips in sorted order of lowest cost
        :param placements: placements holder
        :param progress_bar: the progress bar
        :param resource_tracker: the resource tracker
        :param placed_vertices: the verts already placed
        :param cost_per_chip: map of (x,y) and the incoming packet cost
        :param machine_graph: machine graph
        :param n_keys_map: map between outgoing partition and n keys down it
        :param machine: the SpiNNMachine instance.
        :rtype: None
        """

        # go through each 1 to 1 group separately
        for group in one_to_one_groups:

            # find which cores have already been allocated or not
            unallocated = list()
            allocated = list()
            for one_to_one_vertex in group:
                if one_to_one_vertex not in placed_vertices:
                    unallocated.append(one_to_one_vertex)
                else:
                    allocated.append(one_to_one_vertex)

            # if allocated, then locate which chip to start search at
            chips = chips_in_order
            if len(allocated) != 0:
                x = None
                y = None
                all_matched = True
                # determine if the placed ones are all in the same chip. else
                #  it doesnt matter.
                for vertex in allocated:
                    placement = placements.get_placement_of_vertex(vertex)
                    if x is None and y is None:
                        x = placement.x
                        y = placement.y
                    else:
                        if x != placement.x or y != placement.y:
                            all_matched = False

                # order chips so that shared chip is first, and the rest are
                # nearby it in order. or if not all same, just least first
                if all_matched:
                    chips = self._generate_radial_chips(
                        machine, resource_tracker=None, start_chip_x=x,
                        start_chip_y=y)

            # allocate verts.
            for one_to_one_vertex in unallocated:
                (x, y, p, _, _) = \
                    resource_tracker.allocate_constrained_resources(
                        one_to_one_vertex.resources_required,
                        one_to_one_vertex.constraints, chips)

                # add to placed tracker
                placed_vertices.add(one_to_one_vertex)

                # make placement
                placements.add_placement(Placement(
                    vertex=one_to_one_vertex, x=x, y=y, p=p))

                # update cost
                cost_per_chip[(x, y)] += self._get_cost(
                    one_to_one_vertex, machine_graph, n_keys_map)

            # sort chips for the next group cycle
            chips_in_order = self._sort_chips_based_off_incoming_cost(
                chips, cost_per_chip)
        # update progress bar to cover one cycle of all the verts in the graph
        progress_bar.update(len(machine_graph.vertices))

    def _place_left_over_verts(
            self, machine_graph, chips_in_order, placements, progress_bar,
            resource_tracker, placed_vertices, cost_per_chip, n_keys_map):
        """ places left over vertices in locations with least costs.

        :param machine_graph: machine graph
        :param chips_in_order: chips in sorted order
        :param placements: placements
        :param progress_bar: progress bar
        :param resource_tracker: resource tracker
        :param placed_vertices: the verts which already been placed
        :param cost_per_chip: map between (x,y) and the total packets going
        through it currently.
        :param n_keys_map: map between outgoing partition and n keys down it.
        :rtype: None
        """

        # locate whatever verts are left
        sorted_verts = self._sort_left_over_verts_based_on_incoming_packets(
            machine_graph, placed_vertices, n_keys_map)

        for vertex in sorted_verts:
            (x, y, p, _, _) = resource_tracker.allocate_constrained_resources(
                vertex.resources_required,
                vertex.constraints, chips_in_order)
            placements.add_placement(Placement(vertex=vertex, x=x, y=y, p=p))
            cost_per_chip[(x, y)] += self._get_cost(
                vertex, machine_graph, n_keys_map)
            # sort chips for the next group cycle
            chips_in_order = self._sort_chips_based_off_incoming_cost(
                chips_in_order, cost_per_chip)

        progress_bar.update(len(machine_graph.vertices))

    def _determine_chip_list(self, machine):
        """ determines the radial list from a deduced middle of the machine

        :param machine: the machine to find a middle from
        :return: a list of chips radially from a deduced middle
        """
        # try the middle chip
        middle_chip_x = math.ceil(machine.max_chip_x / 2)
        middle_chip_y = math.ceil(machine.max_chip_y / 2)
        chip = machine.get_chip_at(middle_chip_x, middle_chip_y)

        # if middle chip don't exist. search for the closest chip.
        if chip is None:
            distance_from_middle = sys.maxsize
            closest_chip = None

            # compare each chip loc to the middle. don't need to be majorly
            # precise, all we're looking for is a chip nearby.
            for chip in machine.chips():
                x_diff = abs(middle_chip_x - chip.x)
                y_diff = abs(middle_chip_y - chip.y)
                diff_total = x_diff + y_diff
                if distance_from_middle > diff_total:
                    distance_from_middle = diff_total
                    closest_chip = chip

                # if you find a chip that's next door, then quit early
                if distance_from_middle == 1:
                    break

            # set correct middle chip
            middle_chip_x = closest_chip.x
            middle_chip_y = closest_chip.y

        # return the radial list from this middle point
        return list(self._generate_radial_chips(
            machine, resource_tracker=None, start_chip_x=middle_chip_x,
            start_chip_y=middle_chip_y))
