import logging
import os
from pacman.model.graphs.application.application_vertex \
    import ApplicationVertex

logger = logging.getLogger(__name__)


class NetworkSpecification(object):
    """ Generate report on the user's network specification.
    """

    def __call__(self, report_folder, graph):
        """
        :param report_folder: the directory to which reports are stored
        :type report_folder: str
        :param graph: the graph generated from the tools
        :type graph: pacman.model.graph.application.application_graph.Graph
        :param hostname: the machine name
        :type hostname: str
        :rtype: None
        """
        filename = report_folder + os.sep + "network_specification.rpt"
        f_network_specification = None
        try:
            f_network_specification = open(filename, "w")
        except IOError:
            logger.error("Generate_placement_reports: Can't open file {}"
                         " for writing.".format(filename))

        # Print information on vertices:
        f_network_specification.write("*** Vertices:\n")
        for vertex in graph.vertices:
            if isinstance(vertex, ApplicationVertex):
                f_network_specification.write(
                    "Vertex {}, size: {}, model: {}\n".format(
                        vertex.label, vertex.n_atoms,
                        vertex.__class__.__name__))
            else:
                f_network_specification.write(
                    "Vertex {}, model: {}\n".format(
                        vertex.label, vertex.__class__.__name__))

            f_network_specification.write("    Constraints:\n")
            for constraint in vertex.constraints:
                f_network_specification.write("        {}\n".format(
                    str(constraint)))

            f_network_specification.write(
                "    Outgoing Edge Partitions:\n")
            for partition in \
                    graph.get_outgoing_edge_partitions_starting_at_vertex(
                        vertex):

                f_network_specification.write("    Partition {}:\n".format(
                    partition.identifier))
                for edge in partition.edges:
                    f_network_specification.write(
                        "        Edge: {}, From {} to {}, model: {}\n".format(
                            edge.label, edge.pre_vertex.label,
                            edge.post_vertex.label, edge.__class__.__name__))
            f_network_specification.write("\n")

        # Close file:
        f_network_specification.close()
