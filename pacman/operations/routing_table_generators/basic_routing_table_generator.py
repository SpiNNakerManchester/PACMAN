"""
basic routing table allocator
"""

MAX_KEYS_SUPPORTED = 2048
MASK = 0xFFFFF800


class BasicRoutingTableGenerator(object):
    """ An basic algorithm that can produce routing tables

    """

    def __call__(
            self, routing_info, routing_table_by_partitions, partitioned_graph):
        """

        :param routing_info:
        :param routing_table_by_partitions:
        :param partitioned_graph:
        :return:
        """



