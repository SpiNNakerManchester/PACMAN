import numpy


class PartitionRoutingInfo(object):
    """ Associates a partition to its routing information
        (keys and masks)
    """

    def __init__(self, keys_and_masks, partition):
        """
        :param keys_and_masks: The keys allocated to the machine partition
        :type keys_and_masks: iterable of\
                    :py:class:`pacman.model.routing_info.key_and_mask.BaseKeyAndMask`
        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.model.graph.simple_outgoing_edge_partition.OutgoingEdgePartition`
        """
        self._keys_and_masks = keys_and_masks
        self._partition = partition

    def get_keys(self, n_keys=None):
        """ Get the ordered list of individual keys allocated to the subedge

        :param n_keys: Optional limit on the number of keys to return
        :type n_keys: int
        :return: An array of keys
        :rtype: array-like of int
        """

        if n_keys is None:
            n_keys = 0
            for key_and_mask in self._keys_and_masks:
                n_keys += key_and_mask.n_keys

        key_array = numpy.zeros(n_keys, dtype=">u4")
        offset = 0
        for key_and_mask in self._keys_and_masks:
            _, offset = key_and_mask.get_keys(
                key_array=key_array, offset=offset, n_keys=(n_keys - offset))
        return key_array

    @property
    def keys_and_masks(self):
        return self._keys_and_masks

    @property
    def first_key_and_mask(self):
        """ The first key and mask (or only one if there is only one)
        """
        return self._keys_and_masks[0]

    @property
    def first_key(self):
        """ The first key (or only one if there is only one)
        """
        return self._keys_and_masks[0].key

    @property
    def first_mask(self):
        """ The first mask (or only one if there is only one)
        """
        return self._keys_and_masks[0].mask

    @property
    def partition(self):
        return self._partition

    def __repr__(self):
        return "partition:{}, keys_and_masks:{}".format(
            self._partition, self._keys_and_masks)
