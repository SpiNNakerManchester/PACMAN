# pacman imports
from pacman import exceptions


class RoutingInfo(object):
    """ An association of a set of subedges to a non-overlapping set of keys\
        and masks
    """

    def __init__(self, partition_info_items=None):
        """

        :param partition_info_items: The subedge information items to add
        :type partition_info_items: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.PartitionRoutingInfo`
                    or none
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there are \
                    two subedge information objects with the same edge
        """

        # List of subedge information indexed by routing key (int)
        self._partition_infos_by_key = dict()

        # Subedge information indexed by subedge
        self._partition_info_by_partition = dict()

        if partition_info_items is not None:
            for partition_info_item in partition_info_items:
                self.add_partition_info(partition_info_item)

    def add_partition_info(self, partition_info):
        """ Add a subedge information item

        :param partition_info: The subedge information item to add
        :type partition_info:\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.PartitionRoutingInfo`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If the subedge\
                    is already in the set of subedges
        """

        if partition_info.partition in self._partition_info_by_partition:
            raise exceptions.PacmanAlreadyExistsException(
                "Partition", str(partition_info))

        self._partition_info_by_partition[partition_info.partition] =\
            partition_info

        for key_and_mask in partition_info.keys_and_masks:

            # first time the key has been added
            if key_and_mask.key not in self._partition_infos_by_key:
                self._partition_infos_by_key[key_and_mask.key] = list()
                self._partition_infos_by_key[key_and_mask.key]\
                    .append(partition_info)

            # need to check that subedge information is linked properly
            elif (self._partition_infos_by_key[key_and_mask.key] !=
                    partition_info):
                self._partition_infos_by_key[key_and_mask.key]\
                    .append(partition_info)

    @property
    def all_partition_info(self):
        """ The subedge information for all subedges

        :return: iterable of subedge information
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.PartitionRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        return self._partition_info_by_partition.itervalues()

    def get_partition_infos_by_key(self, key, mask):
        """ Get the routing information associated with a particular key, once\
            the mask has been applied

        :param key: The routing key
        :type key: int
        :param mask: The routing mask
        :type mask: int
        :return: a routing information associated with the\
                    specified routing key or None if no such key exists
        :rtype:\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.PartitionRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        key_mask_combo = key & mask
        if key_mask_combo in self._partition_infos_by_key:
            return self._partition_infos_by_key[key_mask_combo]
        return None

    def get_keys_and_masks_from_partition(self, partition):
        """ Get the key associated with a particular partition

        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.utilities.utility_objs.outgoing_edge_partition.OutgoingEdgePartition`
        :return: The routing key or None if the subedge does not exist
        :rtype: int
        :raise None: does not raise any known exceptions
        """
        if partition in self._partition_info_by_partition:
            return self._partition_info_by_partition[partition].keys_and_masks
        return None

    def get_routing_info_from_partition(self, partition):
        """
        :param partition: The partition to set the number of keys for
        :type partition:\
                    :py:class:`pacman.utilities.utility_objs.outgoing_edge_partition.OutgoingEdgePartition`
        :return: the partition_routing_info for the partition
        """
        if partition in self._partition_info_by_partition:
            return self._partition_info_by_partition[partition]
        return None

    def __iter__(self):
        """ returns a iterator for the subedge routing information

        :return: a iterator of subedge routing information
        """
        return iter(self._partition_infos_by_key)
