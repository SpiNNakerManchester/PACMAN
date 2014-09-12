from collections import namedtuple


class SubedgeRoutingInfo(namedtuple("SubedgeRoutingInfo", "subedge key mask")):
    """ Associates a subedge to its routing information (key and mask)
    """

    @property
    def key_mask_combo(self):
        """ The combination of the key and the mask

        :return: the key mask combo
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self.key & self.mask