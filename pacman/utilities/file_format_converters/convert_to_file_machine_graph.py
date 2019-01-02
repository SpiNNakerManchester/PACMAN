import json
from collections import defaultdict
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs import AbstractVirtualVertex
from pacman.utilities.utility_calls import md5, ident
from pacman.utilities import file_format_schemas

DEFAULT_NUMBER_OF_CORES_USED_PER_VERTEX = 1


class ConvertToFileMachineGraph(object):
    """ Converts a memory based graph into a file based graph
    """

    __slots__ = []

    def __call__(self, machine_graph, plan_n_timesteps, file_path):
        """
        :param machine_graph: The graph to convert
        :param plan_n_timesteps: number of timesteps to plan for
        :type  plan_n_timesteps: int
        :param file_path: Where to write the JSON
        """
        progress = ProgressBar(
            machine_graph.n_vertices + 1, "Converting to JSON graph")

        # write basic stuff
        json_graph = dict()

        # write vertices data
        vertices_resources = dict()
        json_graph["vertices_resources"] = vertices_resources

        edges_resources = defaultdict()
        json_graph["edges"] = edges_resources

        vertex_by_id = dict()
        partition_by_id = dict()
        for vertex in progress.over(machine_graph.vertices, False):
            self._convert_vertex(
                vertex, vertex_by_id, vertices_resources, edges_resources,
                machine_graph, plan_n_timesteps, partition_by_id)

        with open(file_path, "w") as f:
            json.dump(json_graph, f)
        progress.update()

        file_format_schemas.validate(json_graph, "machine_graph.json")

        progress.end()

        return file_path, vertex_by_id, partition_by_id

    def _convert_vertex(self, vertex, vertex_by_id, vertices, edges,
                        machine_graph, plan_n_timesteps, partition_by_id):
        vertex_id = id(vertex)
        vertex_by_id[ident(vertex)] = vertex

        # handle external devices
        if isinstance(vertex, AbstractVirtualVertex):
            vertices[vertex_id] = {
                "cores": 0}
        elif vertex.resources_required.iptags or \
                vertex.resources_required.reverse_iptags:
            # handle tagged vertices:
            # handle the edge between the tag-able vertex and the fake vertex
            tag_id = md5(ident(vertex) + "_tag")
            edges[tag_id] = {
                "source": ident(vertex),
                "sinks": [tag_id],
                "weight": 1.0,
                "type": "FAKE_TAG_EDGE"}
            # add the tag-able vertex
            vertices[vertex_id] = {
                "cores": DEFAULT_NUMBER_OF_CORES_USED_PER_VERTEX,
                "sdram": int(vertex.resources_required.sdram.get_total_sdram(
                    plan_n_timesteps))}
            # add fake vertex
            vertices[tag_id] = {
                "cores": 0,
                "sdram": 0}
        else:
            # handle standard vertices
            vertices[vertex_id] = {
                "cores": DEFAULT_NUMBER_OF_CORES_USED_PER_VERTEX,
                "sdram": int(vertex.resources_required.sdram.get_total_sdram(
                    plan_n_timesteps))}

        # handle the vertex edges
        for partition in machine_graph\
                .get_outgoing_edge_partitions_starting_at_vertex(vertex):
            p_id = str(id(partition))
            partition_by_id[p_id] = partition
            edges[p_id] = {
                "source": ident(vertex),
                "sinks": [
                    ident(edge.post_vertex) for edge in partition.edges],
                "weight": sum(edge.traffic_weight for edge in partition.edges),
                "type": partition.traffic_type.name.lower()}
