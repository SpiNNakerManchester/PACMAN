from pacman.model.constraints.abstract_router_constraint \
    import AbstractRouterConstraint


class KeyAllocatorRoutingConstraint(AbstractRouterConstraint):
    """ A constraint which limits the number of atoms of a single subvertex\
        during the partitioner process
    """

    def __init__(self, function_call):
        """

        :param size: The maximum number of atoms to assign to each subvertex
        :type size: int
        :raise None: does not raise any known exceptions
        """
        AbstractRouterConstraint.__init__(
            self, "key allocator constraint where subedges coming from the "
                  "vertex requires a specific key and mask which are generated "
                  "from the function call {}".format(function_call))
        self._function_call = function_call

    @property
    def function_call(self):
        return self._function_call