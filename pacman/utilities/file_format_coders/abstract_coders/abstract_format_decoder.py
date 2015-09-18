"""
abstract decoder for file formats to objects from other algorithms 
"""
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractFormatDecoder(object):
    """
    abstract decoder for file formats to objects from other algorithms 
    """

    def __init__(self):
        pass

    @abstractmethod
    def decode_placements(self):
        """
        :return:placements object
        """

    @abstractmethod
    def decode_partitionable_graph(self):
        """
        :return:partitionable_graph object
        """

    @abstractmethod
    def decode_partitioned_graph(self):
        """
        :return:partitioned_graph object
        """

    @abstractmethod
    def decode_machine(self):
        """
        :return:machine object
        """
        
    @abstractmethod
    def decode_partitioned_graph_constraints(self):
        """
        :return:partitioned_graph object
        """
        
    @abstractmethod
    def decode_partitionable_graph_constraints(self):
        """
        :return:partitionable_graph object
        """
        
    @abstractmethod
    def decode_routing_infos(self):
        """
        :return: routing info object
        """
        
    @abstractmethod
    def decode_routing_paths(self):
        """
        :return: routing path object
        """
        
    @abstractmethod
    def decode_routing_tables(self):
        """
        :return: routing table object
        """
        
    @abstractmethod
    def decode_tags(self):
        """
        :return: tags object
        """

    @abstractmethod
    def decode_algorithm_data_objects(self):
        """

        :return: returns the algorithm data objects which represent all the
        algorithms for inputs and outputs
        """
