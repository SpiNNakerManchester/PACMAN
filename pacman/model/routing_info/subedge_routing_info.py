from pacman import exceptions

class SubedgeRoutingInfo(object):
    """ Associates a subedge to its routing information (key and mask)
    """

    def __init__(self, key, mask):
        self._key = key
        self._mask = mask
        if self._key & self._mask != self._key:
            raise exceptions.PacmanConfigurationException(
                "This routing info is invalid as the mask and key together "
                "alters the key_combo. This is deemed to be a error from "
                "spynnaker's point of view and therefore please rectify and"
                "try again")


    @property
    def key_mask_combo(self):
        """ The combination of the key and the mask

        :return: the key mask combo
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        return self._key & self._mask

    @property
    def key(self):
        return self._key

    @property
    def mask(self):
        return self._mask

