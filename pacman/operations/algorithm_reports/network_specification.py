import logging
import os.path
from spinn_utilities.log import FormatAdapter
from pacman.model.graphs.application import ApplicationVertex

logger = FormatAdapter(logging.getLogger(__name__))


class NetworkSpecification(object):
    """ Generate report on the user's network specification.
    """

    _FILENAME = "network_specification.rpt"

    def __call__(self, report_folder, graph):
        """
        :param report_folder: the directory to which reports are stored
        :type report_folder: str
        :param graph: the graph generated from the tools
        :type graph: pacman.model.graph.application.ApplicationGraph
        :rtype: None
        """
        filename = os.path.join(report_folder, self._FILENAME)
        try:
            with open(filename, "w") as f:
                f.write("*** Vertices:\n")
                for vertex in graph.vertices:
                    self._write_report(f, vertex, graph)
        except IOError:
            logger.exception("Generate_placement_reports: Can't open file {}"
                             " for writing.", filename)

    @staticmethod
    def _write_report(f, vertex, graph):
        if isinstance(vertex, ApplicationVertex):
            f.write("Vertex {}, size: {}, model: {}\n".format(
                vertex.label, vertex.n_atoms, vertex.__class__.__name__))
        else:
            f.write("Vertex {}, model: {}\n".format(
                vertex.label, vertex.__class__.__name__))

        f.write("    Constraints:\n")
        for constraint in vertex.constraints:
            f.write("        {}\n".format(
                str(constraint)))

        f.write("    Outgoing Edge Partitions:\n")
        for partition in graph.get_outgoing_edge_partitions_starting_at_vertex(
                vertex):
            f.write("    Partition {}:\n".format(
                partition.identifier))
            for edge in partition.edges:
                f.write("        Edge: {}, From {} to {}, model: {}\n".format(
                    edge.label, edge.pre_vertex.label,
                    edge.post_vertex.label, edge.__class__.__name__))
        f.write("\n")
