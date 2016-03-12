from collections import defaultdict
import os
import json
import hashlib

import jsonschema

from pacman.model.abstract_classes.abstract_virtual_vertex import \
    AbstractVirtualVertex
from pacman.model.constraints.abstract_constraints.\
    abstract_tag_allocator_constraint import \
    AbstractTagAllocatorConstraint
from pacman.utilities import utility_calls
from spinn_machine.progress_bar import ProgressBar
from pacman.utilities import file_format_schemas

DEFAULT_NOUMBER_OF_CORES_USED_PER_PARTITIONED_VERTEX = 1


class ConvertToFilePartitionedGraph(object):
    """ Converts a memory based partitioned graph into a file based\
        partitioned graph
    """

    def __call__(self, partitioned_graph, file_path):
        """

        :param partitioned_graph:
        :param folder_path:
        :return:
        """
        progress_bar = ProgressBar(
            len(partitioned_graph.subvertices),
            "Converting to json partitioned graph")
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
                vertices_resources[id(vertex)] = vertex_resources
                vertex_resources["cores"] = 0

            # handle tagged vertices
            elif len(utility_calls.locate_constraints_of_type(
                    vertex.constraints, AbstractTagAllocatorConstraint)) != 0:

                # handle the edge between the tag-able vertex and the fake
                # vertex
                hyper_edge_dict = dict()
                edges_resources[hashlib.md5(vertex.label).hexdigest()] = \
                    hyper_edge_dict
                hyper_edge_dict["source"] = str(id(vertex))
                hyper_edge_dict['sinks'] = \
                    [hashlib.md5(vertex.label).hexdigest()]
                hyper_edge_dict["weight"] = 1.0
                hyper_edge_dict["type"] = "FAKE_TAG_EDGE"

                # add the tag-able vertex
                vertex_resources = dict()
                vertices_resources[id(vertex)] = vertex_resources
                vertex_resources["cores"] = \
                    DEFAULT_NOUMBER_OF_CORES_USED_PER_PARTITIONED_VERTEX
                vertex_resources["sdram"] = \
                    int(vertex.resources_required.sdram.get_value())

                # add fake vertex
                vertex_resources = dict()
                vertices_resources[
                    hashlib.md5(vertex.label).hexdigest()] = vertex_resources
                vertex_resources["cores"] = 0
                vertex_resources["sdram"] = 0

            # handle standard vertices
            else:
                vertex_resources = dict()
                vertices_resources[id(vertex)] = vertex_resources
                vertex_resources["cores"] = \
                    DEFAULT_NOUMBER_OF_CORES_USED_PER_PARTITIONED_VERTEX
                vertex_resources["sdram"] = \
                    int(vertex.resources_required.sdram.get_value())

            vertex_outgoing_partitions = \
                partitioned_graph.outgoing_edges_partitions_from_vertex(vertex)

            # handle the vertex edges
            for partition_id in vertex_outgoing_partitions:
                partition = vertex_outgoing_partitions[partition_id]
                hyper_edge_dict = dict()
                edges_resources[str(id(partition))] = hyper_edge_dict
                hyper_edge_dict["source"] = str(id(vertex))

                sinks_string = []
                weight = 0

                for edge in partition.edges:
                    sinks_string.append(str(id(edge.post_subvertex)))
                    weight += edge.weight
                hyper_edge_dict['sinks'] = sinks_string
                hyper_edge_dict["weight"] = weight
                hyper_edge_dict["type"] = partition.type.name.lower()
            progress_bar.update()

        file_to_write = open(file_path, "w")
        json.dump(json_graph_dictory_rep, file_to_write)
        file_to_write.close()

        # validate the schema
        partitioned_graph_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__),
            "partitioned_graph.json"
        )
        file_to_read = open(partitioned_graph_schema_file_path, "r")
        partitioned_graph_schema = json.load(file_to_read)
        jsonschema.validate(
            json_graph_dictory_rep, partitioned_graph_schema)

        progress_bar.end()

        return {"partitioned_graph": file_path}
