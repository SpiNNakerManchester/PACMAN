from pacman.exceptions import PacmanAlreadyExistsException
class RoutingInfo(object):
    """ An association of a set of subedges to a non-overlapping set of keys\
        and masks
    """

    def __init__(self, subedge_info_items):
        """
        
        :param subedge_info_items: The subedge information items to add
        :type subedge_info_items: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there are any\
                    two items with the same key once the mask is applied\
                    which do not have the same source subvertex
        """
        self._subedge_info_by_key = dict()
        self._subedge_info = list()
        if subedge_info_items is not None:
            self._subedge_info = list(subedge_info_items)

        for subedge_info_item in subedge_info_items:
            self.add_subedge_info(subedge_info_item)


    def add_subedge_info(self, subedge_info):
        """ Add a subedge information item
        
        :param subedge_info: The subedge information item to add
        :type subedge_info:\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanAlreadyExistsException: If there is\
                    already an item with the same key once the mask is applied\
                    which does not have the same source subvertex
        """
        if subedge_info.key in self._subedge_info_by_key.keys():
            raise PacmanAlreadyExistsException("The key already exists in the routing information",\
                                                   str(subedge_info.key))
        else:
            self._subedge_info_by_key[subedge_info.key] = subedge_info

    @property
    def all_subedge_info(self):
        """ The subedge information for all subedges

        :return: iterable of subedge information
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        return self._subedge_info

    def get_subedge_info_by_key(self, key, mask):
        """ Get the routing information associated with a particular key, once\
            the mask has been applied

        :param key: The routing key
        :type key: int
        :param mask: The routing mask
        :type mask: int
        :return: an iterable of routing information associated with the\
                    specified routing key or None if no such key exists
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_info.subedge_routing_info.SubedgeRoutingInfo`
        :raise None: does not raise any known exceptions
        """
        key_and_mask = key & mask
        list_of_accepting_key_mask_combinations = list()
        if key_and_mask in self._subedge_info_by_key.keys():
            list_of_accepting_key_mask_combinations.append(self._subedge_info_by_key[key_and_mask])
        return list_of_accepting_key_mask_combinations

