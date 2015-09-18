"""
XMLFileCoder for encoding python obejcts into XML files
"""
from pacman.utilities.file_format_coders.abstract_coders.\
    abstract_format_coder import AbstractFormatCoder
from pacman import exceptions


class XMLFileCoder(AbstractFormatCoder):
    """
    XMLFileCoder:  encoder for encoding python obejcts into XML files
    """

    def __init__(self, folder_path):
        AbstractFormatCoder.__init__(self)
        self._folder_path = folder_path

    def store_routing_tables(self, routing_tables):
        raise exceptions.PacmanException("Not implimented yet")

    def store_routing_paths(self, routing_paths):
        raise exceptions.PacmanException("Not implimented yet")

    def store_placements(self, placements):
        raise exceptions.PacmanException("Not implimented yet")

    def store_partitionable_graph(self, partitionable_graph):
        raise exceptions.PacmanException("Not implimented yet")

    def store_machine(self, machine):
        raise exceptions.PacmanException("Not implimented yet")

    def store_partitioned_graph(self, partitioned_graph):
        raise exceptions.PacmanException("Not implimented yet")

    def store_partitionable_graph_constraints(self, partitionable_graph):
        raise exceptions.PacmanException("Not implimented yet")

    def store_routing_infos(self, routing_infos):
        raise exceptions.PacmanException("Not implimented yet")

    def store_tags(self, tags):
        raise exceptions.PacmanException("Not implimented yet")

    def store_partitioned_graph_constraints(self, partitioned_graph):
        raise exceptions.PacmanException("Not implimented yet")