from pacman.model.graphs import AbstractVirtualVertex
from pacman.model.constraints.placer_constraints\
    import PlacerChipAndCoreConstraint, AbstractPlacerConstraint
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
            for constraint in vertex.constraints:
                self._handle_vertex_constraint(
                    constraint, json_obj, vertex, vertex_id)
                progress.update()
            self._handle_vertex_resources(
                vertex.resources_required, json_obj, vertex_id)
            if isinstance(vertex, AbstractVirtualVertex):
                self._handle_virtual_vertex(
                    vertex, vertex_id, json_obj, machine)
        return vertex_by_id

    def _handle_virtual_vertex(
            self, vertex, vertex_id, json_obj, machine):
        r_dict = dict()
        v_dict = dict()
        json_obj.append(r_dict)
        json_obj.append(v_dict)

        (real_chip_id, direction_id) = \
            self._locate_connected_chip_data(vertex, machine)
        r_dict['type'] = "route_endpoint"
        r_dict['vertex'] = vertex_id
        r_dict['direction'] = EDGES(direction_id)

        v_dict["type"] = "location"
        v_dict["vertex"] = vertex_id
        v_dict["location"] = real_chip_id

    @staticmethod
    def _locate_connected_chip_data(vertex, machine):
        """ Finds the connected virtual chip

        :param vertex:
        :param machine:
        """
        # locate the chip from the placement constraint
        placement_constraint = utility_calls.locate_constraints_of_type(
            vertex.constraints, PlacerChipAndCoreConstraint)
        router = machine.get_chip_at(
            placement_constraint.x, placement_constraint.y).router
        found_link = False
        link_id = 0
        while not found_link or link_id < 5:
            if router.is_link(link_id):
                found_link = True
            else:
                link_id += 1
        if not found_link:
            raise PacmanConfigurationException(
                "Can't find the real chip this virtual chip is connected to."
                "Please fix and try again.")
        else:
            return ("[{}, {}]".format(router.get_link(link_id).destination_x,
                                      router.get_link(link_id).destination_y),
                    router.get_link(link_id).multicast_default_from)

    @staticmethod
    def _handle_vertex_constraint(
            constraint, json_obj, vertex, vertex_id):
        if not isinstance(vertex, AbstractVirtualVertex):
            if isinstance(constraint, AbstractPlacerConstraint):
                if not isinstance(constraint, PlacerChipAndCoreConstraint):
                    raise PacmanConfigurationException(
                        "Converter does not recognise placer constraint {}"
                        .format(constraint))
                c_dict = dict()
                c_dict['type'] = "location"
                c_dict['vertex'] = vertex_id
                c_dict['location'] = [constraint.x, constraint.y]
                json_obj.append(c_dict)
                if constraint.p is not None:
                    c_dict = dict()
                    c_dict['type'] = "resource"
                    c_dict['vertex'] = vertex_id
                    c_dict['resource'] = "cores"
                    c_dict['range'] = "[{}, {}]".format(
                        constraint.p, constraint.p + 1)
                    json_obj.append(c_dict)

    @staticmethod
    def _handle_vertex_resources(
            resources_required, json_obj, vertex_id):
        for _ in resources_required.iptags:
            c_dict = dict()
            c_dict['type'] = "resource"
            c_dict['vertex'] = vertex_id
            c_dict['resource'] = "iptag"
            c_dict['range'] = [0, 1]
            json_obj.append(c_dict)
        for _ in resources_required.reverse_iptags:
            c_dict = dict()
            c_dict['type'] = "resource"
            c_dict['vertex'] = vertex_id
            c_dict['resource'] = "reverse_iptag"
            c_dict['range'] = [0, 1]
            json_obj.append(c_dict)

    @staticmethod
    def _add_extra_monitor_cores(json_obj, machine):
        for chip in machine.chips:
            for processor in chip.processors:
                if processor.processor_id != 0 and processor.is_monitor:
                    m_dict = dict()
                    m_dict['type'] = "reserve_resource"
                    m_dict['resource'] = "cores"
                    m_dict['reservation'] = \
                        [processor.processor_id, processor.processor_id + 1]
                    m_dict['location'] = [chip.x, chip.y]
                    json_obj.append(m_dict)

    @staticmethod
    def _add_monitor_core_reserve(json_obj):
        reserve_monitor = dict()
        reserve_monitor['type'] = "reserve_resource"
        reserve_monitor['resource'] = "cores"
        reserve_monitor['reservation'] = [0, 1]
        reserve_monitor['location'] = None
        json_obj.append(reserve_monitor)
