from pacman.model.constraints.abstract_router_constraint \
    import AbstractRouterConstraint


class KeyAllocatorFixedMaskConstraint(AbstractRouterConstraint):
    """ A constraint which controls the functions used to determine the
     mask during key allocation
    """

    def __init__(self, fixed_mask_value):
        """

        :param fixed_mask_value: the fixed mask to be used during key \
                    allocation
        :type fixed_mask_value: int
        :raise None: does not raise any known exceptions
        """
        AbstractRouterConstraint.__init__(
            self, "key allocator constraint where subedges coming from the "
                  "vertex requires a specific mask")
        self._fixed_mask = fixed_mask_value

    def is_router_constraint(self):
        return True

    @property
    def fixed_mask_value(self):
        return self._fixed_mask
