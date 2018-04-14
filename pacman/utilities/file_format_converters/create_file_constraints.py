from pacman.model.graphs import AbstractVirtualVertex
from pacman.model.constraints.placer_constraints\
    import ChipAndCoreConstraint, AbstractPlacerConstraint
from pacman.exceptions import PacmanConfigurationException
from pacman.utilities import utility_calls, file_format_schemas
from pacman.utilities.constants import EDGES
from pacman.utilities.utility_calls import ident
from spinn_utilities.progress_bar import ProgressBar

import json


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
            machine_graph.n_vertices + 2, "creating JSON constraints")

        json_obj = list()
        self._add_monitor_core_reserve(json_obj)
        progress.update()
        self._add_extra_monitor_cores(json_obj, machine)
        progress.update()
        vertex_by_id = self._search_graph_for_placement_constraints(
            json_obj, machine_graph, machine, progress)

        with open(file_path, "w") as f:
            json.dump(json_obj, f)

        # validate the schema
        file_format_schemas.validate(json_obj, "constraints.json")

        # complete progress bar
        progress.end()

        return file_path, vertex_by_id

    def _search_graph_for_placement_constraints(
            self, json_obj, machine_graph, machine, progress):
        vertex_by_id = dict()
        for vertex in progress.over(machine_graph.vertices, False):
            vertex_id = ident(vertex)
            vertex_by_id[vertex_id] = vertex
            for constraint in vertex.constraints:
                self._handle_vertex_constraint(
                    constraint, json_obj, vertex, vertex_id)
            self._handle_vertex_resources(
                vertex.resources_required, json_obj, vertex_id)
            if isinstance(vertex, AbstractVirtualVertex):
                self._handle_virtual_vertex(
                    vertex, vertex_id, json_obj, machine)
        return vertex_by_id

    def _handle_virtual_vertex(self, vertex, vertex_id, json_obj, machine):
        chip_id, direction = self._locate_connected_chip_data(vertex, machine)
        json_obj.append({
            "type": "route_endpoint",
            "vertex": vertex_id,
            "direction": EDGES(direction).name.lower()})
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
        placement_constraints = utility_calls.locate_constraints_of_type(
            vertex.constraints, ChipAndCoreConstraint)
        routers = (
            machine.get_chip_at(constraint.x, constraint.y).router
            for constraint in placement_constraints)
        links = (
            router.get_link(i)
            for router in routers for i in range(6) if router.is_link(i))
        link = next(iter(links), None)
        if link is None:
            raise PacmanConfigurationException(
                "Can't find the real chip this virtual chip is connected to."
                "Please fix and try again.")
        return ([link.destination_x, link.destination_y],
                link.multicast_default_from)

    @staticmethod
    def _handle_vertex_constraint(constraint, json_obj, vertex, vertex_id):
        if isinstance(vertex, AbstractVirtualVertex):
            return
        if isinstance(constraint, AbstractPlacerConstraint):
            if not isinstance(constraint, ChipAndCoreConstraint):
                raise PacmanConfigurationException(  # pragma: no cover
                    "Converter does not recognise placer constraint {}".format(
                        constraint))
            json_obj.append({
                "type": "location",
                "vertex": vertex_id,
                "location": [constraint.x, constraint.y]})
            if constraint.p is not None:
                json_obj.append({
                    "type": "resource",
                    "vertex": vertex_id,
                    "resource": "cores",
                    "range": [constraint.p, constraint.p + 1]})

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
