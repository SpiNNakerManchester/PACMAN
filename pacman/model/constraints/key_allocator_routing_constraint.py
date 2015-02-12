from pacman.model.constraints.abstract_router_constraint \
    import AbstractRouterConstraint


class KeyAllocatorRoutingConstraint(AbstractRouterConstraint):
    """ A constraint which controls the functions used to determine key and
     mask and key with neuron ids.
    """

    def __init__(self, key_mask_function_call,
                 key_with_atom_ids_function_call):
        """

        :param key_mask_function_call:
        the call required to generate the key and mask
        :type key_mask_function_call: a python method
        :param key_with_atom_ids_function_call:
        the call required to generate keys with enuron ids
        :type key_with_atom_ids_function_call: python function
        :raise None: does not raise any known exceptions
        """
        AbstractRouterConstraint.__init__(
            self, "key allocator constraint where subedges coming from the "
                  "vertex requires a specific key and mask which are generated"
                  " from the function call {}".format(key_mask_function_call))
        self._key_function_call = key_mask_function_call
        self._atom_ids_function_call = key_with_atom_ids_function_call

    def is_router_constraint(self):
        return True

    @property
    def key_function_call(self):
        return self._key_function_call

    @property
    def key_with_atom_ids_function_call(self):
        return self._atom_ids_function_call
