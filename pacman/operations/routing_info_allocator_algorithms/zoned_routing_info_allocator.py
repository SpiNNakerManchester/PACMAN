# Copyright (c) 2019 The University of Manchester
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
import math
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.routing_info import (
    RoutingInfo, PartitionRoutingInfo, BaseKeyAndMask)
from pacman.utilities.utility_calls import (
    check_algorithm_can_support_constraints)
from pacman.exceptions import PacmanRouteInfoAllocationException
from pacman.model.constraints.key_allocator_constraints import (
    AbstractKeyAllocatorConstraint, ContiguousKeyRangeContraint,
    FixedKeyAndMaskConstraint)
from pacman.model.graphs.common import EdgeTrafficType
from pacman.operations.routing_info_allocator_algorithms.\
    malloc_based_routing_allocator.malloc_based_routing_info_allocator import (
    get_key_ranges)

KEY_SIZE = 32


class ZonedRoutingInfoAllocator(object):
    """ An basic algorithm that can produce routing keys and masks for\
        edges in a graph based on the x,y,p of the placement\
        of the preceding vertex.

    .. note::
        No constraints are supported, and that the number of keys\
        required by each edge must be 2048 or less, and that all edges coming\
        out of a vertex will be given the same key/mask assignment.
    """

    __slots__ = [
        # Passed in paramateres
        "_application_graph",
        "_graph_mapper",
        "_machine_graph",
        "_placements",
        "_n_keys_map",
        # the maximum number of bytes for the key for any vertex
        "_max_app_keys_bites",
        # Map of (app_vertex, identifier) to the number of bites needed for
        #   their key.
        "_key_bites_map",
        # Map from core_sets to list of (app_vertex, identifier) pairs
        "_targets_map",
        # The Number of app vertex, identifier pairs in the graph
        "_n_vertex_identifier",
        # Routing infor being collected
        "_routing_infos",
        # dict of app_vertex to BaseKeyAndMask
        "_by_app_vertex",
        # Indexes used by fixed keys ext
        "_used_indexes"
    ]

    def __call__(self, application_graph, graph_mapper, machine_graph,
                 placements, n_keys_map):
        """
        :param machine_graph:\
            The machine graph to allocate the routing info for
        :type machine_graph:\
            :py:class:`pacman.model.graphs.machine.MachineGraph`
        :param placements: The placements of the vertices
        :type placements:\
            :py:class:`pacman.model.placements.placements.Placements`
        :param n_keys_map:\
            A map between the edges and the number of keys required by the\
            edges
        :type n_keys_map:\
            :py:class:`pacman.model.routing_info.AbstractMachinePartitionNKeysMap`
        :return: The routing information
        :rtype:\
            :py:class:`pacman.model.routing_info.PartitionRoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: \
            If something goes wrong with the allocation
        """

        self._application_graph = application_graph
        self._graph_mapper = graph_mapper
        self._machine_graph = machine_graph
        self._placements = placements
        self._n_keys_map = n_keys_map

        # check that this algorithm supports the constraints put onto the
        # partitions
        check_algorithm_can_support_constraints(
            constrained_vertices=machine_graph.outgoing_edge_partitions,
            supported_constraints=[ContiguousKeyRangeContraint,
                                   FixedKeyAndMaskConstraint],
            #supported_constraints=[ContiguousKeyRangeContraint],
            abstract_constraint_type=AbstractKeyAllocatorConstraint)

        self._routing_infos = RoutingInfo()
        self._by_app_vertex = dict()
        self._used_indexes = set()

        self._group_by_targets()
        self._calculate_zones()
        self._allocate_fixed_keys()
        self._check_sizes()
        self._allocate_keys()

        return self._routing_infos, self._by_app_vertex

    def _group_by_targets(self):
        """
        Groups the vertex, identifier pairs by target cores

        Finds the partition.identifier(s) for each app_vertex

        Then for each pair of app_vertex and identifier it finds all the cores
            the edge's post_vertexes are on.

        The vertex, identifier pairs are groups if they have the same target
            cores. There groups are saved in self._targets_map

        """
        self._targets_map = defaultdict(list)
        self._n_vertex_identifier = self._application_graph.n_vertices
        progress = ProgressBar(
            self._application_graph.n_vertices, "groupsing by traget")
        for app_vertex in progress.over(self._application_graph.vertices):
            self._group_by_targets_simple(app_vertex)

    def _group_by_targets_simple(self, app_vertex):
        """
        Groups a vertex and its partition identifer

        Adds the pair to the self._targets_map

        If more than one identifier found this method delegates to
        _group_by_targets_with_partition

        :param app_vertex:
        :return:
        """
        cores_set = set()
        machine_vertices = self._graph_mapper.get_machine_vertices(app_vertex)
        identifiers = set()
        for vertex in machine_vertices:
            partitions = self._machine_graph.\
                get_outgoing_edge_partitions_starting_at_vertex(vertex)
            for partition in partitions:
                if partition.traffic_type == EdgeTrafficType.MULTICAST:
                    print(partition)
                    identifiers.add(partition.identifier)
                    for edge in partition.edges:
                        placement = \
                            self._placements.get_placement_of_vertex(
                                edge.post_vertex)
                        core = (placement.x, placement.y, placement.p)
                        cores_set.add(core)
        if len(identifiers) == 1:
            self._update_tragets_map(app_vertex, identifiers.pop(), cores_set)
        else:
            self._group_by_targets_with_partition(app_vertex, identifiers)

    def _update_tragets_map(self, app_vertex, identifier, cores_set):
        """
        Add the app_vertex, identifer pair to the self._targets_map

        Currently just based on a str of the cores_set
        :param app_vertex:
        :param identifier:
        :param cores_set:
        :return:
        """
        as_list = list(cores_set)
        as_list.sort()
        core_str = str(as_list)
        self._targets_map[core_str].append((app_vertex, identifier))

    def _group_by_targets_with_partition(self, app_vertex, identifiers):
        """
        Groups a vertex and each of its partition identifers

        These pairs are added to the self._targets_map
        """

        self._n_vertex_identifier += (len(identifiers) - 1)
        for identifier in identifiers:
            cores_set = set()
            machine_vertices = self._graph_mapper.get_machine_vertices(
                app_vertex)
            for vertex in machine_vertices:
                partitions = self._machine_graph.\
                    get_outgoing_edge_partitions_starting_at_vertex(vertex)
                for partition in partitions:
                    if partition.identifier == identifier:
                        for edge in partition.edges:
                            placement = \
                                self._placements.get_placement_of_vertex(
                                    edge.post_vertex)
                            core = (placement.x, placement.y, placement.p)
                            cores_set.add(core)
            self._update_tragets_map(app_vertex, identifier, cores_set)

    def _iterate_vertex_identifier(self, progress_message):
        """
        Iterates over the (app_vertex, identifier) pairs with a progress bar.

        The order of the pairs will be based on an guess of which pairs
        may benefit from having keys near each other.

        :param progress_message: Message for the progress bar
        :return: (app_vertex, identifier)
        """
        progress = ProgressBar(self._n_vertex_identifier, progress_message)
        for app_list in self._targets_map.values():
            for (app_vertex, identifier) in progress.over(
                    app_list, finish_at_end=False):
                yield (app_vertex, identifier)
        progress.end()

    def _check_constraint(self, partition, constraint_class):
        """
        Checks the contraints on a partition and attempts to find one of the
        class being looked for

        :return: constraints if found or None if not found
        """
        if constraint_class:
            for constraint in partition.constraints:
                if isinstance(constraint, constraint_class):
                        return constraint
            return None
        return None

    def _except_constraint(
            self, app_vertex, identifier, constraint_class=None):
        """
        Iterates over the partitions of this app_vertex that DO NOT have a
            constraint of this type

        yields partition, machine_vertex_index
        """
        machine_vertices = self._graph_mapper.get_machine_vertices(app_vertex)
        for vertex in machine_vertices:
            index = self._graph_mapper.get_machine_vertex_index(vertex)
            partitions = self._machine_graph. \
                get_outgoing_edge_partitions_starting_at_vertex(vertex)
            for partition in partitions:
                if partition.identifier == identifier:
                    if self._check_constraint(
                            partition, constraint_class) is None:
                        yield partition, index

    def _only_constraint(
            self, app_vertex, identifier, constraint_class=None):
        """
        Iterates over the partitions of this app_vertex that DO have a
            constraint of this type

        Note: The assumption is that NO partition will have more than one
            constraint of the given type

        yields partition, constraint
        """
        machine_vertices = self._graph_mapper.get_machine_vertices(app_vertex)
        for vertex in machine_vertices:
            partitions = self._machine_graph. \
                get_outgoing_edge_partitions_starting_at_vertex(vertex)
            for partition in partitions:
                if partition.identifier == identifier:
                    constraint = self._check_constraint(
                        partition, constraint_class)
                    if constraint is not None:
                        yield partition, constraint

    def _calculate_zones(self):
        """
        Calculates the bites needed for the keys of each
            app vertex, identifier pair

        results are stored in
            self._max_app_keys_bites: Which is the largest found.
            self._key_bites_map: Which is a map of app_vertex, identifier
         """
        self._max_app_keys_bites = 0
        self._key_bites_map = dict()
        for (app_vertex, identifier) in self._iterate_vertex_identifier(
                "Calculating zones"):
            machine_vertices = self._graph_mapper.get_machine_vertices(
                app_vertex)
            max_keys = 0
            for partition, index in self._except_constraint(
                    app_vertex, identifier, FixedKeyAndMaskConstraint):
                n_keys = self._n_keys_map.n_keys_for_partition(partition)
                max_keys = max(max_keys, n_keys)
            if max_keys > 0:
                key_bites = self._bites_needed(max_keys)
                machine_bites = self._bites_needed(len(machine_vertices))
                self._max_app_keys_bites = max(
                    self._max_app_keys_bites, machine_bites + key_bites)
                self._key_bites_map[(app_vertex, identifier)] = key_bites

    def _bites_needed(self, size):
        """
        Computes the bytes need to distiniquish size values

        For example for 7 values you need 3 bites

        Note: That the values are assumed to start at zero so for size which
        is a power of 2 the bites do not need to include that power position
        size of 8 needs 3 bits which are the values
            (000, 001, 010, 011, 100, 101, 110 and 111)
        size 1 needs ZERO bytes as there is no need to distiniquish

        :param size: Number of values to distinguish
        :return: minimum bites needed
        """
        return math.ceil(math.log(size, 2))

    def _mark_source_indexes_used(self, constraint):
        """
        Mark the source_index used by fixed keys and masks as taken

        If even one of the key range covered is used mark the whole as used

        results saved in self._used_indexes
        """
        for key_mask in constraint.keys_and_masks:
            for key, n_keys in get_key_ranges(key_mask.key, key_mask.mask):
                low_index = key >> self._max_app_keys_bites
                high_index = self._max_app_keys_bites
                for index in range(low_index, high_index+1):
                    self._used_indexes.add(index)

    def _allocate_fixed_keys(self):
        """
        Allocate any partitions with fixed keys and masks and
        mark the source indexs they cover as used
        """
        for (app_vertex, identifier) in self._iterate_vertex_identifier(
                "Allocating routing keys"):
            for partition, constraint in self._only_constraint(
                    app_vertex, identifier, FixedKeyAndMaskConstraint):
                self._mark_source_indexes_used(constraint)
                info = PartitionRoutingInfo(
                    constraint.keys_and_masks, partition)
                self._routing_infos.add_partition_info(info)
                # TODO work out how this is used to know what to do with
                # multiple identifiers
                # self._by_app_vertex[app_vertex] = constraint.keys_and_masks

    def _check_sizes(self):
        """
        Check that there is enough room to allocate zone based.

        Taking into consideration indexs taken by fixed keys

        """
        indexes_needed = self._n_vertex_identifier + len(self._used_indexes)
        source_bites = self._bites_needed(indexes_needed)
        if source_bites + self._max_app_keys_bites > KEY_SIZE:
            raise PacmanRouteInfoAllocationException(
                "Unable to use ZonedRoutingInfoAllocator please select a "
                "different allocator as it needs {} + {} bites"
                "".format(source_bites, self._max_app_keys_bites))

    def _allocate_keys(self):
        """
        Allocates the keys for each app_vertex, identifer pair

        The keys are allocated so that all app_vertexes start at a multiple
        of 2^^self._max_app_keys_bites

        Within an app_vertex, identifer pair keys are allocated as continious
            as possible while still making sure that
            1. All machine vertexs have none intersecting key, map pairs
            2. The number of bites used for the key is the same

        Keys will be continious if and only if for app vertex, identifer pair
        the n_keys_for_partition for all partitions
        (except possibly the last one)
        is the same number AND a power of 2

        WARNING: The map of app_vertex to BaseKeyAndMask is currently BROKEN
            for app_vertexes with multiple partitions.

        :return: RoutingInfo, dict of app_vertex to BaseKeyAndMask
        """
        app_mask = 2 ** 32 - 2 ** self._max_app_keys_bites

        source_index = 0
        for (app_vertex, identifier) in self._iterate_vertex_identifier(
                "Allocating routing keys"):
            for partition, index in self._except_constraint(
                    app_vertex, identifier, FixedKeyAndMaskConstraint):
                key_bites = self._key_bites_map[(app_vertex, identifier)]
                mask = 2 ** 32 - 2 ** key_bites
                key = source_index << self._max_app_keys_bites | \
                    index << key_bites
                keys_and_masks = list([BaseKeyAndMask(
                    base_key=key, mask=mask)])
                info = PartitionRoutingInfo(keys_and_masks, partition)
                self._routing_infos.add_partition_info(info)
            app_key = source_index << self._max_app_keys_bites
            self._by_app_vertex[app_vertex] = BaseKeyAndMask(
                base_key=app_key, mask=app_mask)
            source_index += 1
            # Skip anying source_indexes used by fix keys
            while source_index in self._used_indexes:
                source_index += 1
