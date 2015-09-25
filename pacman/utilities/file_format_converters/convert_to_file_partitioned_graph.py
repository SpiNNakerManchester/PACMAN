"""
 converts a memory based partitioned graph into a file based partitioned graph
"""

from pacman.model.abstract_classes.abstract_virtual_vertex import \
    AbstractVirtualVertex
from pacman.model.constraints.abstract_constraints.\
    abstract_tag_allocator_constraint import \
    AbstractTagAllocatorConstraint
from pacman.utilities import utility_calls

from pacman.utilities import file_format_schemas

from collections import defaultdict

import os
import json
import validictory
import hashlib

DEFAULT_NOUMBER_OF_CORES_USED_PER_PARTITIONED_VERTEX = 1


class ConvertToFilePartitionedGraph(object):
    """
    converts a memory based partitioned graph into a file based partitioned graph
    """

    def __call__(self, partitioned_graph, folder_path):
        """

        :param partitioned_graph:
        :param folder_path:
        :return:
        """

        # write basic stuff
        json_graph_dictory_rep = dict()

        # write vertices data
        vertices_resources = dict()
        json_graph_dictory_rep["vertices_resources"] = vertices_resources

        edges_resources = defaultdict()
        json_graph_dictory_rep["edges"] = edges_resources

        for vertex in partitioned_graph.subvertices:

            # handle external devices
            if isinstance(vertex, AbstractVirtualVertex):
                vertex_resources = dict()
                vertices_resources[vertex.label] = vertex_resources
                vertex_resources["cores"] = 0

            # handle taged vertices
            elif len(utility_calls.locate_constraints_of_type(
                    vertex.constraints, AbstractTagAllocatorConstraint)) != 0:

                # handel the eddge between the tagable vertex and the fake
                # vertex
                hyper_edge_dict = dict()
                edges_resources[hashlib.md5(vertex.label).hexdigest()] = \
                    hyper_edge_dict
                hyper_edge_dict["source"] = vertex.label
                hyper_edge_dict['sinks'] = \
                    [hashlib.md5(vertex.label).hexdigest()]
                hyper_edge_dict["weight"] = 1.0
                hyper_edge_dict["type"] = "FAKE_TAG_EDGE"

                # add the tagable vertex
                vertex_resources = dict()
                vertices_resources[vertex.label] = vertex_resources
                vertex_resources["cores"] = \
                    DEFAULT_NOUMBER_OF_CORES_USED_PER_PARTITIONED_VERTEX
                vertex_resources["sdram"] = vertex.resources_required.sdram

                # add fake vertex
                vertex_resources = dict()
                vertices_resources[hashlib.md5(vertex.label).hexdigest()] = \
                    vertex_resources
                vertex_resources["cores"] = 0
                vertex_resources["sdram"] = 0

            # handel standard vertices
            else:
                vertex_resources = dict()
                vertices_resources[vertex.label] = vertex_resources
                vertex_resources["cores"] = \
                    DEFAULT_NOUMBER_OF_CORES_USED_PER_PARTITIONED_VERTEX
                vertex_resources["sdram"] = vertex.resources_required.sdram
            vertex_outgoing_partitions = \
                partitioned_graph.outgoing_edges_partitions_from_vertex(vertex)

            # handel the vertex edges
            for vertex_partition in vertex_outgoing_partitions:
                hyper_edge_dict = dict()
                edges_resources[
                    "{}:{}".format(vertex.label, vertex_partition)] = \
                    hyper_edge_dict
                hyper_edge_dict["source"] = vertex.label

                sinks_string = []
                for edge in vertex_outgoing_partitions[vertex_partition]:
                    sinks_string.append(edge.post_subvertex.label)
                hyper_edge_dict['sinks'] = sinks_string
                hyper_edge_dict["weight"] = 1.0
                hyper_edge_dict["type"] = vertex_partition.type.value

        file_path = os.path.join(folder_path, "graph.json")
        json.dump(json_graph_dictory_rep, file_path)

        # validate the schema
        partitioned_graph_schema_file_path = os.path.join(
            file_format_schemas.__file__, "partitioned_graph.json"
        )
        validictory.validate(
            json_graph_dictory_rep, partitioned_graph_schema_file_path)

        return {"FilePartitionedGraph": file_path}






