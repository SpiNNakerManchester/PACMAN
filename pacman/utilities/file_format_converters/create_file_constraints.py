from pacman.model.graphs import AbstractVirtualVertex
from pacman.model.constraints.placer_constraints\
    import ChipAndCoreConstraint, AbstractPlacerConstraint
from pacman.exceptions import PacmanConfigurationException
from pacman.utilities import utility_calls, file_format_schemas
from pacman.utilities.constants import EDGES

from spinn_utilities.progress_bar import ProgressBar

import json
import os
import jsonschema


class CreateConstraintsToFile(object):
    """ Creates constraints file from the machine and machine graph
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, file_path):
        """
        :param machine_graph: the machine graph
        :param machine: the machine
        """

        progress = ProgressBar(
            machine_graph.n_vertices + 2, "creating json constraints")

        json_obj = list()
        self._add_monitor_core_reserve(json_obj)
        progress.update()
        self._add_extra_monitor_cores(json_obj, machine)
        progress.update()
        vertex_by_id = self._search_graph_for_placement_constraints(
            json_obj, machine_graph, machine, progress)

        with open(file_path, "w") as file_to_write:
            json.dump(json_obj, file_to_write)

        # validate the schema
        constraints_schema_file_path = os.path.join(
            os.path.dirname(file_format_schemas.__file__), "constraints.json")

        # for debug purposes, read schema and validate
        with open(constraints_schema_file_path, "r") as file_to_read:
            jsonschema.validate(json_obj, json.load(file_to_read))

        # complete progress bar
        progress.end()

        return file_path, vertex_by_id

    def _search_graph_for_placement_constraints(
            self, json_obj, machine_graph, machine, progress):
        vertex_by_id = dict()
        for vertex in machine_graph.vertices:
            vertex_id = str(id(vertex))
            vertex_by_id[vertex_id] = vertex
            for constraint in progress.over(vertex.constraints, False):
                self._handle_vertex_constraint(
                    constraint, json_obj, vertex, vertex_id)
            self._handle_vertex_resources(
                vertex.resources_required, json_obj, vertex_id)
            if isinstance(vertex, AbstractVirtualVertex):
                self._handle_virtual_vertex(
                    vertex, vertex_id, json_obj, machine)
        return vertex_by_id

    def _handle_virtual_vertex(self, vertex, vertex_id, json_obj, machine):
        chip_id, direction_id = \
            self._locate_connected_chip_data(vertex, machine)
        json_obj.append({
            "type": "route_endpoint",
            "vertex": vertex_id,
            "direction": EDGES(direction_id)})
        json_obj.append({
            "type": "location",
            "vertex": vertex_id,
            "location": chip_id})

    @staticmethod
    def _locate_connected_chip_data(vertex, machine):
        """ Finds the connected virtual chip

        :param vertex:
        :param machine:
        """
        # locate the chip from the placement constraint
        placement_constraint = utility_calls.locate_constraints_of_type(
            vertex.constraints, ChipAndCoreConstraint)
        router = machine.get_chip_at(
            placement_constraint.x, placement_constraint.y).router
        link = next(
            (router.get_link(i) for i in range(6) if router.is_link(i)),
            None)
        if link is None:
            raise PacmanConfigurationException(
                "Can't find the real chip this virtual chip is connected to."
                "Please fix and try again.")
        return (str([link.destination_x, link.destination_y]),
                link.multicast_default_from)

    @staticmethod
    def _handle_vertex_constraint(constraint, json_obj, vertex, vertex_id):
        if not isinstance(vertex, AbstractVirtualVertex):
            if isinstance(constraint, AbstractPlacerConstraint):
                if not isinstance(constraint, ChipAndCoreConstraint):
                    raise PacmanConfigurationException(
                        "Converter does not recognise placer constraint {}"
                        .format(constraint))
                json_obj.append({
                    "type": "location",
                    "vertex": vertex_id,
                    "location": [constraint.x, constraint.y]})
                if constraint.p is not None:
                    json_obj.append({
                        "type": "resource",
                        "vertex": vertex_id,
                        "resource": "cores",
                        "range": str([constraint.p, constraint.p + 1])})

    @staticmethod
    def _handle_vertex_resources(resources_required, json_obj, vertex_id):
        for _ in resources_required.iptags:
            json_obj.append({
                "type": "resource",
                "vertex": vertex_id,
                "resource": "iptag",
                "range": [0, 1]})
        for _ in resources_required.reverse_iptags:
            json_obj.append({
                "type": "resource",
                "vertex": vertex_id,
                "resource": "reverse_iptag",
                "range": [0, 1]})

    @staticmethod
    def _add_extra_monitor_cores(json_obj, machine):
        for chip in machine.chips:
            for p in chip.processors:
                if p.processor_id and p.is_monitor:
                    json_obj.append({
                        "type": "reserve_resource",
                        "resource": "cores",
                        "reservation": [p.processor_id, p.processor_id + 1],
                        "location": [chip.x, chip.y]})

    @staticmethod
    def _add_monitor_core_reserve(json_obj):
        json_obj.append({
            'type': "reserve_resource",
            'resource': "cores",
            'reservation': [0, 1],
            'location': None})
