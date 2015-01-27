import math
from pacman.model.constraints.abstract_router_constraint import \
    AbstractRouterConstraint
from pacman.model.constraints.key_allocator_routing_constraint import \
    KeyAllocatorRoutingConstraint
from pacman.model.routing_info.routing_info import RoutingInfo
from pacman.utilities import constants
from pacman import exceptions
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.operations.routing_info_allocator_algorithms.\
    abstract_routing_info_allocator_algorithm import \
    AbstractRoutingInfoAllocatorAlgorithm
from pacman.operations.routing_info_allocator_algorithms.\
    malloc_based_routing_allocator.free_space import FreeSpace
from pacman.utilities import utility_calls
from pacman.utilities.progress_bar import ProgressBar


class MallocBasedRoutingInfoAllocator(AbstractRoutingInfoAllocatorAlgorithm):

    def __init__(self, graph_mapper):
        AbstractRoutingInfoAllocatorAlgorithm.__init__(self)
        self._supported_constraints.append(KeyAllocatorRoutingConstraint)
        self._free_space_tracker = list()
        self._vertex_to_routing_info_register = dict()
        self._registered_key_combos = dict()
        self._free_space_tracker.append(FreeSpace(0, math.pow(2, 32)))
        self._graph_mapper = graph_mapper

    def _register_a_key(self, key, mask, partitioned_vertex, subedge):
        """ function to handle edges and vertices which have specific
        requreiments on their key and mask.

        :param key: the key needed to be used
        :param mask: the mask to use with the key
         (indirectly used for a max atoms)
        :param partitioned_vertex: the partitioned vertex this key is
        associated with
        :param subedge: the subedge assoicated with this key
        :return: the routing info object that encompasses the decisions
        :raises: PacmanAlreadyExistsException if the key has already been
        allocated
        PacmanConfigurationException if there is not enough space to allocate
        the key given its contraints
        """
        key_combo = key & mask
        #check if key has been used already
        if key_combo in self._registered_key_combos.keys():
            raise exceptions.PacmanAlreadyExistsException(
                "this key: {} with mask {} has already been registered to "
                "vertex {}, not vertex {}. Please use another key and mask and "
                "try again"
                .format(key, mask, self._registered_key_combos[key_combo],
                        partitioned_vertex), key_combo)
        else:
            #key has not been registered, therefore start registration process
            #locate space which this key is needing
            mask_size = self._deduce_size_from_mask(mask)
            self._handle_space_for_key(key, mask_size)
            #check if subvert hasnt registered a key before, make a new list
            routing_info = self._update_data_objects(
                key_combo, key, mask, partitioned_vertex, subedge)
            return routing_info

    def _update_data_objects(self, key_combo, key, mask, partitioned_vertex,
                             subedge):
        """ takes the generated key, mask, and assoicated objects and
        updates internal represnetations

        :param key_combo: the key anded with the mask
        :param partitioned_vertex: the partitioned vertex which requested a
        key allocation in the first place
        :param key: the key allocated/requested to it by the system
        :param mask: the mask allocated/requested to it by the system
        :param subedge: the subegde going out of the partitioned vertex
        in the first place
        :return: a routing info object which reflects the decisions
        :raises: None
        """
        #check if subvert hasnt registered a key before, make a new list
        self._registered_key_combos[key_combo] = partitioned_vertex
        vertex_keys = self._vertex_to_routing_info_register.keys()
        if partitioned_vertex not in vertex_keys:
            self._vertex_to_routing_info_register[partitioned_vertex] \
                = dict()
        routing_info = SubedgeRoutingInfo(int(key), int(mask), subedge)
        self._vertex_to_routing_info_register[partitioned_vertex][subedge]\
            = routing_info
        return routing_info

    def _handle_space_for_key(self, key, mask_size):
        """handles the allocating of space for a speific key and range
        of neruons. Risk is that this key space has already been allocated

        :param key: the key to be used
        :param mask_size: the max size needed with the mask to cover neurons
        :return: None
        :raises: PacmanConfigurationException when the key space has already
        been allocated
        """
        reached_slot = False
        found = False
        position = 0
        while not reached_slot and position < len(self._free_space_tracker):
            free_space_slot = self._free_space_tracker[position]
            #check that slot could contain the start key
            if free_space_slot.start_address <= key:
                max_key = key + mask_size
                max_free_space_slot_key = \
                    free_space_slot.start_address + free_space_slot.size
                #check that the top part of the key resides in the slot
                if max_free_space_slot_key > max_key:
                    reached_slot = True
                    self._reallocate_space(free_space_slot, key, max_key,
                                           position)
            else:
                reached_slot = True
            position += 1
        if not found:
            raise exceptions.PacmanConfigurationException(
                "Could not allocate the key, as there is no free space"
                " avilable where this key can reside")

    def _reallocate_space(self, free_space_slot, key, max_key, position):
        """ method that relalocates space as required

        :param free_space_slot: the slot thats being adjusted
        :param key: the start address of the key which is to be used to split
        the search space
        :param max_key: the max key that governs how much of the space to remove
        :param position: the position of the space slot in the ordered list
        :return: None
        :raises: None
        """
        max_free_space_slot_key = \
            free_space_slot.start_address + free_space_slot.size
        self._free_space_tracker.remove(free_space_slot)
        #if the eky is the start address, then theres no left slot
        if free_space_slot.start_address != key:
            left_slot = \
                FreeSpace(free_space_slot.start_address,
                          key - free_space_slot.start_address)
            self._free_space_tracker.insert(position, left_slot)
        right_slot = FreeSpace(max_key,
                               max_free_space_slot_key - max_key)
        self._free_space_tracker.insert(position + 1, right_slot)

    def _handle_space_for_neurons(self, n_neurons):
        """ sorts out the space objects based on the n_neurons asked to be
        covered by some key.

        :param n_neurons: the number of neurons that need to be covered by a key
        :return:
        """
        mask, mask_size = self._calculate_mask(n_neurons)
        found = False
        key = None
        position = 0
        while not found and position < len(self._free_space_tracker):
            free_space_slot = self._free_space_tracker[position]
            if free_space_slot.size > mask_size:
                key = free_space_slot.start_address
                max_key = key + mask_size
                self._reallocate_space(free_space_slot, key, max_key, position)
                found = True
        if not found:
            raise exceptions.PacmanConfigurationException(
                "there is no space avilable that can contain this key, please"
                "readjust your key allocation and try again")
        return key, mask

    @staticmethod
    def _deduce_size_from_mask(mask):
        """ from the mask, returns the max_number of neurons it covers

        :param mask: the mask to deduce the number of neurons from
        :return: the max_neurons deduced from the mask
        """
        position = 0
        final_mask = 0
        while position < constants.BITS_IN_KEY:
            temp_mask = mask >> position
            temp_mask &= 0xF
            if temp_mask != 0xF:
                final_mask += (temp_mask << position)
            position += 4
        return final_mask

    @staticmethod
    def _calculate_mask(n_neurons):
        """calculates a mask for a number of neurons (placed at bottom of key)
        and informs next emthod of the max neurons it covers as this has to be
         a power of two from the actual number of n_neurons

        :param n_neurons: the number of neurons the mask has to cover
        :return: the mask generated from the n_neurons and the total number of
        atoms the mask can cover
        """
        temp_value = math.floor(math.log(n_neurons, 2))
        max_value = int(math.pow(2, 32))
        max_atoms_covered = \
            math.pow(2, int(math.log(int(math.pow(2, temp_value + 1)), 2)) + 1)
        mask = max_value - int(math.pow(2, temp_value + 1))
        return mask, max_atoms_covered

    def _request_a_key(self, n_neurons, partitioned_vertex, subedge):
        """ takes a number of neurons and detemrines a key and mask that

        :param n_neurons:
        :param partitioned_vertex:
        :param subedge:
        :return: a routinginfo object that encompasses the
        """
        key, mask = self._handle_space_for_neurons(n_neurons)
        key_combo = int(key) & mask
        routing_info = self._update_data_objects(
            key_combo, key, mask, partitioned_vertex, subedge)
        return routing_info

    def _generate_keys_with_atom_id(self, vertex_slice, vertex, placement,
                                    subedge):
        """ generates a dict of atoms to key mapping
        (to be used within the database)

        :param vertex_slice: the slice used by the partitioned vertex
        :param vertex: the partitioned vertex being considered
        :param placement: the position on the machine in x,y,p
        :param subedge: the subedge being considered
        :return: a dictonary of neuron_id to key mappings.
        :raises: None
        """
        routing_info = self._vertex_to_routing_info_register[vertex][subedge]
        key = routing_info.key
        keys = dict()
        for atom in range(vertex_slice.lo_atom, vertex_slice.hi_atom):
            keys[atom] = key + atom
        return keys

    def allocate_routing_info(self, subgraph, placements):
        """ Allocates routing information to the subedges in a partitioned_graph

        :param subgraph: The partitioned_graph to allocate the routing info for
        :type subgraph: :py:class:`pacman.model.subgraph.subgraph.Subgraph`
        :param placements: The placements of the subvertices
        :type placements: :py:class:`pacman.model.placements.placements.Placements`
        :return: The routing information
        :rtype: :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :raise pacman.exceptions.PacmanRouteInfoAllocationException: If\
                   something goes wrong with the allocation
        """
        #check that this algorithm supports the constraints put onto the
        #subvertexes

        utility_calls.check_algorithm_can_support_constraints(
            constrained_vertices=subgraph.subvertices,
            supported_constraints=self._supported_constraints,
            abstract_constraint_type=AbstractRouterConstraint)

        #take each subedge and create keys from its placement
        progress_bar = \
            ProgressBar(len(subgraph.subvertices),
                        "on allocating the key's and masks for each subedge")
        routing_infos = RoutingInfo()
        for partitioned_vertex in subgraph.subvertices:
            router_constraints_of_vertex =\
                utility_calls.locate_constraints_of_type(
                    partitioned_vertex.constraints,
                    KeyAllocatorRoutingConstraint)
            if len(router_constraints_of_vertex) == 1:
                out_going_subedges = subgraph.\
                    outgoing_subedges_from_subvertex(partitioned_vertex)
                for out_going_subedge in out_going_subedges:
                    key, mask = \
                        router_constraints_of_vertex[0].key_function_call()
                    routing_info = self._register_a_key(
                        key, mask, partitioned_vertex, out_going_subedge)
                    routing_infos.add_subedge_info(routing_info)
        for partitioned_vertex in subgraph.subvertices:
            router_constraints_of_vertex =\
                utility_calls.locate_constraints_of_type(
                    partitioned_vertex.constraints,
                    KeyAllocatorRoutingConstraint)
            if len(router_constraints_of_vertex) == 0:
                out_going_subedges = subgraph.\
                    outgoing_subedges_from_subvertex(partitioned_vertex)
                for out_going_subedge in out_going_subedges:
                    vertex_slice = \
                        self._graph_mapper.get_subvertex_slice(
                            partitioned_vertex)
                    routing_info = \
                        self._request_a_key(vertex_slice.n_atoms,
                                            partitioned_vertex,
                                            out_going_subedge)
                    routing_infos.add_subedge_info(routing_info)
        return routing_infos