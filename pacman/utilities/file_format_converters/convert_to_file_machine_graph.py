import hashlib
import json
from collections import defaultdict
from pacman.model.graphs import AbstractVirtualVertex

from spinn_utilities.progress_bar import ProgressBar

DEFAULT_NUMBER_OF_CORES_USED_PER_VERTEX = 1


class ConvertToFileMachineGraph(object):
    """ Converts a memory based graph into a file based graph
    """

    __slots__ = []

    def __call__(self, machine_graph, file_path):
        """

        :param machine_graph:
        :param file_path:
        """
        progress = ProgressBar(
            machine_graph.n_vertices + 1, "Converting to json graph")

        # write basic stuff
        json_graph_directory_rep = dict()

        # write vertices data
        vertices_resources = dict()
        json_graph_directory_rep["vertices_resources"] = vertices_resources

        edges_resources = defaultdict()
        json_graph_directory_rep["edges"] = edges_resources

        vertex_by_id = dict()
        partition_by_id = dict()
        for vertex in machine_graph.vertices:
            self._convert_vertex(vertex, vertex_by_id, vertices_resources,
                                 edges_resources, machine_graph,
                                 partition_by_id)
            progress.update()

        with open(file_path, "w") as file_to_write:
            json.dump(json_graph_directory_rep, file_to_write)
        progress.update()

        progress.end()

        return file_path, vertex_by_id, partition_by_id

    def _convert_vertex(self, vertex, vertex_by_id, vertices,
                        edges, machine_graph, partition_by_id):
        vertex_id = id(vertex)
        vertex_by_id[str(vertex_id)] = vertex

        # handle external devices
        if isinstance(vertex, AbstractVirtualVertex):
            v = dict()
            vertices[vertex_id] = v
            v["cores"] = 0

        # handle tagged vertices
        elif vertex.resources_required.iptags or \
                vertex.resources_required.reverse_iptags:
            # handle the edge between the tag-able vertex and the fake vertex
            tag_id = hashlib.md5(str(vertex_id) + "_tag").hexdigest()
            hyper_edge = dict()
            edges[tag_id] = hyper_edge
            hyper_edge["source"] = str(vertex_id)
            hyper_edge['sinks'] = tag_id
            hyper_edge["weight"] = 1.0
            hyper_edge["type"] = "FAKE_TAG_EDGE"

            # add the tag-able vertex
            v = dict()
            vertices[vertex_id] = v
            v["cores"] = DEFAULT_NUMBER_OF_CORES_USED_PER_VERTEX
            v["sdram"] = int(vertex.resources_required.sdram.get_value())

            # add fake vertex
            v = dict()
            vertices[tag_id] = v
            v["cores"] = 0
            v["sdram"] = 0

        # handle standard vertices
        else:
            v = dict()
            vertices[vertex_id] = v
            v["cores"] = DEFAULT_NUMBER_OF_CORES_USED_PER_VERTEX
            v["sdram"] = int(vertex.resources_required.sdram.get_value())

        # handle the vertex edges
        for partition in machine_graph\
                .get_outgoing_edge_partitions_starting_at_vertex(vertex):
            p_id = str(id(partition))
            partition_by_id[p_id] = partition

            hyper_edge = dict()
            edges[p_id] = hyper_edge
            hyper_edge["source"] = str(id(vertex))

            sinks_string = []
            weight = 0

            for edge in partition.edges:
                sinks_string.append(str(id(edge.post_vertex)))
                weight += edge.traffic_weight
            hyper_edge['sinks'] = sinks_string
            hyper_edge["weight"] = weight
            hyper_edge["type"] = partition.traffic_type.name.lower()
