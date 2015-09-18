"""
abstract coder for obejcts to file formats for other algorithms to decode
"""
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractFormatCoder(object):
    """
    abstract coder for obejcts to file formats for other algorithms to decode
    """

    def __init__(self):
        pass

    @abstractmethod
    def store_placements(self, placements):
        """

        :param placements:
        :return:
        """

    @abstractmethod
    def store_partitionable_graph(self, partitionable_graph):
        """

        :param partitionable_graph:
        :return:
        """

    @abstractmethod
    def store_partitioned_graph(self, partitioned_graph):
        """

        :param partitioned_graph:
        :return:
        """

    @abstractmethod
    def store_machine(self, machine):
        """

        :param machine:
        :return:
        """

    @abstractmethod
    def store_partitioned_graph_constraints(self, partitioned_graph):
        """

        :param partitioned_graph:
        :return:
        """

    @abstractmethod
    def store_partitionable_graph_constraints(self, partitionable_graph):
        """

        :param partitionable_graph:
        :return:
        """

    @abstractmethod
    def store_routing_infos(self, routing_infos):
        """

        :param routing_infos:
        :return:
        """

    @abstractmethod
    def store_routing_paths(self, routing_paths):
        """

        :param routing_paths:
        :return:
        """

    @abstractmethod
    def store_routing_tables(self, routing_tables):
        """

        :param routing_tables:
        :return:
        """

    @abstractmethod
    def store_tags(self, tags):
        """

        :param tags:
        :return:
        """